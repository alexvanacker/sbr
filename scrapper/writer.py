#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import os
import scrapper
import time
import gzip


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
        print 'Writing file: ' + os.path.abspath(dest_file.name)
        print 'Number of URLs to process: ' + str(nb_elements)

         # Get the first url and fetch its info to create the csv header
        found_good_url = False
        index = 0
        while not found_good_url:
            try:
                sample_infos = scrapper_function(list_url[index])
                found_good_url = True
            except:
                index += 1
                if index > nb_elements - 1:
                    print 'Could not find one URL that could be reached.'
                    raise

        if isinstance(sample_infos, list):
            field_names = sample_infos[0].keys()
        else:
            field_names = sample_infos.keys()

        csv_writer = csv.DictWriter(dest_file, fieldnames=field_names)
        csv_writer.writeheader()

        current_processed = 0
        total_processed = 0
        temp_array = []
        # Keep URLs that have failed
        error_list = []

        for url in list_url:
            info = None
            total_processed += 1
            try:
                info = scrapper_function(url)
            except:
                print 'Error while loading URL: ' + url
                print 'Trying again in 5 seconds...'
                time.sleep(5)

                try:
                    info = scrapper_function(url)

                except Exception, e:
                    error_list.append(url)
                    current_processed += 1
                    print 'Could not load URL: ' + url
                    print str(e)
                    print 'Moving on to the next.'

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
                    percent_processed = total_processed * 100 / nb_elements
                    print 'Processed: ' + str(percent_processed) + '%'

        # Finish writing
        write_unicode_csv_rows(temp_array, csv_writer)

        print 'Finished writing beers to ' + dest_file_path
        print 'Number of errors: ' + str(len(error_list))

        # Write errors to file
        if error_list:
            current_time = time.strftime('%Y_%m_%d_%H_%M_%S')
            error_file_name = 'beer_info_errors_'+current_time+'.txt'
            error_file = open(error_file_name, 'w')
            error_file.writelines(error_list)
            error_file.close()

    except Exception:
        print 'Error while writing data'
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

    for beer_url in list_url:
        last_page = scrapper.find_last_number_of_subpages_from_url(beer_url)
        start = 0
        last_page_int = int(last_page)

        # Get list of review URLs for the beer
        while start <= last_page_int:
            url_ratings = beer_url + '?hideRatings=N&start=' + str(start)
            reviews_urls.append(url_ratings)
            # Reviews are 25 by 25
            start = start + 25

    # Now we write
    global_writer(reviews_urls, dest_file_path,
                  scrapper.extract_reviews_from_url, write_every_nbr,
                  size_limit, compress)


def is_file_above_limit(filepath, limit=0):
    """ Checks if given filepath has size above given limit.

    Returns true if size if above the limit, false otherwise. Raises an
    exception if the file does not exist.

    filepath -- Path to the file to check
    limit -- Size limit in Mb
    """

    if not os.path.exists(filepath):
        raise Exception('File does not exist: '+filepath)

    size_in_b = os.path.getsize(filepath)
    size_in_mb = size_in_b / (1024 * 1024)
    if limit > 0 and size_in_mb > limit:
        return True
    else:
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
            print 'Error writing line: ' + str(dict_row)
            print str(e)
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
