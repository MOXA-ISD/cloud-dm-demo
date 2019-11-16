import base64
import hmac
import hashlib
import time
import requests
import urllib
import json

class DeviceOperation:
    
    API_VERSION = '2019-07-01-preview'
    TOKEN_VALID_SECS = 365 * 24 * 60 * 60
    TOKEN_FORMAT = 'SharedAccessSignature sr=%s&sig=%s&se=%s&skn=%s'
    
    def __init__(self, connectionString=None):
        if connectionString != None:
            iotHost, keyName, keyValue = [sub[sub.index('=') + 1:] for sub in connectionString.split(";")]
            self.iotHost = iotHost
            self.keyName = keyName
            self.keyValue = keyValue
    
    def _buildExpiryOn(self):
        return '%d' % (time.time() + self.TOKEN_VALID_SECS)
    
    def _buildSasToken(self):
        targetUri = self.iotHost.lower()
        expiryTime = self._buildExpiryOn()
        toSign = '%s\n%s' % (targetUri, expiryTime)
        key = base64.b64decode(self.keyValue.encode('utf-8'))
        signature = urllib.parse.quote(
            base64.b64encode(
                hmac.HMAC(key, toSign.encode('utf-8'), hashlib.sha256).digest()
                )
        ).replace('/', '%2F')
        return self.TOKEN_FORMAT % (targetUri, signature, expiryTime, self.keyName)
    
    def createDeviceId(self, deviceId, enable=True):
        sasToken = self._buildSasToken()
        url = 'https://%s/devices/%s?api-version=%s' % (self.iotHost, deviceId, self.API_VERSION)
        status = "enabled" if enable == True else "disabled"
        body = '{deviceId: "%s", status: "%s"}' % (deviceId, status)
        r = requests.put(url, headers={'Content-Type': 'application/json', 'Authorization': sasToken}, data=body)
        return r.status_code, r.text
    
    def getDevice(self, deviceId):
        sasToken = self._buildSasToken()
        url = 'https://%s/devices/%s?api-version=%s' % (self.iotHost, deviceId, self.API_VERSION)
        r = requests.get(url, headers={'Content-Type': 'application/json', 'Authorization': sasToken})
        return r.status_code, r.text
    
    def getDevices(self, top=None):
        if top == None:
            top = 1000
        sasToken = self._buildSasToken()
        url = 'https://%s/devices?top=%d&api-version=%s' % (self.iotHost, top, self.API_VERSION)
        r = requests.get(url, headers={'Content-Type': 'application/json', 'Authorization': sasToken})
        return r.status_code, r.text

    def deleteDevice(self, deviceId):
        sasToken = self._buildSasToken()
        url = 'https://%s/devices/%s?api-version=%s' % (self.iotHost, deviceId, self.API_VERSION)
        r = requests.delete(url, headers={'Content-Type': 'application/json', 'Authorization': sasToken, 'If-Match': '*' }) 
        # If-Match Etag, but if * is used, no need to precise the Etag of the device. The Etag of the device can be seen in the header requests.text response 
        return r.status_code, r.text
    
    def callDirectMethod(self, deviceId, methodName, inputsPara):
        sasToken = self._buildSasToken()
        url = 'https://%s/twins/%s/methods?api-version=%s' % (self.iotHost, deviceId, self.API_VERSION)
        postData = dict()
        postData['methodName'] = methodName
        postData['connectTimeoutInSeconds'] = 30
        postData['responseTimeoutInSeconds'] = 60
        postData['payload'] = inputsPara
        body = json.dumps(postData)
        r = requests.post(url, headers={'Content-Type': 'application/json', 'Authorization': sasToken}, data=body)
        return r.status_code, r.text

    def callModuleDirectMethod(self, deviceId, moduleId, methodName, inputsPara):
        sasToken = self._buildSasToken()
        url = 'https://%s/twins/%s/modules/%s/methods?api-version=%s' % (self.iotHost, deviceId, moduleId, self.API_VERSION)
        postData = dict()
        postData['methodName'] = methodName
        postData['connectTimeoutInSeconds'] = 30
        postData['responseTimeoutInSeconds'] = 60
        postData['payload'] = inputsPara
        body = json.dumps(postData)
        r = requests.post(url, headers={'Content-Type': 'application/json', 'Authorization': sasToken}, data=body)
        return r.status_code, r.text
    
    def updateDesiredProperties(self, deviceId, desiredProperties):
        sasToken = self._buildSasToken()
        url = 'https://%s/twins/%s?api-version=%s' % (self.iotHost, deviceId, self.API_VERSION)
        postData = dict()
        TwinProperties = dict()
        TwinProperties['desired'] = desiredProperties
        postData['properties'] = TwinProperties
        body = json.dumps(postData)
        r = requests.patch(url, headers={'Content-Type': 'application/json', 'Authorization': sasToken}, data=body)
        return r.status_code, r.text

    def getModules(self, deviceId):
        sasToken = self._buildSasToken()
        url = 'https://%s/devices/%s/modules?api-version=%s' % (self.iotHost, deviceId, self.API_VERSION)
        r = requests.get(url, headers={'Content-Type': 'application/json', 'Authorization': sasToken})
        return r.status_code, r.text

    def getModuleTwin(self, deviceId, moduleId):
        sasToken = self._buildSasToken()
        url = 'https://%s/twins/%s/modules/%s?api-version=%s' % (self.iotHost, deviceId, moduleId, self.API_VERSION)
        r = requests.get(url, headers={'Content-Type': 'application/json', 'Authorization': sasToken})
        return r.status_code, r.text

    def updateModuleDesiredProperties(self, deviceId, moduleId, desiredProperties):
        sasToken = self._buildSasToken()
        url = 'https://%s/twins/%s/modules/%s?api-version=%s' % (self.iotHost, deviceId, moduleId, self.API_VERSION)
        postData = dict()
        TwinProperties = dict()
        TwinProperties['desired'] = desiredProperties
        postData['properties'] = TwinProperties
        body = json.dumps(postData)
        r = requests.patch(url, headers={'Content-Type': 'application/json', 'Authorization': sasToken}, data=body)
        return r.status_code, r.text 

    def withEdgeCapability(self, deviceId):
        status, content = self.getDevice(deviceId)
        if status != 200:
            return False

        deviceJSON = json.loads(content)
        if 'capabilities' not in deviceJSON:
            return False

        return deviceJSON['capabilities']['iotEdge']