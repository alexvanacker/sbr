#!/usr/bin/env python
# -*- coding: utf-8 -*-$

from bs4 import BeautifulSoup
from pyquery import PyQuery as pq
import time
import sys
import requests
import os
import json
import logging
import logging.config
import pyquerycrawler as pqc
import miniscrapper


def setup_logging(
    default_path='logging.json',
    default_level=logging.INFO,
    env_key='LOG_CFG'
):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        f = open(path, 'rt')
        config = json.load(f)
        logging.config.dictConfig(config=config)
    else:
        logging.basicConfig(level=default_level)


def run_beautiful_soup():
    '''
    Get all beer URLs then reads the number of comments and reviews
    from a random 100 of them.
    '''
    logger.info('Starting beautiful soup test...')
    miniscrapper.count_number_of_beers()


def run_pyquery():
    logger.info('Starting PyQuery test...')
    pqc.count_number_beers()


setup_logging(default_level=logging.DEBUG)
logger = logging.getLogger('speedcompare')

# start = time.time()
# run_pyquery()
# pyquery_time = time.time() - start

# start = time.time()
# run_beautiful_soup()
# bs_time = time.time() - start

# logger.info('PyQuery time: '+str(pyquery_time))
# logger.info('BeautifulSoup time: '+str(bs_time))
