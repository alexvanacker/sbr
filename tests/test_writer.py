
import unittest
from scrapper import writer
import os


class WriterTest(unittest.TestCase):

    def test_write_reviews(self):
        list_url = ['http://www.beeradvocate.com/beer/profile/26/42349/']
        csv_file = 'test.csv'
        writer.write_all_beers_reviews(list_url, csv_file)
        # Cleanup
        os.remove(csv_file)

    def test_write_beer_info(self):
        list_url = ['http://www.beeradvocate.com/beer/profile/694/15881/',
                    'http://www.beeradvocate.com/beer/profile/26/42349/']
        csv_file = 'test.csv'
        writer.write_all_beer_infos(list_url, csv_file)

    def test_write_brewery_info(self):
        list_url = ['http://www.beeradvocate.com/beer/profile/24252/',
                    'http://www.beeradvocate.com/beer/profile/3079/',
                    'http://www.beeradvocate.com/beer/profile/887/',
                    'http://www.beeradvocate.com/beer/profile/4067',
                    'http://www.beeradvocate.com/beer/profile/1536/']
        csv_file = 'test.csv'
        writer.write_all_brewery_infos(list_url, csv_file)

def main():
    unittest.main()

if __name__ == '__main__':
    main()
