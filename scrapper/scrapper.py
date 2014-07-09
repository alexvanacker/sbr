#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import csv
import time
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


def make_soup(url):
    """Get soup object from url """

    r = requests.get(url)
    if r.status_code != requests.codes.ok:
        raise Exception('Error: status code is %s for URL: %s',
                        str(r.status_code), url)
    contents = r.content

    soup = BeautifulSoup(contents, parser)
    return soup


def find_last_number_of_subpages_from_url(url):
    """ Wrapper method for finding last subpage for given URL

    """
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
    m = re.search('\(out of (.+?)\)', st)
    if m:
        found = m.group(1)
    else:
        logger.error('Could not extract max number of subpages: '+url)
        raise Exception
    return found


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

                if not found_place and content.name  \
                        and 'a' in content.name \
                        and 'place' in content['href']:
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
        print 'Error while working on URL: '+beer_profile_url
        raise


def write_all_beer_infos(list_url, dest_file_path, number_limit=0):
    """ Writes beer infos to a CSV file

    Writes beer infos extracted from the pages defined in list_url.

    Keyword arguments:
    list_url -- List of beer profile URLs
    dest_file_path -- Path to the csv file to write
    number_limit -- Number of beer profiles scrapped before writing to file.
    """

    dest_file = open(dest_file_path, 'wb')
    try:
        nb_beers = len(list_url)
        print 'Writing beer data to ' + dest_file_path
        print 'Number of URLs to process: ' + str(nb_beers)
        # get the first url and fetch its info to create the csv header
        found_good_url = False
        index = 0
        while not found_good_url:
            if index > nb_beers - 1:
                raise Exception('Could not find one URL that could be reached.')
            try:
                sample_infos = get_beer_infos(list_url[index])
                found_good_url = True
            except:
                index += 1

        field_names = sample_infos.keys()
        csv_writer = csv.DictWriter(dest_file, fieldnames=field_names)
        csv_writer.writeheader()

        number_beer = 0
        total_processed = 0
        total_beers = len(list_url)
        temp_array = []
        # Keep URLs that have failed
        error_list = []

        for beer_url in list_url:
            beer_info = None
            total_processed += 1
            try:
                beer_info = get_beer_infos(beer_url)
            except:
                print 'Error while loading URL: ' + beer_url
                print 'Trying again in 5 seconds...'
                time.sleep(5)

                try:
                    beer_info = get_beer_infos(beer_url)
                except Exception, e:
                    error_list.append(beer_url)
                    print 'Could not load URL: ' + beer_url
                    print str(e)
                    print 'Moving on to the next.'

            if beer_info:
                temp_array.append(beer_info)
                number_beer += 1
                if number_limit > 0 and number_beer >= number_limit:

                    # write to disk
                    write_unicode_csv_rows(temp_array, csv_writer)

                    # Reset to 0
                    number_beer = 0
                    temp_array = []

                    # Some feedback is nice
                    percent_processed = total_processed * 100 / total_beers
                    print 'Processed: ' + str(percent_processed) + '%'

        # Finish writing
        write_unicode_csv_rows(temp_array, csv_writer)

        print 'Finished writing beers to ' + dest_file_path
        print 'Number of errors: ' + str(len(error_list))

        # Write errors to file
        current_time = time.strftime('%Y_%m_%d_%H_%M_%S')
        error_file_name = 'beer_info_errors_'+current_time+'.txt'
        error_file = open(error_file_name, 'w')
        error_file.writelines(error_list)
        error_file.close()

    except Exception, e:
        print 'Global error while writing beer info to ' + dest_file_path
        print str(e)
        raise

    finally:
        dest_file.close()


def write_unicode_csv_rows(dicts, csv_writer):
    """Writes the dictionaries using the csv writer

    dicts -- Dictionaries to write
    csv_writer -- CSV writer instanciated
    """
    for dict_row in dicts:
        try:
            csv_writer.writerow({k: v.encode("utf-8").strip()
                                if v else '' for k, v in dict_row.items()})
        except Exception, e:
            print 'Error writing line: ' + str(dict_row)
            print str(e)
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
        ratings_and_reviews = extract_comments_and_ratings_from_url(suburl)
        comments_and_ratings.extend(ratings_and_reviews)

    return comments_and_ratings


def extract_comments_and_ratings_from_url(url):
    try:

        # Clean end of URL to get the main Beer URL
        beer_url = url
        if '?' in url:
            beer_url = re.sub(r'\?.*', '', url)

        empty_rating_dict = {'beer_url': beer_url, 'user_url': '',
                             'score': '', 'rdev': '', 'date': '',
                             'look': '', 'smell': '', 'taste': '', 'feel': '',
                             'overall': '', 'serving_type': '',
                             'review': ''}

        list_ratings_reviews = []
        soup = make_soup(url)

        # Used for extracting review date
        date_pattern = re.compile('(\d+-\d+-\d+ \d+:\d+)+')
        # Used for extracting serving type
        type_pattern = re.compile(('type: (.+)'))

        single_note_pattern = re.compile('(\d+\.?\d*)+')

        review_divs = soup.findAll(id='rating_fullview_content_2')

        for review_div in review_divs:
            rating_dict = empty_rating_dict.copy()

            # user url
            rating_dict['user_url'] = review_div.h6.a['href']

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
            # A review is preceded by a single <br>, if no review
            # then a double <br>
            next_el = rdev_line.next_sibling
            next_el_sibl = next_el.next_sibling
            current_el = next_el_sibl

            # Get all siblings, in any case
            all_siblings = current_el.next_siblings
            # Remove all tags from the siblings
            true_siblings = [x for x in all_siblings if not x.name]

            if not current_el.name or not 'br' in current_el.name:
                # It's a review, let's parse it

                # Current element is look, taste, etc. notes
                # Order is look, smell, taste, feel, overall
                notes_search = single_note_pattern.findall(current_el)
                try:
                    if notes_search:
                        rating_dict['look'] = float(notes_search[0])
                        rating_dict['smell'] = float(notes_search[1])
                        rating_dict['taste'] = float(notes_search[2])
                        rating_dict['feel'] = float(notes_search[3])
                        rating_dict['overall'] = float(notes_search[4])
                    else:
                        print 'Could not find note pattern on %s' % beer_url

                except Exception:
                    print 'Error getting notes on %s' % beer_url
                    raise

                # Second to last element is serving type
                serving_type_raw = true_siblings[-2]
                type_match = type_pattern.search(serving_type_raw)
                if type_match:
                    rating_dict['serving_type'] = type_match.group(1)
                else:
                    print 'Error getting serving type on %s' % beer_url

                # Remaining are comments
                review_string = " ".join(true_siblings[0: -2])
                rating_dict['review'] = review_string

            # Last is always date
            date = true_siblings[-1]
            date_match = date_pattern.match(date)
            if not date_match:
                print 'Error getting review date on %s ' % beer_url
            else:
                rating_dict['date'] = date_match.group(1)

            list_ratings_reviews.append(rating_dict)

        return list_ratings_reviews

    except Exception:
        print 'Error fetching reviews and ratings from %s' % url
        if review_div:
            print review_div
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
    second = soup.find_all(attrs={'class':"secondaryContent pairsJustified"}, recursive=True)[0]
    for dl in second.findAll('dl'):
        print dl.dt.contents[0]
        if dl.dt.contents[0] == 'Joined:':
            return dl.dd.contents[0]
    return ''


def get_user_name(soup):
    ''' get the user name in the dedicated field
    '''
    return soup.find_all(attrs={'itemprop':"name",'class':"username"},recursive=True)[0].contents[0]


def get_user_id(user_url):
    ''' parse url to get the user_id in it.
    '''
    return re.search('\.(\d+)?/$', user_url).group(1)


def get_user_infos(user_url):
    ''' given a user url, returns all the relevant information we can get
    '''
    user_infos = {'scrapped_date': '', 'user_id': '', 'user_name': '',
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

def get_brewery_from_beer(url) :
    ''' given a beer url generates the corresponding brewery url
    '''
    brew_id = re.search('profile/(\d*)/', url).group(1)
    return 'http://www.beeradvocate.com/beer/profile/'+str(brew_id)

def get_brewery_id(url):
    ''' get brewery id from url '''
    return re.search('profile/(\d+)?/$', url).group(1)

def get_brewery_infos(url):
    ''' get all brewery infos from url
    '''
    brewery_infos = {}
    brewery_infos['url'] = url
    # id, no need for soup
    brewery_infos['brewery_id'] = get_brewery_id(url)
    ## now the soup 
    soup = make_soup(url)
    # name
    brewery_infos['name'] = soup.findAll('div',attrs = {'class' : 'titleBar'})[0].h1.contents[0]
    baContent = soup.findAll('div',attrs = {'id' : 'baContent'})[0]
    # image
    brewery_infos['image_url'] = baContent.table.tr.td.img['src']
    # address
    address = {}
    a = baContent.table.table
    city = a.findAll(attrs={'href':re.compile(".*/place/list.*", re.I)})[0]
    address['city'] = city.contents[0]
    address['address'] = city.previous_sibling.previous_sibling
    a = city.parent # less to search later
    country = a.findAll(attrs={'href':re.compile(".*/place/directory/.*", re.I)})
    if len(country) == 2 :
        address['region'] = country[0].contents[0]
        address['country'] = country[1].contents[0]
        address['postal_code'] = re.search(', (.*)',country[1].previous_sibling.previous_sibling).group(1)
    else:
        address['region'] = ''
        address['country'] = country[0].contents[0]
        address['postal_code'] = re.search(', (.*)',country[0].previous_sibling.previous_sibling).group(1)
    # phone
    brewery_infos['phone'] = re.search('phone: ([^<>]*)[<>]', str(a)).group(1)
    brewery_infos['address'] = address
    # website
    brewery_infos['website'] = a.findAll('img', attrs= {'alt':'visit their website'})[0].parent['href']
    return brewery_infos
