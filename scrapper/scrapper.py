#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import time
import re
import logging
import logging.config
import datetime
from urlparse import urlparse
from urlparse import parse_qs
from bs4 import BeautifulSoup
from bs4 import FeatureNotFound
from bs4 import NavigableString

import utils

parser_lxml = "lxml"
parser_html5 = "html5lib"
parser = parser_lxml

logger = logging.getLogger(__name__)

try:
    test_soup = BeautifulSoup('<html></html>', parser)
    logger.info('Using parser : ' + parser)
except FeatureNotFound:
    logger.info(parser + ' not found, switching to '+parser_html5)
    parser = parser_html5
    test_soup = BeautifulSoup('<html></html>', parser)


def get_styles_url_and_names():
    """ Get beer style URL

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


def test_access_url(url, time_pause_sec=5):
    """ Test if URL is accessible

    If fails, tries again in timeout seconds.
    If a second fail occurs, considers URL not accessible

    url -- URL to test_soup
    time_pause_sec -- Time to wait between two tries in seconds
    """
    r = requests.get(url)
    if r.status_code != requests.codes.ok:
        time.sleep(5)
        r = requests.get(url)
        if r.status_code != requests.codes.ok:
            raise Exception('Error: status code is %s for URL: %s' %
                            (str(r.status_code), url))


def make_soup(url):
    """Get soup object from url """

    r = requests.get(url)
    if r.status_code != requests.codes.ok:
        raise Exception('Error: status code is %s for URL: %s' %
                        (str(r.status_code), url))

    contents = r.content

    soup = BeautifulSoup(contents, parser)
    return soup


def find_last_number_of_subpages_from_url(url):
    """ Wrapper method for finding last subpage for given URL """

    soup = make_soup(url)
    return find_last_number_of_subpages(soup, url)


def find_last_number_of_subpages(soup, url):
    """ Finds the last subpage number in the soup.

    Based on the link to last. URL is used for feedback if error.
    """

    #5th div
    div_with_last = (soup.body.findAll(id='baContent')[0]
                     .findAll('div', recursive=False)[4])

    # Check that it has subpages
    if div_with_last.b:
        last_a = div_with_last.findAll('a', recursive='False')[-1]
        href = last_a['href']
        match = re.search('start=(\d+)', href)

        if match:
            return match.group(1)

        else:
            logger.error('Could not extract max number of subpages: ' + url)
            raise Exception('Could not extract max number of subpages: ' + url)

    else:
        return '0'


def find_max(url):
    soup = make_soup(url)
    st = soup.body.findAll(id='baContent')[0].table.td.span.b.contents[0]
    first_split = st.split('out of')
    try:
        second_split = first_split[1].split(')')
        max_page = second_split[0].strip()
        int(max_page)
        return max_page
    except Exception, e:
        logger.error('Could not extract max number of subpages: '+url)
        raise 
    

def get_substyle_url(url):
    """From a style get all the pages of the style """

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
    try:
        info_dict = {}
        soup = make_soup(beer_profile_url)
        beer_name = get_beer_name(soup)
        info_dict['beer_url'] = beer_profile_url
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
            infos_tbody = (infos_tr.find_all('td', recursive=False)[1]
                           .table.tbody)
        else:
            logger.error('Unhandled parser: ' + parser)
            raise

        infos_td = infos_tbody.find_all('tr', recursive=False)[1].td

        infos_td_contents = infos_td.contents
        # String element if td is at the end, and contains the added by
        # Did mention 'ugly'?
        added_by_string = infos_td_contents[-1]
        m_added_user = re.search(': (.+)? on', added_by_string)
        if m_added_user:
            info_dict['added_by'] = m_added_user.group(1)

        m_added_date = re.search('on (\d+-\d+-\d+)+', added_by_string)
        if m_added_date:
            info_dict['added_on'] = m_added_date.group(1)

        # Availability also
        found_place = False
        for content in infos_td_contents:
            content_string = content.string

            if content_string:

                if 'Brewed' in content_string and content.name \
                        and 'b' in content.name:

                            brewery = content.find_next('a').b.string
                            info_dict['brewery'] = brewery

                if (not found_place and not isinstance(content, NavigableString)
                        and content.name
                        and 'a' in content.name
                        and 'place' in content['href']):
                    location = ''
                    double_break = False
                    previous_was_br = False
                    found_place = True
                    el = content
                    index = infos_td_contents.index(el)
                    while not double_break:
                        el = infos_td_contents[index]

                        if el.string:
                            location += ' ' + el.string.strip()

                        el_name = None
                        if not isinstance(el, NavigableString):
                            el_name = el.name

                        if el_name and 'br' in el_name:
                            double_break = previous_was_br
                            previous_was_br = True
                        else:
                            previous_was_br = False

                        index += 1

                    info_dict['brewery_location'] = location

                if 'Style' in content_string and content.name \
                        and 'b' in content.name:
                    a_tag = content.find_next('a')
                    style = a_tag.b.string
                    info_dict['style'] = style

                    # Get ABV also
                    index = infos_td_contents.index(a_tag)
                    abv_string = infos_td_contents[index + 1].replace('|', '')
                    abv_string = abv_string.replace('%', '').strip()
                    info_dict['abv'] = abv_string

                if 'Avail' in content_string and content.name \
                        and 'b' in content.name:
                    index = infos_td_contents.index(content)
                    avail = infos_td_contents[index + 1].strip()
                    info_dict['availability'] = avail

                if 'Notes' in content_string > -1 and content.name \
                        and 'b' in content.name:
                    index = infos_td_contents.index(content)
                    index += 1
                    notes = ''
                    while index < len(infos_td_contents) - 1:
                        el = infos_td_contents[index]
                        el_string = el.string
                        if el_string:
                            notes += ' ' + el_string.strip()
                        index += 1
                    info_dict['notes'] = notes

        return info_dict
    except:
        logger.error('Error while working on URL: %s', beer_profile_url)
        raise


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
            logger.error('Expected: %s found: %s', str(real_nb_beers),
                         str(style_number))
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

        logger.debug(str(nb_ratings), str(nb_reviews))
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
    """Return list of comments and ratings for beer URL.

    Tuple is made of url, user_name, user_url, rating, comment...
    """
    comments_and_ratings = []

    # Get list of subpages
    last_page = find_last_number_of_subpages_from_url(beer_profile_url)
    comments_and_ratings_urls = []
    start = 0
    last_page_int = int(last_page)

    while start <= last_page_int:
        url_ratings = beer_profile_url + '?hideRatings=N&start=' + str(start)
        comments_and_ratings_urls.append(url_ratings)
        # Reviews are 25 by 25
        start = start + 25

    for suburl in comments_and_ratings_urls:
        ratings_and_reviews = extract_reviews_from_url(suburl)
        comments_and_ratings.extend(ratings_and_reviews)

    return comments_and_ratings


def extract_reviews_from_url(url):
    try:
        # Avoid raising exception... In the except section
        review_div = None

        logger.debug('Getting reviews from %s', url)
        # Clean end of URL to get the main Beer URL
        beer_url = url
        if '?' in url:
            beer_url = re.sub(r'\?.*', '', url)

        # Kept begin of review order int
        review_order = 0
        if 'start=' in url:
            parse_result = urlparse(url)
            query_dict = parse_qs(parse_result.query)
            try:
                review_order = int(query_dict['start'][0])
            except:
                logger.error('Could not get start index. Query string: '+str(query_dict))
                raise

        empty_rating_dict = {'beer_url': beer_url, 'user_url': '',
                             'score': '', 'rdev': '', 'date': '',
                             'review': '', 'scrap_time': '', 'review_order': ''}

        list_ratings_reviews = []
        soup = make_soup(url)

        review_divs = soup.findAll(id='rating_fullview_content_2')

        for review_div in review_divs:

            rating_dict = empty_rating_dict.copy()
            rating_dict['review_order'] = str(review_order)
            review_order += 1

            now = datetime.datetime.now()
            rating_dict['scrap_time'] = str(now)

            # Date
            muted = review_div.find_all(class_='muted')
            date = muted[-1].find_all('a')[-1].contents[0]
            real_date = utils.extract_date(date, current_date=now)
            rating_dict['date'] = str(real_date)

            # user url
            rating_dict['user_url'] = review_div.find(class_='username')['href']

            # score
            bascore = review_div.find(class_='BAscore_norm')
            rating_dict['score'] = bascore.contents[0]

            # Now we'll process line by line... Always ugly
            # rdev - useful?
            norm_line = review_div.find(class_='rAvg_norm')

            rdev_line = norm_line.next_sibling
            rdev_string = rdev_line.string
            # Need to take into account rDev 0%
            if not '%' in rdev_string:
                rdev_line = rdev_line.next_sibling
                rdev_string = rdev_line.string
            rdev = rdev_line.string.replace('%', '').replace('rDev', '').strip()
            rating_dict['rdev'] = rdev

            # If there is a review, then we have more info
            next_el = rdev_line.next_sibling
            next_el_sibl = next_el.next_sibling
            current_el = next_el_sibl

            # Get all siblings, in any case
            all_siblings = current_el.next_siblings
            # Remove all tags from the siblings
            true_siblings = [x for x in all_siblings
                             if isinstance(x, NavigableString) or not x.name]

            # It's a review, let's parse it
            review_string = " ".join(true_siblings[0: -2])
            rating_dict['review'] = review_string

            list_ratings_reviews.append(rating_dict)

        return list_ratings_reviews

    except Exception:
        logger.error('Error fetching reviews and ratings from %s' % url)
        if review_div:
            logger.error('Div: ')
            logger.error(review_div)
        raise


def handle_info_key(key, valuesoup):
    ''' handle different values of soup according to different key
    '''
    if key == 'Gender:':
        mytuple = ('gender', valuesoup.contents[0])
    elif key == 'Birthday:':
        catch = re.search(', (\d+)? \(', valuesoup.contents[0])
        year = '' if not catch else catch.group(1)
        mytuple = ('birth_year', year)
    elif key == 'Location:':
        mytuple = ('location', valuesoup.a.contents[0])
    elif key == 'Home page:':
        mytuple = ('home_page', '')  # TODO do we need ?
    elif key == 'Occupation:':
        mytuple = ('occupation', valuesoup.contents[0])
    elif key == 'Content:':
        mytuple = ('content', '')  # TODO do we need ?
    else:  # should not be the case but we never know.
        mytuple = (key, valuesoup.contents[0])
    return mytuple


def get_user_join_date(soup):
    ''' get user join date from dedicated field
    '''
    second = soup.find_all(attrs={'class': "secondaryContent pairsJustified"},
                           recursive=True)[0]
    for dl in second.findAll('dl'):
        if dl.dt.contents[0] == 'Joined:':
            return dl.dd.contents[0]
    return ''


def get_user_name(soup):
    ''' get the user name in the dedicated field
    '''
    return soup.find_all(attrs={'itemprop': "name", 'class': "username"},
                         recursive=True)[0].contents[0]


def get_user_id(user_url):
    ''' parse url to get the user_id in it.
    '''
    return re.search('\.(\d+)?/$', user_url).group(1)


def get_user_infos(user_url):
    ''' given a user url, returns all the relevant information we can get
    '''
    user_infos = {'user_id': '', 'user_name': '',
                  'join_date': '', 'occupation': '', 'location': '',
                  'gender': '', 'birth_year': '', 'content': '',
                  'home_page': ''}
    user_infos['user_id'] = get_user_id(user_url)
    soup = make_soup(user_url)
    user_infos['user_name'] = get_user_name(soup)
    user_infos['join_date'] = get_user_join_date(soup)
    about = soup.find_all('li', attrs={"class": 'profileContent', 'id': 'info'})
    dls = about[0].find_all('dl')
    for dluser in dls:
        info = handle_info_key(dluser.dt.contents[0], dluser.dd)
        user_infos[info[0]] = info[1]
    return user_infos


def get_brewery_from_beer(url):
    """ given a beer url generates the corresponding brewery url """
    brew_id = re.search('profile/(\d*)/', url).group(1)
    return 'http://www.beeradvocate.com/beer/profile/'+str(brew_id)


def get_brewery_id(url):
    ''' get brewery id from url '''
    return re.search('profile/(\d+)/?$', url).group(1)


def get_brewery_infos(url):
    ''' get all brewery infos from url
    '''
    brewery_infos = {}
    brewery_infos['url'] = url
    # id, no need for soup
    brewery_infos['brewery_id'] = get_brewery_id(url)
    # now the soup
    soup = make_soup(url)
    # name
    brewery_infos['name'] = soup.findAll('div', attrs={'class': 'titleBar'})[0].h1.contents[0]
    baContent = soup.findAll('div', attrs={'id': 'baContent'})[0]
    # image
    brewery_infos['image_url'] = baContent.table.tr.td.img['src']
    # address
    a = baContent.table.table
    try:
        city = a.findAll(attrs={'href': re.compile(".*/place/list.*", re.I)})[0]
        brewery_infos['city'] = city.contents[0]
        brewery_infos['address'] = city.previous_sibling.previous_sibling
    except:
        brewery_infos['city'] = ''
        brewery_infos['address'] = ''
    try:
        country = a.findAll(attrs={'href': re.compile(".*/place/directory/.*", re.I)})
        if len(country) == 2:
            brewery_infos['region'] = country[0].contents[0]
            brewery_infos['country'] = country[1].contents[0]
            try:
                brewery_infos['postal_code'] = re.search(', (.*)',country[1].previous_sibling.previous_sibling).group(1)
            except:
                brewery_infos['postal_code'] = ''
        else:
            brewery_infos['region'] = ''
            brewery_infos['country'] = country[0].contents[0]
            try:
                brewery_infos['postal_code'] = re.search(', (.*)',country[0].previous_sibling.previous_sibling).group(1)
            except:
                brewery_infos['postal_code'] = ''
    except:
        brewery_infos['region'] = ''
        brewery_infos['country'] = ''
    # phone
    try:
        brewery_infos['phone'] = re.search('phone: ([^<>]*)[<>]', str(a)).group(1)
    except:
        brewery_infos['phone'] = ''
    # website
    try:
        brewery_infos['website'] = a.findAll('img', attrs= {'alt':'visit their website'})[0].parent['href']
    except:
        brewery_infos['website'] = ''

    return brewery_infos
