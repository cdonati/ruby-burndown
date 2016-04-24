#!/usr/bin/env python3
import datetime
import git
import json

from flask import Flask, render_template

REMOTE_REPO = 'https://github.com/AppScale/appscale.git'
LOCAL_REPO = 'appscale.git'
RUBY_DIR = 'AppController'
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


def to_json(commits):
    for commit in commits:
        commit['date'] = commit['date'].isoformat()
        del commit['id']
    commits.reverse()
    return json.dumps(commits)


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
        repo = git.Repo(LOCAL_REPO)
    except git.exc.NoSuchPathError:
        return '[]'
    start_date = datetime.datetime.now() - datetime.timedelta(weeks=52)
    commits = fetch_commits(repo.head.commit, start_date)
    return to_json(commits)


@app.route('/refresh')
def refresh():
    try:
        repo = git.Repo(LOCAL_REPO)
    except git.exc.NoSuchPathError:
        git.Repo.clone_from(REMOTE_REPO, LOCAL_REPO)
        return 'Cloned repo.'
    repo.remotes.origin.pull()
    return 'Updated repo.'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
