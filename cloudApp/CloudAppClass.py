# -*- coding: utf-8 -*-
import AzureIoTHubHelper
import json, datetime


class ThingsProEdge:
    def __init__(self, connectionString, thingsproAgentId):        
        self.connectionString = connectionString 
        self.thingsproAgentId = thingsproAgentId

        self.azureIoTHub = AzureIoTHubHelper.DeviceOperation(self.connectionString)
        self.d2cMessagePolicy = json.loads('{"groups":[{"enable":true,"outputTopic":"sample","properties":[{"key":"messageType","value":"deviceMonitor"}],"tags":[{"srcName":"system","tagNames":["cpuUsage","memoryUsage"]}],"pollingInterval":5,"sendOutThreshold":{"size":4096,"time": 0}}]}')
        self.upgradeSoftwarePolicy = json.loads('{"downloadURL": "", "runInstallation": false}')
        self.universalDirectMethodPayload = json.loads('{"path":"", "method": "", "headers":[{"Content-Type":"application/json"}], "requestBody":""}')
        
    # List Azure IoT DeviceID, filter by IoT Edge capability
    def getThingsProEdgeList(self):
        edgeDeviceList = []
        try:
            status, content = self.azureIoTHub.getDevices()
            if (status == 200):
                deviceArray = json.loads(content)
                for device in deviceArray:
                    if (self.azureIoTHub.withEdgeCapability(device['deviceId'])):
                        edgeDeviceList.append(device)
            else:
                raise Exception('status:' + str(status))
        except:
            raise
        return edgeDeviceList
    
    def getReportedPropertiesJSON(self, deviceId):
        try:
            status, content = self.azureIoTHub.getModuleTwin(deviceId, self.thingsproAgentId)
            if (status == 200):
                deviceTwin = json.loads(content)
                if 'properties' in deviceTwin:
                    if 'reported' in deviceTwin['properties']:
                        return deviceTwin['properties']['reported']

            elif (status == 404):
                raise Exception('thingspro-agent not found')
            else: 
                raise Exception('status:' + str(status))
        except:
            raise
        return None
    
    def getDeviceInfoDict(self, deviceId):
        try:
            reportedProperties = self.getReportedPropertiesJSON(deviceId)
            deviceInfo = dict()
            if (reportedProperties != None):
                deviceInfo['hostName'] = reportedProperties['general']['hostName']
                deviceInfo['modelName'] = reportedProperties['general']['modelName']
                deviceInfo['firmwareVersion'] = reportedProperties['general']['firmwareVersion']
                deviceInfo['thingsproVersion'] = reportedProperties['general']['thingsproVersion']
                deviceInfo['wan'] = reportedProperties['wan']['displayName']
                deviceInfo['ip'] = reportedProperties['wan']['ip']

                status, content = self.azureIoTHub.getModules(deviceId)
                if (status == 200):
                    modules = json.loads(content)
                    for module in modules:
                        if (module['moduleId'] == '$edgeHub'):
                            deviceInfo['connectionState'] = module['connectionState']
                            break
                else:
                    deviceInfo['connectionState'] = 'Unknow'
            else:
                return None
        except:
            return None
        return deviceInfo
    
    def getThingsProEdgeConfiguration(self, deviceId):
        try:
            status, content = self.azureIoTHub.getModuleTwin(deviceId, self.thingsproAgentId)
            deviceConfig = dict()
            if (status == 200):
                deviceTwin = json.loads(content)
                if 'properties' in deviceTwin:
                    if 'reported' in deviceTwin['properties']:
                        deviceConfig['hostName'] = deviceTwin['properties']['reported']['general']['hostName']
                        deviceConfig['firmwareVersion'] = deviceTwin['properties']['reported']['general']['firmwareVersion']
                        deviceConfig['thingsproVersion'] = deviceTwin['properties']['reported']['general']['thingsproVersion']
                        deviceConfig['wan'] = deviceTwin['properties']['reported']['wan']['displayName']
                        deviceConfig['ip'] = deviceTwin['properties']['reported']['wan']['ip']
                        deviceConfig['description'] = deviceTwin['properties']['reported']['general']['description']
                        deviceConfig['deviceType'] = deviceTwin['properties']['reported']['general']['deviceType']
                        deviceConfig['modelName'] = deviceTwin['properties']['reported']['general']['modelName']
                        deviceConfig['serialNumber'] = deviceTwin['properties']['reported']['general']['serialNumber']
                        deviceConfig['ntpEnable'] = deviceTwin['properties']['reported']['time']['ntp']['enable']
                        deviceConfig['ntpServer'] = deviceTwin['properties']['reported']['time']['ntp']['server']
                        deviceConfig['ntpInterval'] = deviceTwin['properties']['reported']['time']['ntp']['interval']
                        deviceConfig['timeZone'] = deviceTwin['properties']['reported']['time']['timezone']                        
                        deviceConfig['lastUpdatedAt'] = deviceTwin['properties']['reported']['$metadata']['$lastUpdated'] 
                        desiredDate = deviceTwin['properties']['desired']['$metadata']['$lastUpdated']                        
                        reportedAt = datetime.datetime.strptime(deviceConfig['lastUpdatedAt'].split('.')[0], '%Y-%m-%dT%H:%M:%S')
                        try:
                            desiredAt = datetime.datetime.strptime(desiredDate.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                            if reportedAt >= desiredAt:
                                deviceConfig['status'] = 'Latest'
                            else:
                                deviceConfig['status'] = 'Waiting'                        
                            return deviceConfig     
                        except:
                            deviceConfig['status'] = 'Latest'
                            return deviceConfig
            else: 
                return None
        except:
            return None
        return None
    
    def updateThingsProEdgeConfiguration(self, deviceId, deviceConfig):
        desiredProperties = dict()
        try:
            if 'hostName' in deviceConfig:
                if 'general' not in desiredProperties:
                    desiredProperties['general'] = dict()                    
                desiredProperties['general']['hostName'] = deviceConfig['hostName']
            if 'description' in deviceConfig:
                if 'general' not in desiredProperties:
                    desiredProperties['general'] = dict()                    
                desiredProperties['general']['description'] = deviceConfig['description']
            if 'ntpEnable' in deviceConfig:
                if 'time' not in desiredProperties:
                    desiredProperties['time'] = dict()
                    desiredProperties['time']['ntp'] = dict()
                if (deviceConfig['ntpEnable'] == 'true'):
                    desiredProperties['time']['ntp']['enable'] = True
                else:
                    desiredProperties['time']['ntp']['enable'] = False
            if 'ntpInterval' in deviceConfig:
                if 'time' not in desiredProperties:
                    desiredProperties['time'] = dict()
                    desiredProperties['time']['ntp'] = dict()                  
                desiredProperties['time']['ntp']['interval'] = int(deviceConfig['ntpInterval'])
            if 'ntpServer' in deviceConfig:
                if 'time' not in desiredProperties:
                    desiredProperties['time'] = dict()
                    desiredProperties['time']['ntp'] = dict()                              
                desiredProperties['time']['ntp']['server'] = deviceConfig['ntpServer']
            if 'timeZone' in deviceConfig:
                if 'time' not in desiredProperties:
                    desiredProperties['time'] = dict()                                           
                desiredProperties['time']['timezone'] = deviceConfig['timeZone']

            status, content = self.azureIoTHub.updateModuleDesiredProperties(deviceId, self.thingsproAgentId, desiredProperties)            
            if (status == 200):
                return 'OK'
            elif (status == 404):
                return 'thingspro-agent not found'
            else: 
                return str(status)
        except Exception as exp:
            return str(exp)

    def rebootDevice(self, deviceId):
        try:
            status, content = self.azureIoTHub.callModuleDirectMethod(deviceId, self.thingsproAgentId, 'system-reboot', '{}')
            if (status == 200):
                return 'OK'
            elif (status == 404):
                return 'thingspro-agent not found or device was offline'
            else: 
                return str(status) 
        except Exception as exp:
            return str(exp)

    def upgradeSoftware(self, deviceId, softwareUpgrade):
        try:
            self.upgradeSoftwarePolicy['downloadURL'] = softwareUpgrade['downloadURL']
            self.upgradeSoftwarePolicy['runInstallation'] = softwareUpgrade['runInstallation']
            status, content = self.azureIoTHub.callModuleDirectMethod(deviceId, self.thingsproAgentId, 'thingspro-software-upgrade', self.upgradeSoftwarePolicy)
            if (status == 200):
                contentJson = json.loads(content)
                if (contentJson['status'] == 200):
                    return 'OK'
                else:
                    return 'Error'                
            elif (status == 404):
                return 'thingspro-agent not found or device was offline'
            else: 
                return str(status) 
        except Exception as exp:
            return str(exp)
       
    
    def monitorDevice(self, deviceId, turnOn):
        try:
            if turnOn:
                self.d2cMessagePolicy['groups'][0]['enable'] = True
            else:
                self.d2cMessagePolicy['groups'][0]['enable'] = False

            status, content = self.azureIoTHub.callModuleDirectMethod(deviceId, self.thingsproAgentId, 'message-policy-put', self.d2cMessagePolicy)
            if (status == 200):
                return 'OK'
            elif (status == 404):
                return 'thingspro-agent not found or device was offline'
            else: 
                return str(status) 
        except Exception as exp:
            return str(exp)


