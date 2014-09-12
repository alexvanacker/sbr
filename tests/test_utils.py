#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import datetime
from scrapper import utils

class UtilsTest(unittest.TestCase):

    def test_today(self):
        s = 'Today at 11:52 PM'
        now = datetime.datetime.now()
        expected = now.replace(hour=23, minute=52, second=0, microsecond=0)
        date = utils.extract_date(s)
        assert date == expected


    def test_yesterday(self):
        s = 'Yesterday at 12:34 PM'
        now = datetime.datetime.now()
        expected = now - datetime.timedelta(days=1)
        expected = expected.replace(hour=12, minute=34, microsecond=0, second=0)
        date = utils.extract_date(s)
        assert date == expected


    def test_time_ago(self):
        diff = 51
        s = str(diff)+' minutes ago'
        now = datetime.datetime.now()
        expected = now - datetime.timedelta(minutes=diff)
        expected = expected.replace(second=0, microsecond=0)
        result = utils.extract_date(s)
        assert expected == result

    def test_minute_ago(self):
        s = '1 minute ago'
        now = datetime.datetime.now()
        expected = now - datetime.timedelta(minutes=1)
        expected = expected.replace(second=0, microsecond=0)
        result = utils.extract_date(s)
        assert expected == result

    def test_date(self):
        s = 'Mar 16, 1987'
        expected = datetime.datetime.now().replace(month=3, year=1987, day=16, hour=0, minute=0, second=0, microsecond=0)
        result = utils.extract_date(s)
        assert expected == result


