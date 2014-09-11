#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import time
import logging


logger = logging.getLogger(__name__)

weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
            'Saturday', 'Sunday']

def extract_date(string, current_date=None):
    """ Converts a string to a date, according to current_date.

    The string is of the form: 'Today', '54 min ago',
    'Mon' or 'Aug 31, 2014'

    string -- representation of the date
    current_date -- Time from which the string is converted
    """
    if current_date is None:
        current_date = datetime.datetime.now()

    if 'Today' in string:
        # Today at 11:52 PM
        time_string = string.split('at')[1].strip()
        # HH:MM AM
        fs = '%I:%M %p'
        time_from_string = datetime.datetime.strptime(time_string, fs)

        # Make the date
        string_date = time_from_string.replace(day=current_date.day,
                                               month=current_date.month,
                                               year=current_date.year,
                                               seconds=0,
                                               microseconds=0)
        return string_date
        
    elif 'ago' in string:
        # 54 min ago
        pass
    elif 'at' in string:
        # Saturday at 02:03 PM
        pass
    else:
        # Aug 31, 2014
        pass



