#!/usr/bin/python
# -*- coding: utf-8 -*-

import json, urllib2
import datetime,time

#  Copyright 2017 Maxime MADRAU

'''
This module allows to use Domoticz devices with simple Python commands
'''

DeviceTypeLight = 'light'
DeviceTypeWeather = 'weather'
DeviceTypeTemp = 'temp'
DeviceTypeUtility = 'utility'

url_opener = urllib2.build_opener()

class Device(object):
    def __init__(self,parent,dev):
        self.parent = self._parent = parent
        self.raw = dev;
        # self.idx = self._idx = int(dev['idx'])

    def __getattr__(self, key):
        return self.raw[key] if key in self.raw else ''

    def keys(self):
        reponse = jsonReponse(self._parent._url,'/json.htm?type=devices&rid=%i'%self.idx)['result'][0]
        return reponse.keys()

    def __repr__(self):
        return '<Domoticz Device %s: %s>' % (self.idx, self.Name)

    def on(self):
        return self.parent.apiRequest('/json.htm?type=command&param=switchlight&idx=%s&switchcmd=On'%self.idx)

    def off(self):
        return self.parent.apiRequest('/json.htm?type=command&param=switchlight&idx=%s&switchcmd=Off'%self.idx)

    def setLevel(self,level):
        return self.parent.apiRequest('/json.htm?type=command&param=switchlight&idx=%s&switchcmd=Set%%20Level&level=%s'%(self.idx,str(level)))

    def __call__(self,cmd):
        return self.parent.apiRequest('/json.htm?type=command&param=switchlight&idx=%s&switchcmd=%s'%(self.idx,cmd))

    def statusDesc(self):
        status = self.Data if self.Data else self.Status
        if self.SubType == 'Selector Switch':
            status = self.LevelNames.split('|')[self.LevelInt/10]
        return '%s: %s' % (self.Name, status)


class Domoticz(object):
    def __init__(self,ip,**kwargs):
        user = kwargs.get('user','')
        password = kwargs.get('password',None)
        fullUser = user if not password else user+':'+password
        isssl = kwargs.get('isssl', False)
        port = kwargs.get('port', 443 if isssl else 80)
        portstr = '' if ((isssl and port == 443) or (not isssl and port == 80)) else ':%d' % (port)
        self.user = user
        self.password = password
        self._fullUser = fullUser
        self.ip = ip
        self.port = port
        self.isssl = isssl
        self._url = 'http%s://%s%s%s%s'%('s' if isssl else '', fullUser, '@' if fullUser else '', ip, portstr)

    def apiRequest(self, path):
        url = self._url + path
        print 'request', url
        body = url_opener.open(url, timeout=10).read()
        response = json.loads(body)
        return response

    def updateServerStatus(self, response):
        now = datetime.datetime.now()
        self.status = response['status']
        self.title = response['title']
        self.ServerTime = datetime.datetime.strptime(response['ServerTime'],'%Y-%m-%d %H:%M:%S')
        self.sunrise = datetime.datetime(now.year,now.month,now.day,hour=int(response['Sunrise'].split(':')[0]),minute=int(response['Sunrise'].split(':')[1]),second=0)
        self.sunset = datetime.datetime(now.year,now.month,now.day,hour=int(response['Sunset'].split(':')[0]),minute=int(response['Sunset'].split(':')[1]),second=0)
        self.actTime = response['ActTime']
        self.startupTime = now - datetime.timedelta(seconds=self.actTime)

    def getDeviceByIdx(self, idx):
        response = self.apiRequest('/json.htm?type=devices&rid=%s' % idx)
        self.updateServerStatus(response)
        dev = Device(self, response['result'][0]) if len(response['result']) > 0 else None
        return dev

    def getDevicesByType(self, type='all', devFilter=None):
        ret = []
        if type == 'scenes':
            response = self.apiRequest('/json.htm?type=scenes')
        else:
            response = self.apiRequest('/json.htm?type=devices&used=true&filter=%s' % type)
        self.updateServerStatus(response)
        if devFilter is None:
            for dev in response['result']:
                ret.append(Device(self, dev))
        else:
            for dev in response['result']:
                d = Device(self, dev)
                if devFilter(d):
                    ret.append(d)
        return ret

    def __call__(**kwargs):
        str_ = ""
        for argument in kwargs:
            str_ += '&%s=%s'%argument
        return jsonReponse(self._url,str_)

    def __repr__(self):
        return '<Domoticz Server at "%s">'%self.ip



