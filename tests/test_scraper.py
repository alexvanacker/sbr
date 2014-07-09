
import unittest
from scrapper import scrapper


class ScraperTest(unittest.TestCase):

    def test_extract_reviews_from_urls(self):
        list_url = ['http://www.beeradvocate.com/beer/profile/694/15881/']
        for url in list_url:
            scrapper.extract_reviews_from_url(url)

    def test_get_beer_infos(self):
        list_url = ['http://www.beeradvocate.com/beer/profile/694/15881/',
                    'http://www.beeradvocate.com/beer/profile/26/42349/']

        for url in list_url:
            scrapper.get_beer_infos(url)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
