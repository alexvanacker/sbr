import requests
import json

def get_info_from_adress(address, way = 'google') :
    ''' get all information from geocoding
        given the api we want to use
        currently only google available
    '''
    if way == 'google' : 
        return callGoogleMaps(address)
    else :
        return 'option %s is not available' %way

def callGoogleMaps(adress):
    ''' Given an address, get all infos avalable from google api
    '''
    url = "https://maps.googleapis.com/maps/api/geocode/json?address="
    split_adress = adress.split()
    plus = "+"
    urlToCall = url+ plus.join(split_adress)
    r = requests.get(urlToCall)
    json = r.json()
    return json

def get_coordinates_from_result(result, way = 'google') :
    ''' extract only latitude and longitude from the api result
        currently only google supported
    ''' 
    if way == 'google' : 
        gpsCoord = result["results"][0]['geometry']['location']
        return (gpsCoord['lat'],gpsCoord['lng'])
    else :
        return ('','')

# ex : 
# address = '87 Santilli Hwy Everett, Massachusetts, 02149-1906 United States'
# get_coordinates_from_result(callGoogleMaps(address))