#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import time
import sys
import re
import logging
import logging.config
from bs4 import BeautifulSoup
from bs4 import FeatureNotFound


logger = logging.getLogger(__name__)

# Define which parser to use
parser_lxml = "lxml"
parser_html5 = "html5lib"
parser = parser_lxml
try:
    test_soup = BeautifulSoup('<html></html>', parser)
except FeatureNotFound:
    # print because logger may not be defined at this stage
    print parser + ' not found, switching to '+parser_html5
    parser = parser_html5
    test_soup = BeautifulSoup('<html></html>', parser)


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


def get_beer_infos(beer_profile_url):
    """Return a dict containing beer information

    Dict contains name, ABV, etc. #TODO finish docstring
    """

    info_dict = {}
    soup = make_soup(beer_profile_url)
    beer_name = get_beer_name(soup)
    info_dict['name'] = beer_name

    # Main info container
    main_div = soup.find(id='baContent')
    infos_tr = main_div.table.tr

    # Get photo URL
    photo_img = infos_tr.td.find('img')
    info_dict['image_url'] = photo_img['src']

    # Warning: tbody not seen by lxml parser
    if parser == parser_lxml:
        infos_tbody = infos_tr.find_all('td', recursive=False)[1].table
    elif parser == parser_html5:
        infos_tbody = infos_tr.find_all('td', recursive=False)[1].table.tbody
    else:
        logger.error('Unhandled parser: ' + parser)
        raise

    infos_td = infos_tbody.find_all('tr', recursive=False)[1].td

    infos_td_contents = infos_td.contents
    # String element if td is at the end, and contains the added by
    # Did mention 'ugly'?
    added_by_string = infos_td_contents[-1]
    m_added_user = re.search('added by: ((.*)+)? on', added_by_string)
    if m_added_user:
        info_dict['added_by'] = m_added_user.group(1)

    m_added_date = re.search('on (\d+-\d+-\d+)?', added_by_string)
    if m_added_date:
        info_dict['added_on'] = m_added_date.group(1)

    # Availability also
    found_place = False
    for content in infos_td_contents:
        content_string = content.string

        if content_string != None:

            if content_string.find('Brewed') > -1:
                    brewery = content.find_next('a').b.string
                    info_dict['brewery'] = brewery

            if not found_place and content.name != None \
                and content.name.find('a') > -1 and content['href'].find('place') > -1:
                location = ''
                double_break = False
                previous_was_br = False
                found_place = True
                el = content
                index = infos_td_contents.index(el)
                while not double_break:
                    el = infos_td_contents[index]

                    if el.string != None and el.string.strip() != '':
                        location += ' ' + el.string.strip()

                    el_name = el.name
                    if el_name != None and el_name.find('br') > -1:
                        double_break = previous_was_br
                        previous_was_br = True
                    else:
                        previous_was_br = False
                    
                    index += 1

                info_dict['brewery_location'] = location

            if content_string.find('Style') > -1:
                a_tag = content.find_next('a')
                style = a_tag.b.string
                info_dict['style'] = style

                # Get ABV also
                index = infos_td_contents.index(a_tag)
                abv_string = infos_td_contents[index + 1].replace('|', '').replace('%','').strip()
                info_dict['abv'] = abv_string

            if content_string.find('Avail') > -1:
                index = infos_td_contents.index(content)
                info_dict['availability'] = infos_td_contents[index + 1].strip()

            if content_string.find('Notes') > -1:
                index = infos_td_contents.index(content)
                index += 1
                notes = ''
                while index < len(infos_td_contents) - 1:
                    el = infos_td_contents[index]
                    el_string = el.string
                    if el_string != None and el_string.strip() != '':
                        notes += ' ' + el_string.strip()
                    index += 1
                info_dict['notes'] = notes
                
    return info_dict


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

    return url_list


def get_beer_comments_and_ratings(beer_profile_url):
    soup_making_start = time.time()
    soup = make_soup(beer_profile_url)
    soup_making_time = time.time() - soup_making_start
    logger.debug('Time for soup making: ' + str(soup_making_time))


def handle_info_key(key, valuesoup) :
    if key == 'Gender:' :
        mytuple = ('Gender',valuesoup.contents[0])
    elif key == 'Birthday:': 
        mytuple = ('Birth_Year','')  # TODO
    elif key == 'Location:' : 
        mytuple = ('Location' , valuesoup.a.contents[0] )
    elif key == 'Home page:' :
        mytuple = ('Home_Page','') # TODO do we need ? 
    elif key == 'Occupation:':
        mytuple = ('Occupation', valuesoup.contents[0] ) 
    elif key == 'Content:' : 
        mytuple = ('Content','') # TODO do we need ? 
    else : # should not be the case but we never know. 
        mytuple = (key,valuesoup.contents[0])
    return mytuple

def get_user_id(user_url):
    # parse url to get the user_id in it. 
    return re.search('\.(\d+)?/$', user_url).group(1)

def get_user_infos(user_url) :
    user_infos = {'user_id':'','Occupation':'','Location':'','Gender':'','Birth_Year':'','Content':'','Home_Page':''}
    user_infos['user_id'] = get_user_id(user_url)
    soup = make_soup(user_url)
    about = soup.find_all('li',attrs={"class":'profileContent','id':'info'})
    dls = about[0].find_all('dl')
    for dluser in dls :
        info = handle_info_key(dluser.dt.contents[0], dluser.dd)
        user_infos[info[0]] = info[1]
    return user_infos
