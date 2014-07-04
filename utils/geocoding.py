#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json

def get_info_from_adress(address, way = 'mapbox') :
    ''' get all information from geocoding
        given the api we want to use
        currently only google available
    '''
    if way == 'google' : 
        return callGoogleMaps(address)
    elif way == 'mapbox' : 
        return call_mapbox(address)
    else :
        return 'option %s is not available' %way

def callGoogleMaps(adress):
    ''' Given an address, get all infos available from google api
    '''
    url = "https://maps.googleapis.com/maps/api/geocode/json?address="
    split_adress = adress.split()
    plus = "+"
    urlToCall = url+ plus.join(split_adress)
    r = requests.get(urlToCall)
    json = r.json()
    return json
    
def call_mapbox(adress, mapid=None, apikey = None):
    ''' Given an address, get all infos available from mapbox
        Should be supported : mapid and apikey
    '''
    mapid = 'examples.map-zr0njcqy' # should be deleted (just for example sake here)
    # apikey = 'l0lIlolV4nAckeRStress4enP3rdreS3ScheV3uX'
    if mapid : 
        url = 'http://api.tiles.mapbox.com/v3/'+ mapid + '/geocode/'
        split_adress = adress.split()
        plus = "+"
        urlToCall = url+ plus.join(split_adress) + '.json'
        r = requests.get(urlToCall)
        json = r.json()
        return json
    elif apikey :
        return ''
    else : 
        return 'please give a mapid or apikey'

def get_coordinates_from_result(result, way = 'google') :
    ''' extract only latitude and longitude from the api result
        mapbox and google supported
    ''' 
    if way == 'google' : 
        gpsCoord = result["results"][0]['geometry']['location']
        return (gpsCoord['lat'],gpsCoord['lng'])
    elif way == 'mapbox' : 
        gpsCoord = a['results'][0][0]
        return (gpsCoord['lat'],gpsCoord['lon'])
    else :
        return ('','')

# EXAMPLES
# a = get_info_from_adress(address, way = 'mapbox')
# get_coordinates_from_result(a,way='mapbox')
# a = get_info_from_adress(address, way = 'google')
# get_coordinates_from_result(a,way='google')

# TODO :
# args and kwargs for mapbox 
# apikey support