import requests
import json

def get_info_from_address(address, way = 'mapbox',mapid=None,apikey=None) :
    ''' get all information from geocoding
        given the api we want to use
        currently only google available
    '''
    if way == 'google' : 
        return callGoogleMaps(address)
    elif way == 'mapbox' : 
        return call_mapbox(address,mapid,apikey)
    else :
        return 'option %s is not available' %way

def callGoogleMaps(address):
    ''' Given an address, get all infos available from google api
    '''
    url = "https://maps.googleapis.com/maps/api/geocode/json?address="
    split_address = address.split()
    plus = "+"
    urlToCall = url+ plus.join(split_address)
    r = requests.get(urlToCall)
    json = r.json()
    return json
    
def call_mapbox(address, mapid=None, apikey = None):
    ''' Given an address, get all infos available from mapbox
        Should be supported : mapid and apikey
    '''
    # mapid = 'examples.map-zr0njcqy' 
    # apikey = 'l0lIlolV4nAckeRStress4enP3rdreS3ScheV3uX'
    if mapid : 
        url = 'http://api.tiles.mapbox.com/v3/'+ mapid + '/geocode/'
        split_address = address.split()
        plus = "+"
        urlToCall = url+ plus.join(split_address) + '.json'
        r = requests.get(urlToCall)
        json = r.json()
        return json
    elif apikey :
        url = 'http://api.tiles.mapbox.com/v4/geocode/mapbox.places-v1/'
        split_address = address.split()
        plus = "+"
        urlToCall = url+ plus.join(split_address) + '.json' + '?access_token=' + apikey
        r = requests.get(urlToCall)
        json = r.json()
        return json
    else : 
        return 'please give a mapid or apikey'

def get_coordinates_from_result(result, way = 'google', mapbox_type = None) :
    ''' extract only latitude and longitude from the api result
        mapbox and google supported
    ''' 
    if way == 'google' : 
        gpsCoord = result["results"][0]['geometry']['location']
        return (gpsCoord['lat'],gpsCoord['lng'])
    elif way == 'mapbox' : 
        if mapbox_type == 'map_id' : 
            gpsCoord = result['results'][0][0]
            return (gpsCoord['lat'],gpsCoord['lon'])
        elif mapbox_type == 'api_key' :
            gpsCoord = result['features'][0]['geometry']['coordinates']
            return (gpsCoord[1],gpsCoord[0])
        else :
            return ('this mapbox_type is not supported',mapbox_type)
    else :
        return ('this way is not supported',way)

# EXAMPLES
# a = get_info_from_address(address, way = 'google')
# print get_coordinates_from_result(a,way='google')
# a = get_info_from_address(address, way = 'mapbox',mapid='examples.map-zr0njcqy')
# print get_coordinates_from_result(a,way='mapbox',mapbox_type = 'map_id')
# b = get_info_from_address(address, way = 'mapbox',apikey = apikey)
# print get_coordinates_from_result(b,way='mapbox',mapbox_type = 'api_key')