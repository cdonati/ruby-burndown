$(document).ready(function() {
    function prettyDate(date) {
        return date.getFullYear() + '-' + date.getMonth() + '-' +
          date.getDate();
    }

    $.get('/chart', function(points) {
        var markup = '<ul>';
        $.each(points, function(index, point) {
            var date = new Date(point.date);
            var lines = point.lines;
            markup += '<li>' + prettyDate(date) + ': ' + lines + '</li>';
        });
        markup += '</ul>';
        $('#chart').html(markup);
    }, 'json');
});
