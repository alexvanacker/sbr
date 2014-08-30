#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import os
import scrapper
import time
import datetime
import gzip
import logging

logger = logging.getLogger(__name__)


def global_writer(list_url, dest_file_path, scrapper_function,
                  write_every_nbr=0, size_limit=0, compress=True):
    """ Writer interface for any writer

    When writing a writer code, call this as your main writer.

    list_url -- List of URLS on which to apply a scrapper function to write
    information.
    dest_file_path -- Path to the CSV file to write.
    scrapper_function -- Function from the scrapper to apply to each URL.
    write_every_nbr -- Number of URLs to process in memory before writing to
    file. 0 means no limit. (default = 0)
    size_limit -- Size limit to the result file in Mb. 0 means no limit.
    (default = 0)
    compress - Compress the resulting file or not. (default = True)
    """

    if compress:
        dest_file = gzip.open(dest_file_path, 'wb')
    else:
        dest_file = open(dest_file_path, 'wb')

    try:
        nb_elements = len(list_url)
        logger.info('Writing file: ' + os.path.abspath(dest_file.name))
        logger.info('Number of URLs to process: ' + str(nb_elements))

         # Get the first url and fetch its info to create the csv header
        found_good_url = False
        index = 0
        logger.info('Defining CSV header...')
        while not found_good_url:
            try:
                sample_infos = scrapper_function(list_url[index])
                found_good_url = True
            except:
                index += 1
                if index > nb_elements - 1:
                    logger.error('Could not find a reachable URL.')
                    raise

        if isinstance(sample_infos, list):
            field_names = sample_infos[0].keys()
        else:
            field_names = sample_infos.keys()

        csv_writer = csv.DictWriter(dest_file, fieldnames=field_names)
        csv_writer.writeheader()
        logger.info('Header written')

        current_processed = 0
        total_processed = 0
        temp_array = []
        # Keep URLs that have failed
        error_list = []
        stop_writing = False

        for url in list_url:
            if stop_writing:
                break
            info = None
            total_processed += 1
            try:
                info = scrapper_function(url)
            except:
                logger.debug('Error while loading URL: ' + url)
                logger.debug('Trying again in 5 seconds...')
                time.sleep(5)

                try:
                    info = scrapper_function(url)

                except Exception, e:
                    error_list.append(url)
                    current_processed += 1
                    logger.warn('Could not load URL: ' + url, e)
                    logger.warn('Moving on to the next.')

            if info:
                if isinstance(info, list):
                    temp_array.extend(info)
                else:
                    temp_array.append(info)
                current_processed += 1
                if write_every_nbr > 0 and current_processed >= write_every_nbr:

                    # write to disk
                    write_unicode_csv_rows(temp_array, csv_writer)

                    # Reset to 0
                    current_processed = 0
                    temp_array = []

                    # Some feedback is nice
                    percent_processed = float(total_processed) / float(nb_elements)
                    logger.info('Processed: {:.2%}'.format(percent_processed))

                    # Check file size
                    if size_limit > 0 and is_file_above_limit(dest_file_path,
                                                              limit=size_limit):

                        logger.info('Size limit reached: %s MB. Stopping '
                                    'write...' % str(size_limit))
                        stop_writing = True

        # Finish writing
        if not stop_writing:
            write_unicode_csv_rows(temp_array, csv_writer)

        logger.info('Finished writing beers to ' + dest_file_path)
        logger.info('Number of errors: ' + str(len(error_list)))

        # Write errors to file
        if error_list:
            current_time = time.strftime('%Y_%m_%d_%H_%M_%S')
            error_file_name = 'writer_errors_'+current_time+'.txt'
            error_file = open(error_file_name, 'w')
            error_file.writelines(error_list)
            error_file.close()

    except Exception:
        logger.error('Error while writing data', exc_info=True)
        raise
    finally:
        dest_file.close()


def write_all_beer_infos(list_url, dest_file_path, write_every_nbr=0,
                         compress=True):
    """ Writes beer infos to a CSV file

    Writes beer infos extracted from the pages defined in list_url.

    Keyword arguments:
    list_url -- List of beer profile URLs
    dest_file_path -- Path to the csv file to write
    number_limit -- Number of beer profiles scrapped before writing to file.
    """

    global_writer(list_url, dest_file_path, scrapper.get_beer_infos,
                  write_every_nbr, compress=compress)


def write_all_beers_reviews(list_url, dest_file_path, write_every_nbr=0,
                            size_limit=0, compress=True):
    """ Writes every beers' reviews to a file

    For each beer URL given, fetches the reviews from it (and its subpages)
    and writes them to a CSV file. Write operation occurs once the number of
    reviews reaches limit.

    list_url -- list of beer URLs to process
    dest_file_path -- path to the output file
    write_every_nbr -- number of reviews to store before writing to file
    (default = 0)
    size_limit -- Size limit for the file in Mb. 0 means no limit. (default = 0)
    compress -- Write the CSV file as a compressed file (default = True)
    """

    # Get the list of all review URLs
    reviews_urls = []
    logger.info('Fetching all review URLs...')
    start_fetch = time.time()
    for beer_url in list_url:
        last_page = None
        try:
            last_page = scrapper.find_last_number_of_subpages_from_url(beer_url)
        except:
            logger.warn('Error while loading URL: ' + beer_url)
            logger.warn('Trying again in 5 seconds...')
            time.sleep(5)

            try:
               last_page = scrapper.find_last_number_of_subpages_from_url(beer_url)

            except Exception:
                logger.warn('Could not load URL: ' + beer_url)
                logger.warn('Moving on to the next.')

        if last_page:
            # Get list of review URLs for the beer
            start = 0
            last_page_int = int(last_page)
            all_nbr = range(start, last_page_int)
            url_start = beer_url + '?hideRatings=N&start='
            # Reviews are 25 by 25
            reviews_urls.extend([url_start + str(x) for x in all_nbr[::25]])
    end_fetch = time.time()
    total_time = end_fetch - start_fetch
    logger.info('Done fetching review URLs.')
    logger.debug('Time: %s' % str(datetime.timedelta(seconds=total_time)))

    # Now we write
    global_writer(reviews_urls, dest_file_path,
                  scrapper.extract_reviews_from_url, write_every_nbr,
                  size_limit, compress)


def is_file_above_limit(filepath, limit=0):
    """ Checks if given filepath has size above given limit.

    Returns true if size is strictly above the limit, false otherwise. Raises an
    exception if the file does not exist.

    filepath -- Path to the file to check
    limit -- Size limit in Mb
    """

    if not os.path.exists(filepath):
        raise Exception('File does not exist: '+filepath)

    if limit > 0:
        size_in_b = os.path.getsize(filepath)
        size_in_mb = size_in_b / (1024 * 1024)
        if size_in_mb > limit:
            logger.debug('File %s is above size limit %s Mb: %s Mb' %
                         (filepath, str(limit), str(size_in_mb)))
            return True

    return False


def write_unicode_csv_rows(dicts, csv_writer):
    """ Writes the dictionaries using the csv writer

    dicts -- Dictionaries to write
    csv_writer -- CSV writer instanciated
    """
    for dict_row in dicts:
        try:
            csv_writer.writerow({k: try_unicode_encode(v)
                                if v else '' for k, v in dict_row.items()})
        except Exception, e:
            logger.error('Error writing line: ' + str(dict_row), e)
            raise


def try_unicode_encode(v):
    """ Encodes string  in utf-8 and strips it.

    Tries to decode from utf-8 first.

    v -- String to encode
    """
    value = v
    try:
        value = v.decode('utf-8')
    except:
        pass

    value = value.encode('utf-8').strip()
    return value


def write_all_brewery_infos(list_url, dest_file_path, write_every_nbr=0,
                            compress=True):
    """ scrap and write all brewery infos into a csv  """

    global_writer(list_url, dest_file_path, scrapper.get_brewery_infos,
                  write_every_nbr, compress=compress)
