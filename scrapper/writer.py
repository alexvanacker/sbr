#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import scrapper
import time


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
            try:
                sample_infos = scrapper.get_beer_infos(list_url[index])
                found_good_url = True
            except:
                index += 1
                if index > nb_beers - 1:
                    print 'Could not find one URL that could be reached.'
                    raise

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
                beer_info = scrapper.get_beer_infos(beer_url)
            except:
                print 'Error while loading URL: ' + beer_url
                print 'Trying again in 5 seconds...'
                time.sleep(5)

                try:
                    beer_info = scrapper.get_beer_infos(beer_url)
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


def write_all_beers_reviews(list_url, dest_file_path, limit=0):
    """ Writes every beers' reviews to a file

    For each beer URL given, fetches the reviews from it (and its subpages)
    and writes them to a CSV file. Write operation occurs once the number of
    reviews reaches limit.

    list_url -- list of beer URLs to process
    dest_file_path -- path to the output file
    limit -- number of reviews to store before writing to file (default = 0)
    """
    # Prepare CSV writer
    dest_file = open(dest_file_path, 'wb')
    try:
        print 'Writing review data to ' + dest_file_path

        # get the first url and fetch its info to create the csv header
        found_good_url = False
        index = 0
        nb_beers = len(list_url)
        while not found_good_url:
            if index > nb_beers - 1:
                raise Exception('Could not find one URL that could be reached.')
            try:
                url = list_url[index]
                sample_infos = scrapper.extract_reviews_from_url(url)[0]
                found_good_url = True
            except:
                index += 1

        field_names = sample_infos.keys()
        csv_writer = csv.DictWriter(dest_file, fieldnames=field_names)
        csv_writer.writeheader()

        for beer_url in list_url:
            write_beer_reviews(beer_url, csv_writer, limit)

    except:
        print 'Global error while writing reviews to ' + dest_file_path
        raise

    finally:
        dest_file.close()


def write_beer_reviews(beer_url, csv_writer, limit=0):
    """ Writes a beer's reviews to csv file

    beer_url -- beer profile URL
    csv_writer -- CSV writer for the csv file
    limit -- number of reviews to store before writing to file (default = 0)
    """
    reviews = []
    error_list = []

    # First make sure we have access to the url
    scrapper.test_access_url(beer_url)

    # Get list of subpages
    try:
        last_page = scrapper.find_last_number_of_subpages_from_url(beer_url)
        reviews_urls = []
        start = 0
        last_page_int = int(last_page)

        # Get list of review URLs
        while start <= last_page_int:
            url_ratings = beer_url + '?hideRatings=N&start=' + str(start)
            reviews_urls.append(url_ratings)
            # Reviews are 25 by 25
            start = start + 25

        for url in reviews_urls:
            beer_reviews = None

            try:
                beer_reviews = scrapper.extract_reviews_from_url(url)
            except:
                print 'Error while loading URL: ' + url
                print 'Trying again in 5 seconds...'
                time.sleep(5)

                try:
                    beer_reviews = scrapper.extract_reviews_from_url(url)
                except Exception, e:
                    error_list.append(url)
                    print 'Could not load URL: ' + beer_url
                    print str(e)
                    print 'Moving on to the next.'

            if beer_reviews:
                reviews.extend(beer_reviews)

                if limit > 0 and len(reviews) > limit:
                    write_unicode_csv_rows(reviews, csv_writer)

                    # Reset
                    reviews = []

        # Write remaining reviews
        if len(reviews) > 0:
            write_unicode_csv_rows(reviews, csv_writer)

    except:
        print 'Error writing reviews from beer URL: ' + beer_url
        raise


def write_unicode_csv_rows(dicts, csv_writer):
    """ Writes the dictionaries using the csv writer

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
