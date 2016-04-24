function prettyDate(date) {
    return date.getFullYear() + '-' + date.getMonth() + '-' +
        date.getDate();
}

function make_x_axis(xRange) {
    return d3.svg.axis().scale(xRange).orient('bottom')
        .tickSubdivide(true);
}

function make_y_axis(yRange) {
    return d3.svg.axis().scale(yRange).orient('left').tickSubdivide(true);
}

function drawChart(data) {
    var svg = d3.select('#chart svg'),
    width = 1000,
    height = 500,
    margin = {
        top: 0,
        right: 0,
        bottom: 140,
        left: 120
    },
    xMin = d3.min(data, function (d) { return d.x; }),
    xMax = d3.max(data, function (d) { return d.x; }),

    yMax = d3.max(data, function (d) { return d.y; }),
    yMin = d3.min(data, function (d) {
        var spread = yMax - d.y;
        var min = yMax - parseInt(spread * 1.5);
        return Math.max(min, 0);
    }),

    xRange = d3.time.scale()
        .domain([data[data.length - 1].x, data[0].x])
        .range([width - margin.right, margin.left]),
    yRange = d3.scale.linear()
        .domain([yMin, yMax])
        .range([height - margin.bottom, margin.top]),

    xAxis = d3.svg.axis().scale(xRange).tickFormat(d3.time.format('%Y-%m-%d')),
    yAxis = d3.svg.axis().scale(yRange).orient('left').tickSubdivide(true);

    svg.append('g').attr('class', 'grid')
        .attr('transform', 'translate(0, ' + (height - margin.bottom) + ')')
        .call(make_x_axis(xRange)
            .tickSize((-height) + (margin.top + margin.bottom), 0, 0)
            .tickFormat('')
        );

    svg.append('g').attr('class', 'grid')
        .attr('transform', 'translate(' + (margin.left) + ',0)')
        .call(make_y_axis(yRange)
            .tickSize((-width) + (margin.right + margin.left), 0, 0)
            .tickFormat('')
        );

    svg.append('svg:g').attr('class', 'x axis')
        .attr('transform', 'translate(0, ' + (height - (margin.bottom)) + ')')
        .call(xAxis)
        .selectAll('text')
        .style('text-anchor', 'end')
        .attr('transform', 'rotate(-65)')
        .attr('dx', '-.8em').attr('dy', '.15em');

    svg.append('svg:g').attr('class', 'y axis')
        .attr('transform', 'translate(' + margin.left + ',0)')
        .call(yAxis);

    var lineFunc = d3.svg.line()
        .x(function (d) { return xRange(d.x); })
        .y(function (d) { return yRange(d.y); })
        .interpolate('basis');

    var areaFunc = d3.svg.area()
        .x(function(d) { return xRange(d.x); })
        .y0(height - margin.bottom).y1(function(d) { return yRange(d.y); })
        .interpolate('basis');

    svg.append('path').attr('class', 'loc').attr('d', lineFunc(data));

    svg.append('path').attr('class', 'area').attr('d', areaFunc(data));

    svg.append('text').attr('class', 'x label')
        .attr('text-anchor', 'middle')
        .attr('x', (width - margin.bottom) / 2).attr('y', height -6)
        .attr('transform', 'translate(' + margin.left + ',0)')
        .text('Date');

    svg.append('text').attr('class', 'y label')
        .attr('text-anchor', 'middle')
        .attr('y', 16).attr('x', -1 * (height - margin.left) / 2)
        .attr('transform', 'rotate(-90)')
        .text('Lines of Ruby Code');

    svg.append('rect').attr('class', 'border')
        .attr('x', margin.left).attr('y', 0)
        .attr('height', height - margin.bottom)
        .attr('width', width - margin.left);
}

$(document).ready(function() {
    $.get('/chart', function(points) {
        var chartData = [];
        $.each(points, function(index, point) {
            var date = new Date(point.date);
            var lines = point.lines;
            chartData.push({'x': date, 'y': lines});
        });
        drawChart(chartData);
    }, 'json');
});
