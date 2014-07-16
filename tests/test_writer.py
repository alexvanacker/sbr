#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from scrapper import writer
import os
import csv


class WriterTest(unittest.TestCase):

    def setUp(self):
        self.csv_file = 'test.csv'

    def tearDown(self):
        if os.path.exists(self.csv_file):
            os.remove(self.csv_file)

    def test_unicode_write(self):
        dest_file = open(self.csv_file, 'wb')
        csv_writer = csv.DictWriter(dest_file, fieldnames=['test'])
        dicts = [{'test': '02 21  16 00 60'}]
        writer.write_unicode_csv_rows(dicts, csv_writer)

    def test_write_reviews(self):
        list_url = ['http://www.beeradvocate.com/beer/profile/26/42349/']
        writer.write_all_beers_reviews(list_url, self.csv_file)

    def test_write_beer_info(self):
        list_url = ['http://www.beeradvocate.com/beer/profile/694/15881/',
                    'http://www.beeradvocate.com/beer/profile/26/42349/']
        writer.write_all_beer_infos(list_url, self.csv_file)

        # test info
        csv_reader = csv.DictReader(open(self.csv_file, 'rb'))
        for line in csv_reader:
            if (line['beer_url'] ==
                    'http://www.beeradvocate.com/beer/profile/694/15881/'):
                self.assertEquals(line['abv'], '7.50')

    def test_write_brewery_info(self):
        list_url = ['http://www.beeradvocate.com/beer/profile/24252/',
                    'http://www.beeradvocate.com/beer/profile/3079/',
                    'http://www.beeradvocate.com/beer/profile/887/',
                    'http://www.beeradvocate.com/beer/profile/4067',
                    'http://www.beeradvocate.com/beer/profile/1536/']
        writer.write_all_brewery_infos(list_url, self.csv_file)

        # Test info
        csv_reader = csv.DictReader(open(self.csv_file, 'rb'))
        for line in csv_reader:
            url = line['url']
            if (url ==
                    'http://www.beeradvocate.com/beer/profile/1536/'):
                self.assertEqual(line['country'], 'Germany',
                                 'Expecting country Germany for ' + url)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
