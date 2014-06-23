#!/usr/bin/env python
# -*- coding: utf-8 -*-$

import logging
import requests
import re
import sys
from pyquery import PyQuery as pq


logger = logging.getLogger(__name__)
root_url = 'http://www.beeradvocate.com'


def find_max(url):
    doc = get_doc(url)
    ba_content = doc('div').filter('#baContent')
    text = ba_content('table').eq(0)('td').eq(0)('span').eq(0)('b').text()

    m = re.search('\(out of (.+?)\)', text)
    if m:
        found = m.group(1)
    else:
        logger.error('Could not find max number of elements in ' + url)
        raise('Error finding maximum number of elements')
    return found


def get_substyle_url(url):
    '''
    From a style URL, get all the URLs of the style
    '''
    substyle_urls = []
    start = 0
    mymax = int(find_max(url))
    while start < mymax:
        substyle_urls.append(url + '?start=' + str(start))
        start = start + 50
    return substyle_urls


def get_styles_url_and_names():
    '''
    Returns a dict linking an url to a beer style and its global type
    '''
    style_url = 'http://www.beeradvocate.com/beer/style/'
    doc = get_doc(style_url)
    # table of class 'mainContent'
    table = doc('table')
    first_tr = table.find('tr').eq(0)
    tds = first_tr.children()
    style_dict = {}
    for td in tds:
        td_doc = pq(td)
        beer_style_list = td_doc('tr').eq(1)('td')
        # This is ugly, cuz the page is ugly...
        style_name = ''

        for el in beer_style_list.children():
            doc_el = pq(el)
            if doc_el.is_('b'):
                # Then it's a style name
                style_name = doc_el.text()

            elif doc_el.is_('a'):
                # Add to dictionary
                beer_substyle = doc_el.text()
                url = doc_el.attr('href')
                style_dict[root_url + url] = (beer_substyle, style_name)

    return style_dict


def count_number_beers():
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
            logger.error('URL: ' + url)
            raise
        # print substyle_name + ': ' + str(style_number)
        total += style_number

    logger.info('Total number of beers: '+str(total))
    return total


def get_doc(url):
        '''
        Get soup object from url
        '''
        r = requests.get(url)
        if r.status_code != requests.codes.ok:
            logger.error('Error: status code is ' + str(r.status_code) +
                         ' for URL: ' + url)
            sys.exit(1)

        contents = r.content
        doc = pq(contents)
        return doc


def get_all_beers_from_substyle(substyle_url):
    '''
    Return all the beers from a substyle URL.
    '''
    url_list = []
    # Get list of all pages for the substyle which contains all beers!
    substyle_urls = get_substyle_url(substyle_url)
    count = 0
    for page_url in substyle_urls:
        doc = get_doc(page_url)
        all_a_anchors = doc.find('a')
        for a in all_a_anchors:
            doc_a = pq(a)
            href = doc_a.attr('href')

            if href and re.search('beer/profile/(.+)/(.+)/$', href):
                count += 1
                # print href
                url_list.append(root_url + href)
    return url_list
