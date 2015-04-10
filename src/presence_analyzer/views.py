# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
from flask import redirect, abort, render_template

from presence_analyzer.main import app
from presence_analyzer.utils import jsonify, \
    get_data, mean, group_by_weekday, get_mean_by_weekday

import logging
log = logging.getLogger(__name__)  # pylint: disable=invalid-name


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect('presence_weekday/')


@app.route('/presence_weekday/')
def presence_weekday():
    """
    Renders presence by weekday page.
    """
    return render_template('presence_weekday.html')


@app.route('/presence_start_end/')
def presence_start_end():
    """
    Renders presence start-end page.
    """
    return render_template('presence_start_end.html')


@app.route('/mean_time_weekday/')
def mean_time_weekday():
    """
    Renders mean-time weekday page.
    """
    return render_template('mean_time_weekday.html')


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    return [
        {'user_id': i, 'name': 'User {0}'.format(str(i))}
        for i in data.keys()
    ]


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], mean(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    return result


@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end_view(user_id):
    """
    Returns timespans (in miliseconds since midnight)
    when the employee is most often present in the office.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    # we multiply by 1000 because js expects miliseconds for Date()
    start = [
        x*1000.0 for x in get_mean_by_weekday(data[user_id], 'start')
    ]
    end = [
        x*1000.0 for x in get_mean_by_weekday(data[user_id], 'end')
    ]

    return [{'start': start[i], 'end': end[i]} for i in range(5)]


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], sum(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result
