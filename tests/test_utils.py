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


    def test_time_ago(self):
        s = '51 minutes ago'


