import re
import os
import sys
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import json
import string, random
import urllib, urllib2, httplib2
import HTMLParser
import time
import cookielib
import base64
from StringIO import StringIO
import gzip


#Provider Files
#from resources.providers.twc import TWC
#from resources.providers.dish import DISH
#from resources.providers.adobe import ADOBE
#from resources.providers.comcast import COMCAST






def FIND(source,start_str,end_str):    
    start = source.find(start_str)
    end = source.find(end_str,start+len(start_str))

    if start != -1:        
        return source[start+len(start_str):end]
    else:
        return ''

def GET_RESOURCE_ID():
    #########################
    # Get resource_id
    #########################
    """
    GET http://stream.nbcsports.com/data/mobile/passnbc.xml HTTP/1.1
    Host: stream.nbcsports.com
    Connection: keep-alive
    Accept: */*
    User-Agent: NBCSports/1030 CFNetwork/711.3.18 Darwin/14.0.0
    Accept-Language: en-us
    Accept-Encoding: gzip, deflate
    Connect
    """
    #req = urllib2.Request(ROOT_URL+'passnbc.xml')  
    #req.add_header('User-Agent',  UA_NBCSN)
    #response = urllib2.urlopen(req)        
    #resource_id = response.read()
    #response.close() 
    #resource_id = resource_id.replace('\n', ' ').replace('\r', '')
    resource_id = '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel><title>nbcsports</title><item><title>NBC Sports PGA Event</title><guid>123456789</guid><media:rating scheme="urn:vchip">TV-PG</media:rating></item></channel></rss>'

    return resource_id

def GET_SIGNED_REQUESTOR_ID():

    ##################################################
    # Use this call to get Adobe's Signed ID
    ##################################################
    """
    GET http://stream.nbcsports.com/data/mobile/configuration-2014-RSN-Sections.json HTTP/1.1
    Host: stream.nbcsports.com
    Connection: keep-alive
    Accept: */*
    User-Agent: NBCSports/1030 CFNetwork/711.3.18 Darwin/14.0.0
    Accept-Language: en-us
    Accept-Encoding: gzip, deflate
    Connection: keep-alive
    """
    req = urllib2.Request(ROOT_URL+'configuration-2014-RSN-Sections.json')  
    req.add_header('User-Agent',  UA_NBCSN)
    response = urllib2.urlopen(req)        

    json_source = json.load(response)                       
    response.close() 

    print "ADOBE PASS"
    signed_requestor_id = json_source['adobePassSignedRequestorId']
    signed_requestor_id = signed_requestor_id.replace('\n',"")
    print signed_requestor_id
    
    return signed_requestor_id

def SET_STREAM_QUALITY(url):
    if QUALITY == 0:
        q_lvl = "200000"
        q_lvl_golf = "296k"
    elif QUALITY == 1:
        q_lvl = "400000"
        q_lvl_golf = "496k"
    elif QUALITY == 2:
        q_lvl = "600000"
        q_lvl_golf = "796k"
    elif QUALITY == 3:
        q_lvl = "900000"
        q_lvl_golf = "1296k"
    elif QUALITY == 4:
        q_lvl = "1400000"
        q_lvl_golf = "1896k"
    elif QUALITY == 5:
        q_lvl = "2200000"
        q_lvl_golf = "2596k"
    else:
        q_lvl = "3450000"
        #q_lvl = "4296000"
        q_lvl_golf = "4296k"
    
    
    url = url.replace('master.m3u8',q_lvl_golf+'/prog.m3u8')       
    url = url.replace('manifest(format=m3u8-aapl-v3)','QualityLevels('+q_lvl+')/Manifest(video,format=m3u8-aapl-v3,audiotrack=audio_en_0)')       
    url = url.replace('manifest(format=m3u8-aapl,filtername=vodcut)','QualityLevels('+q_lvl+')/Manifest(video,format=m3u8-aapl,filtername=vodcut)')
    url = url.replace('manifest(format=m3u8-aapl-v3,filtername=vodcut)','QualityLevels('+q_lvl+')/Manifest(video,format=m3u8-aapl-v3,audiotrack=audio_en_0,filtername=vodcut)')


    return url

def SAVE_COOKIE(cj):
    # Cookielib patch for Year 2038 problem
    # Possibly wrap this in if to check if box is indeed 32bit
    for cookie in cj:
        # Jan, 1 2038
        if cookie.expires >= 2145916800:
            #Jan, 1 2037
            cookie.expires =  2114380800
    
    cj.save(ignore_discard=True);  


def CLEAR_SAVED_DATA():
    print "IN CLEAR"
    try:
        os.remove(ADDON_PATH_PROFILE+'/device.id')
    except:
        pass
    try:
        os.remove(ADDON_PATH_PROFILE+'/provider.info')
    except:
        pass
    try:
        os.remove(ADDON_PATH_PROFILE+'/cookies.lwp')
    except:
        pass
    try:
        os.remove(ADDON_PATH_PROFILE+'/auth.token')
    except:
        pass
    ADDON.setSetting(id='clear_data', value='false')   


"""
def SET_PROVIDER():
    provider = None
    if MSO_ID == 'Dish':
        provider = DISH()
    elif MSO_ID == 'TWC':
        provider = TWC()
    elif MSO_ID == 'Comcast_SSO':
        provider = COMCAST()

    return provider

def AUTHORIZE_STREAM(provider):    
    adobe = ADOBE()
    expired_cookies = True
    try:
        cj = cookielib.LWPCookieJar()
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        
        for cookie in cj:
            #print cookie.name
            #print cookie.expires
            #print cookie.is_expired()
            if cookie.name == 'BIGipServerAdobe_Pass_Prod':
                expired_cookies = cookie.is_expired()
    except:
        pass

    resource_id = GET_RESOURCE_ID()    
    signed_requestor_id = GET_SIGNED_REQUESTOR_ID() 
    auth_token_file = os.path.join(ADDON_PATH_PROFILE, 'auth.token')        
    
    last_provider = ''
    fname = os.path.join(ADDON_PATH_PROFILE, 'provider.info')
    if os.path.isfile(fname):                
        provider_file = open(fname,'r') 
        last_provider = provider_file.readline()
        provider_file.close()

    #If cookies are expired or auth token is not present run login or provider has changed
    if expired_cookies or not os.path.isfile(auth_token_file) or (last_provider != MSO_ID):
        #saml_request, relay_state, saml_submit_url = adobe.GET_IDP()            
        var_1, var_2, var_3 = provider.GET_IDP()            
        saml_response, relay_state = provider.LOGIN(var_1, var_2, var_3)
        adobe.POST_ASSERTION_CONSUMER_SERVICE(saml_response,relay_state)
        adobe.POST_SESSION_DEVICE(signed_requestor_id)    


    authz = adobe.POST_AUTHORIZE_DEVICE(resource_id,signed_requestor_id)        
    media_token = adobe.POST_SHORT_AUTHORIZED(signed_requestor_id,authz)
    stream_url = adobe.TV_SIGN(media_token,resource_id, stream_url)

    return stream_url
    """




# KODI ADDON GLOBALS
ADDON_HANDLE = int(sys.argv[1])
ROOTDIR = xbmcaddon.Addon(id='script.module.adobepass').getAddonInfo('path')
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_PATH = xbmc.translatePath(ADDON.getAddonInfo('path'))
ADDON_PATH_PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile'))
KODI_VERSION = float(re.findall(r'\d{2}\.\d{1}', xbmc.getInfoLabel("System.BuildVersion"))[0])
LOCAL_STRING = ADDON.getLocalizedString
FANART = ROOTDIR+"/fanart.jpg"
ICON = ROOTDIR+"/icon.png"

'''
MSO_ID = ''
if PROVIDER == '0':
    MSO_ID = 'auth_cableone_net'
elif PROVIDER == '1':    
    MSO_ID = 'Charter_Direct'  
elif PROVIDER == '2':    
    MSO_ID = 'Comcast_SSO'  
elif PROVIDER == '3':
    MSO_ID = 'Dish' 
elif PROVIDER == '4':
    MSO_ID = 'DTV'
elif PROVIDER == '5':
    MSO_ID = 'Cablevision'
elif PROVIDER == '6':
    MSO_ID = 'TWC'
elif PROVIDER == '7':
    MSO_ID = 'Verizon'
'''

#IDP_URL = 'https://sp.auth.adobe.com//adobe-services/1.0/authenticate/saml?domain_name=adobe.com&noflash=true&mso_id='+MSO_ID+'&requestor_id=nbcsports&no_iframe=true&client_type=iOS&client_version=1.9&redirect_url=http://adobepass.ios.app/'
ORIGIN = ''
REFERER = ''

USERNAME = ''
PASSWORD = ''
IDP_URL = ''

#User Agents
UA_IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Mobile/12H143'
UA_PC = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'
UA_ADOBE_PASS = 'AdobePassNativeClient/1.9 (iPhone; U; CPU iPhone OS 8.4 like Mac OS X; en-us)'



#Create Random Device ID and save it to a file
fname = os.path.join(ADDON_PATH_PROFILE, 'device.id')
if not os.path.isfile(fname):
    if not os.path.exists(ADDON_PATH_PROFILE):
        os.makedirs(ADDON_PATH_PROFILE)
    new_device_id = ''.join([random.choice('0123456789abcdef') for x in range(64)])
    device_file = open(fname,'w')   
    device_file.write(new_device_id)
    device_file.close()

fname = os.path.join(ADDON_PATH_PROFILE, 'device.id')
device_file = open(fname,'r') 
DEVICE_ID = device_file.readline()
device_file.close()

'''
#Create a file for storing Provider info
fname = os.path.join(ADDON_PATH_PROFILE, 'provider.info')
if os.path.isfile(fname):    
    provider_file = open(fname,'r')
    last_provider = provider_file.readline()
    provider_file.close()
    if MSO_ID != last_provider:
        CLEAR_SAVED_DATA()

provider_file = open(fname,'w')   
provider_file.write(MSO_ID)
provider_file.close()
'''

