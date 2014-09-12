#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import time
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
            'Saturday', 'Sunday']
# HH:MM AM/PM
time_format = '%I:%M %p'

def extract_date(string, current_date=None):
    """ Converts a string to a date, according to current_date.

    The string is of the form: 'Today', '54 min ago',
    'Mon' or 'Aug 31, 2014'

    string -- representation of the date
    current_date -- Time from which the string is converted
    """
    logger.debug('Extracting date from: %s', string)

    if current_date is None:
        current_date = datetime.datetime.now()

    if 'Today' in string:
        # Today at 11:52 PM
        time_string = string.split('at')[1].strip()

        time_from_string = datetime.datetime.strptime(time_string, time_format)

        # Make the date
        string_date = time_from_string.replace(day=current_date.day,
                                               month=current_date.month,
                                               year=current_date.year,
                                               second=0,
                                               microsecond=0)
        return string_date
        
    elif 'ago' in string:
        # 54 minutes ago
        min_ago_str = string.split('minute')[0].strip()
        try:
            min_ago = int(min_ago_str)
            string_date = current_date - datetime.timedelta(minutes=min_ago)
            string_date = string_date.replace(second=0, microsecond=0)
            return string_date


        except Exception, e:
            logger.error('Could not extract time from %s', string)
            raise
        
    elif 'at' in string:

        # Saturday at 02:03 PM
        # Yesterday at 09:45 PM
        split = string.split(' at ')
        day_name = split[0].strip()
        time_string = split[1].strip()
        time = datetime.datetime.strptime(time_string, time_format)

        # Compute the difference
        today_day = current_date.weekday()
        if day_name in weekdays:
            date_day = weekdays.index(day_name)
            day_diff = today_day - date_day
        else:
            # It's yesterday, day_diff = 1
            day_diff = 1

        if day_diff < 0:
            day_diff = 7 + day_diff

        delta = datetime.timedelta(days=day_diff)
        final_date = current_date - delta
        final_date = final_date.replace(hour=time.hour, minute=time.minute, second=0, microsecond=0)
        return final_date

    else:
        # Aug 31, 2014
        string_format = '%b %d, %Y'
        date_from_string = datetime.datetime.strptime(string, string_format)
        return date_from_string



