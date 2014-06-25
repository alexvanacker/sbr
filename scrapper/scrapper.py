#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import time
import sys
import re
import logging
import logging.config
import os
import json
import random
import pickle
from bs4 import BeautifulSoup
from bs4 import FeatureNotFound


logger = logging.getLogger(__name__)

# Define which parser to use
parser_1 = "lxml"
parser_2 = "html5lib"
parser = parser_1
try:
    test_soup = BeautifulSoup('<html></html>', parser)
except FeatureNotFound:
    # print because logger may not be defined at this stage
    print parser + ' not found, switching to '+parser_2
    parser = parser_2
    test_soup = BeautifulSoup('<html></html>', parser)


def setup_logging(
    default_path='logging.json',
    default_level=logging.INFO,
    env_key='LOG_CFG'
):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        f = open(path, 'rt')
        config = json.load(f)
        logging.config.dictConfig(config=config)
    else:
        logging.basicConfig(level=default_level)


def get_styles_url_and_names():
    """Get beer style URL

    Returns a dict linking an url to a beer style and its global type
    """

    root_page = 'http://www.beeradvocate.com'
    current_page = 'http://www.beeradvocate.com/beer/style/'
    soup = make_soup(current_page)
    body = soup.body
    table = body.table
    first_tr = table.tr
    global_list = {}
    for td in first_tr.find_all('td', recursive=False):
        for td_table in td.find_all('table', recursive=False):
            tr_in_table = td_table.find_all('tr', limit=2)
            # Contains all names and links to beer styles
            style_list_html = tr_in_table[1].td
            for style_name_html in style_list_html.find_all('b'):
                style_name = style_name_html.contents[0]
                # Go down in the tr tree, until you have a double
                # break line. Such ugly.
                double_br = False
                previous_was_br = False
                previous_element = style_name_html
                while not double_br:
                    next_element = previous_element.find_next()
                    is_br = next_element.name.find('br') > -1
                    double_br = is_br and previous_was_br

                    # Now, if it's a link, add it to the dict
                    if next_element.name == 'a':
                        link = next_element['href']
                        full_link = root_page + link
                        beer_style_name = next_element.contents[0]
                        global_list[full_link] = (beer_style_name, style_name)

                    previous_was_br = is_br
                    previous_element = next_element

    return global_list


def make_soup(url):
    """Get soup object from url

    Currently based on lxml parser for speed.
    """
    r = requests.get(url)
    if r.status_code != requests.codes.ok:
        print 'Error: status code is ' + str(r.status_code) + ' for URL: ' + url
        sys.exit(1)
    contents = r.content

    soup = BeautifulSoup(contents, parser)
    return soup


def find_max(url):
    soup = make_soup(url)
    st = soup.body.findAll(id='baContent')[0].table.td.span.b.contents[0]
    m = re.search('\(out of (.+?)\)', st)
    if m:
        found = m.group(1)
    else:
        logger.error('Could not extract max number of subpages: '+url)
        raise Exception
    return found


def get_substyle_url(url):
    """From a style get all the pages of the style

    """
    substyle_urls = []
    start = 0
    mymax = int(find_max(url))
    while start < mymax:
        substyle_urls.append(url + '?start=' + str(start))
        start = start + 50
    return substyle_urls


def get_all_beers_from_substyle(substyle_url):
    """Return all the beers from a substyle URL.

    List is made by jumping from page to page
    """
    root_url = 'http://www.beeradvocate.com/'
    url_list = []
    # Get list of all pages for the substyle which contains all beers!
    substyle_urls = get_substyle_url(substyle_url)

    for page_url in substyle_urls:
        soup = make_soup(page_url)
        links = soup.find_all(href=re.compile('beer/profile/(.+)/(.+)/$'))
        for link in links:
            beer_profile_url = link['href']
            full_beer_url = root_url + beer_profile_url
            url_list.append(full_beer_url)

    return url_list


def get_beer_name(profile_page_soup):
    title_bar = profile_page_soup.find(class_='titleBar')
    h1 = title_bar.h1
    return h1.contents[0]


def get_beer_stats(profile_page_soup):

    infos_dict = {}

    main_div = profile_page_soup.find(id='baContent')
    stats_tr = main_div.table.tr.find_all('td')[1].find('tr')
    real_stats_tr = stats_tr.find('tr')
    stats_td_list = real_stats_tr.find_all('td', recursive=False)

    if len(stats_td_list) < 3:
        logger.error('Error on profile page, not enough columns')
        raise
    # first td is BA score
    ba_score_td = stats_td_list[0]

    # second is Bros score -> useless
    bros_score_td = stats_td_list[1]

    # Third is summary with number of ratings, number of reviews, etc
    # Structure from 2014_06_18:
    # <td width="33%" align="left" valign="top" style="padding-left:10px;">
    #    Ratings: 430<br>Reviews: 238<br>rAvg: 4.04<!--<br>psDev: 10.6%-->
    #    <br>pDev: 13.12%
    #    <br><a href="/beer/trade/61128/?view=W">Wants: 14</a>
    #    <br><a href="/beer/trade/61128/?view=G">Gots: 37</a> | <a href="/beer/trade/61128/?view=FT">FT: 1</a>
    #    </td>
    summary_td = stats_td_list[2]
    td_text = summary_td.get_text()
    match_nb_ratings = re.search('Ratings: (\d+,?\d*)?', td_text)
    if match_nb_ratings:
        nb_ratings = match_nb_ratings.group(1)
        infos_dict['nb_ratings'] = nb_ratings

    match_nb_reviews = re.search('Reviews: (\d+,?\d*)?', td_text)
    if match_nb_reviews:
        nb_reviews = match_nb_reviews.group(1)
        infos_dict['nb_reviews'] = nb_reviews

    match_r_avg = re.search('rAvg: (\d+\.?\d*)?', td_text)
    if match_r_avg:
        r_avg = match_r_avg.group(1)
        infos_dict['r_avg'] = r_avg

    match_p_dev = re.search('pDev: (\d+\.?\d*)?', td_text)
    if match_p_dev:
        p_dev = match_p_dev.group(1)
        infos_dict['p_dev'] = p_dev

    print str(infos_dict)


def parse_beer_profile(beer_profile_url):
    show_all_ratings_url_suffix = '?show_ratings=Y'
    with_ratings_url = beer_profile_url + show_all_ratings_url_suffix
    soup = make_soup(with_ratings_url)
    beer_name = get_beer_name(soup)
    #TODO
    get_beer_stats(soup)


def fast_count_number_of_beers():
    logger.info('Fast counting number of beers...')
    dict_url_styles = get_styles_url_and_names()
    total = 0
    for url in dict_url_styles.keys():
        real_nb_beers = int(find_max(url))
        total += real_nb_beers
    logger.info('Total number of beers: '+str(total))
    return total

def count_number_of_beers():
    logger.info('Counting number of beers...')
    dict_url_styles = get_styles_url_and_names()
    total = 0
    for url in dict_url_styles.keys():
        real_nb_beers = int(find_max(url))
        beer_urls = get_all_beers_from_substyle(url)
        style_number = len(beer_urls)
        if style_number != real_nb_beers:
            logger.error('Error: wrong number of beers detected')
            logger.error('Expected: ' + str(real_nb_beers) + ' found: ' + str(style_number))
            logger.error('URL: '+url)
            raise
        # print substyle_name + ': ' + str(style_number)
        total += style_number

    logger.info('Total number of beers: '+str(total))
    return total


def count_number_of_ratings_and_comments_for_beer_url(beer_url):
    '''
    Returns a tuple (nb_ratings, nb_comments), representing the
    number of ratings and comments for a given beer page.
    '''
    soup = make_soup(beer_url)
    ba_content = soup.find(id='baContent')
    divs = ba_content.find_all('div', recursive=False, limit=6)
    last_div = divs[5]
    text = last_div.get_text()
    nb_ratings = 0
    nb_reviews = 0

    # now parse it
    # WARNING: Ratings and Reviews use ',' for thousands!
    match_nb_ratings = re.search('Ratings: (\d+,?\d*)?', text)
    match_nb_reviews = re.search('Reviews: (\d+,?\d*)?', text)
    beer_name = get_beer_name(soup)
    logger.debug('Counting for ' + beer_name)
    try:
        if match_nb_ratings:
            nb_ratings = int(match_nb_ratings.group(1).replace(',', ''))

        if match_nb_reviews:
            nb_reviews = int(match_nb_reviews.group(1).replace(',', ''))

        if nb_ratings < nb_reviews:
            logger.warn('More ratings than reviews: '+beer_name)

        logger.debug(nb_ratings, nb_reviews)
        return (nb_ratings, nb_reviews)

    except Exception:
        logger.error('Error on beer: ' + beer_name)
        logger.error('text: '+text)
        logger.error(match_nb_ratings.group(1))
        logger.error(match_nb_reviews.group(1))
        raise


def get_all_beers_urls():
    """ Returns a list of beer URLs

    List is made of tuples <URL, beer style, global style>
    """
    url_list = []
    style_url_dict = get_styles_url_and_names()

    for style_url in style_url_dict.keys():
        (style, global_style) = style_url_dict[style_url]
        style_beers_urls = get_all_beers_from_substyle(style_url)

        for beer_url in style_beers_urls:
            url_list.append((beer_url, style, global_style))

        if(len(url_list) > 10):
            return url_list

    return url_list


def get_beer_comments_and_ratings(beer_profile_url):
    soup_making_start = time.time()
    soup = make_soup(beer_profile_url)
    soup_making_time = time.time() - soup_making_start
    logger.debug('Time for soup making: ' + str(soup_making_time))


def parsers_compare(url, parser_list):
    try:
        times_list = []

        r = requests.get(url)
        if r.status_code != requests.codes.ok:
            print 'Error: status code is ' + str(r.status_code) + ' for URL: ' + url
            sys.exit(1)
        contents = r.content

        for parser in parser_list:
            start = time.time()
            try:
                soup = BeautifulSoup(contents, parser)
            except:
                logger.error('Parser could not be used: '+parser)

            soup_time = time.time() - start
            times_list.append(soup_time)

        return times_list

    except:
        logger.error('Error handling URL: ' + str(url))
        raise


def parsers_compare_main():
    if os.path.exists('beers'):
        logger.info('Loading beer URL list from file')
        beer_urls = pickle.load(open('beers', 'rb'))
    else:
        start = time.time()
        beer_urls = get_all_beers_urls()
        end = time.time()
        total_time = end - start
        logger.info('Time fetching URLs: '+str(total_time))
        outfile = open('beers', 'wb')
        pickle.dump(beer_urls, outfile)

    max_iter = 10

    parser_list = ['lxml', 'html5lib', 'html.parser']

    total_times = [0 for p in parser_list]

    for i in range(max_iter):
        beer_url = random.choice(beer_urls)
        time_list = parsers_compare(beer_url, parser_list)
        for i in range(len(time_list)):
            total_times[i] += time_list[i]

    avg_times = [t/max_iter for t in total_times]
    
    index = 0
    for avg_time in avg_times:

        logger.info('Parser: '+parser_list[index]+' Average time: '+str(avg_time))
        index += 1



if __name__ == '__main__':
    setup_logging()
    logger = logging.getLogger('miniscrapper')
    start = time.time()
    parsers_compare_main()
    end = time.time()
    total_time = end - start
    logger.info('Time elapsed: '+str(total_time))

    # Test review/ratings extraction
    # on http://www.beeradvocate.com/beer/profile/45/51480/
