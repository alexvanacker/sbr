#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import scrapper
import time


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
