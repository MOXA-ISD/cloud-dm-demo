# -*- coding: utf-8 -*-
import AzureIoTHubHelper
import CloudAppClass
import json

_iotHubConnectionString = 'HostName=thingsproEdge.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=Geq9NJs0z0GkZVqDgm3PBnpoQu/1RZkaYuA63uRf7jc='

#azureIoTHub = AzureIoTHubHelper.DeviceOperation(_iotHubConnectionString)
#status, content = azureIoTHub.getDevices()
#status, content = azureIoTHub.getDevice('Edge001')
#status, content = azureIoTHub.getModules('Edge001')
#status, content = azureIoTHub.getModuleTwin('kevinEdge1008', 'thingspro-agent')
#jsonObj = json.loads(content)
#lastUpdateTime = jsonObj['properties']['reported']['lastUpdateTime']
#desiredTime = jsonObj['properties']['desired']['$metadata']['$lastUpdated']
#content = azureIoTHub.withEdgeCapability('Edge001')

_cloudApp = CloudAppClass.ThingsProEdge(_iotHubConnectionString)
#deviceConfig = _cloudApp.getThingsProEdgeConfiguration('kevinEdge1008')
#if (deviceConfig != None):
#    deviceConfig['deviceId'] = 'kevinEdge1008'
#print(json.dumps(deviceConfig))

_deviceList = _cloudApp.getThingsProEdgeList()
for device in _deviceList:
    try:
        deviceInfo = _cloudApp.getDeviceInfoDict(device['deviceId'])
        print(deviceInfo)
        deviceConfig = _cloudApp.getThingsProEdgeConfiguration(device['deviceId'])
        print(deviceConfig)
    except Exception as exp:
        print(str(exp))







