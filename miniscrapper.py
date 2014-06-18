#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import re
from bs4 import BeautifulSoup


def get_styles_url_and_names():
    '''
    Returns a dict linking an url to a beer style and its global type
    '''

    root_page = 'http://www.beeradvocate.com'
    current_page = 'http://www.beeradvocate.com/beer/style/'
    r = requests.get(current_page)

    contents = r.content
    soup = BeautifulSoup(contents)

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
    r = requests.get(url)
    contents = r.content
    soup = BeautifulSoup(contents)
    return soup


def find_max(url):
    soup = make_soup(url)
    st = soup.body.findAll(id='baContent')[0].table.td.span.b.contents[0]
    m = re.search('\(out of (.+?)\)', st)
    if m:
        found = m.group(1)
    else:
        print "FUUUUUUUUCKKKKK"
    return found


def get_substyle_url(url):
    '''
    From a style get all the page of the style
    '''
    substyle_urls = []
    start = 0
    mymax = int(find_max(url))
    while start < mymax:
        substyle_urls.append(url + '?start=' + str(start))
        start = start + 50
    return substyle_urls


def get_all_beers_from_substyle(substyle_url):
    root_url = 'http://www.beeradvocate.com/'
    soup = make_soup(substyle_url)
    st = soup.find(id='baContent')
    url_list = []
    links = st.find_all('a')
    for link in links:
        if is_beer_profile(link):
            beer_profile_url = link['href']
            full_beer_url = root_url + beer_profile_url
            url_list.append(full_beer_url)
    return url_list


def is_beer_profile(tag):
    url = tag['href']
    m = re.search('beer/profile/(.+)/(.+)/$', url)
    return m

if __name__ == '__main__':
    style_dict = get_styles_url_and_names()
    for style_url in style_dict.keys():
        list_beer = get_all_beers_from_substyle(style_url)
        print str(list_beer)
