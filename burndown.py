#!/usr/bin/env python3
import datetime
import dateutil.parser
import git
import json
import logging
import os

from flask import Flask, render_template, send_file
from pymemcache.client.base import Client

REMOTE_REPO = 'https://github.com/AppScale/appscale.git'
LOCAL_REPO = 'appscale.git'
RUBY_DIR = 'AppController'
MEMCACHE_ADDR = os.environ.get('MEMCACHE_PORT_11211_TCP_ADDR', 'localhost')
MEMCACHE_PORT = int(os.environ.get('MEMCACHE_PORT_11211_TCP_PORT', 11211))
MEMCACHE_KEY = 'chart_data'

memcache_client = Client((MEMCACHE_ADDR, MEMCACHE_PORT))
app = Flask(__name__)


def ruby_loc(commit):
    total_loc = 0
    for blob in commit.tree[RUBY_DIR].traverse():
        if blob.path.endswith('.rb'):
            total_loc += sum(1 for _ in blob.data_stream.read())
    return total_loc


def commit_affected_ruby(commit):
    diff = commit.diff(commit.parents[0])
    for change in diff:
        if change.a_path.endswith('.rb'):
            return True
    return False


def json_safe(commits):
    for commit in commits:
        commit['date'] = commit['date'].isoformat()
        del commit['id']
    commits.reverse()
    return commits


def fetch_commits(start_commit, start_date):
    commits = []
    commit = start_commit
    first_commit = True
    while True:
        if not first_commit:
            commit = commit.parents[0]
        first_commit = False

        commit_date = commit.committed_datetime.replace(tzinfo=None)
        if commit_date < start_date:
            break

        if commits:
            last_commit_date = commits[-1]['date']
            if (commit_date.year == last_commit_date.year and
                    commit_date.month == last_commit_date.month and
                    commit_date.day == last_commit_date.day):
                continue

        if not commit_affected_ruby(commit):
            continue

        commits.append({'date': commit_date, 'lines': ruby_loc(commit),
                        'id': commit.hexsha})
    return commits


@app.route('/')
def main():
    return render_template('index.html')


@app.route('/chart')
def chart():
    try:
        cache = memcache_client.get(MEMCACHE_KEY)
        if cache is None:
            return refresh()
        chart_data = json.loads(cache.decode('utf-8'))['data']
    except ConnectionRefusedError:
        logging.warning('Unable to access memcached.')
        repo = git.Repo(LOCAL_REPO)
        start_date = datetime.datetime.now() - datetime.timedelta(weeks=52)
        chart_data = json_safe(fetch_commits(repo.head.commit, start_date))
    return json.dumps(chart_data)


@app.route('/refresh')
def refresh():
    chart_data_json = memcache_client.get(MEMCACHE_KEY)
    if chart_data_json is not None:
        chart_data = json.loads(chart_data_json.decode('utf-8'))
        updated = dateutil.parser.parse(chart_data['updated'])
        if updated > (datetime.datetime.now() - datetime.timedelta(hours=1)):
            return json.dumps(chart_data['data'])
    try:
        repo = git.Repo(LOCAL_REPO)
        repo.remotes.origin.pull()
    except git.exc.NoSuchPathError:
        git.Repo.clone_from(REMOTE_REPO, LOCAL_REPO)
        repo = git.Repo(LOCAL_REPO)
    start_date = datetime.datetime.now() - datetime.timedelta(weeks=52)
    commits = fetch_commits(repo.head.commit, start_date)
    cache = {'updated': datetime.datetime.now().isoformat(),
             'data': json_safe(commits)}
    memcache_client.set(MEMCACHE_KEY, json.dumps(cache))
    return cache['data']


@app.route('/favicon.ico')
def favicon():
    return send_file('static/favicon.ico')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
