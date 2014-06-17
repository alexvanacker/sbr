#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup

r = requests.get('http://www.beeradvocate.com/beer/profile/27039/16814/')

contents = r.content
soup = BeautifulSoup(contents)
print soup.title

