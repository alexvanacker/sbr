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
    '''
    Get soup object from url
    '''
    r = requests.get(url)
    # FIXME test if response code is OK!
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
    From a style get all the pages of the style
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


def get_beer_name(profile_page_soup):
    title_bar = profile_page_soup.find(class_='titleBar')
    h1 = title_bar.h1
    return h1.contents[0]


def get_beer_comments_and_ratings(beer_profile_url):
    # TODO
    pass


def get_beer_stats(profile_page_soup):

    infos_dict = {}

    main_div = profile_page_soup.find(id='baContent')
    stats_tr = main_div.table.tr.find_all('td')[1].find('tr')
    real_stats_tr = stats_tr.find('tr')
    stats_td_list = real_stats_tr.find_all('td', recursive=False)
    
    if len(stats_td_list) < 3:
        print 'Error on profile page, not enough columns'
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
    match_nb_ratings = re.search('Ratings: (\d+)?', td_text)
    if match_nb_ratings:
        nb_ratings =  match_nb_ratings.group(1)
        infos_dict['nb_ratings'] = nb_ratings
    
    match_nb_reviews = re.search('Reviews: (\d+)?', td_text)
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
    #print str(sullary_contents)

    print str(infos_dict)


def parse_beer_profile(beer_profile_url):
    show_all_ratings_url_suffix = '?show_ratings=Y'
    with_ratings_url = beer_profile_url + show_all_ratings_url_suffix
    soup = make_soup(with_ratings_url)
    beer_name = get_beer_name(soup)
    get_beer_stats(soup)


if __name__ == '__main__':
    parse_beer_profile('http://www.beeradvocate.com/beer/profile/16315/61128/')
