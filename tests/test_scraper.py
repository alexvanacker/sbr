
import unittest
from scrapper import scrapper


class ScraperTest(unittest.TestCase):

    def test_extract_reviews_from_urls(self):
        list_url = ['http://www.beeradvocate.com/beer/profile/694/15881/',
                    'http://www.beeradvocate.com/beer/profile/26/42349/']
        for url in list_url:
            reviews = scrapper.extract_reviews_from_url(url)
            if '/26/42349/' in url:
                # Check for review, only way is to hardcode this
                for r in reviews:
                    if 'wpqx.748148' in r['user_url']:
                        if not r['review'] or r['review'] == '':
                            raise Exception('Missing reviews')

    def test_get_beer_infos(self):
        list_url = ['http://www.beeradvocate.com/beer/profile/694/15881/',
                    'http://www.beeradvocate.com/beer/profile/26/42349/']

        for url in list_url:
            scrapper.get_beer_infos(url)

    def test_get_brewery_infos(self):
        list_url = ['http://www.beeradvocate.com/beer/profile/24252/',
                    'http://www.beeradvocate.com/beer/profile/3079/',
                    'http://www.beeradvocate.com/beer/profile/887/',
                    'http://www.beeradvocate.com/beer/profile/4067',
                    'http://www.beeradvocate.com/beer/profile/1536/']

        for url in list_url:
            scrapper.get_brewery_infos(url)

    def test_get_user_infos(self):
        list_url = [
            'http://www.beeradvocate.com/community/members/le_scratch.813128/',
            'http://www.beeradvocate.com/community/members/zekeman17.427655/'
        ]

        for url in list_url:
            scrapper.get_user_infos(url)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
