# -*- coding: utf-8 -*-
from MessageBusHelper import ThingsProMessageBus
from datetime import datetime
import json, os, requests, time

class programMain:
    def __init__(self):
        # Load Configuration from file
        try:
            configFile = os.path.join(os.path.dirname((os.path.dirname(os.path.abspath(__file__)))), 'config.json')
            with open(configFile) as json_file:
                config = json.load(json_file)
                self.serviceBusConnectionString = config['azureResource']['ServiceBusConnectionString']
                self.serviceBusQueueName = config['azureResource']['ServiceBusQueueName']
                self.webAppURL = config['appSetting']['webAppURL']
                if (not self.webAppURL.endswith('/')):
                    self.webAppURL = self.webAppURL + '/'
                self.thingsProAgentName = config['appSetting']['thingsproAgentName']        
                self.rtMessageRoomId = config['appSetting']['rtMessageRoomId']
        except:
            raise

    def feedInMessage2RTMessage(self, data):
        headers = {
            'Content-Type': 'application/json',
        }
        url = self.webAppURL + 'api/v1/rtmessage'
        response = requests.post(url, headers=headers, params=None, json=json.loads(data))
        print(response.content.decode("utf-8"))

    # Feed in message to rtMessage Web API
    def notifyEdgeConnectionChange(self, deviceId, status):
        feedInMessage = dict()
        feedInMessage['roomId'] = self.rtMessageRoomId
        feedInMessage['data'] = dict()
        feedInMessage['data']['deviceId'] = deviceId
        if status == 'Connected':   
            feedInMessage['data']['connectionStatus'] = 'Connected'
        elif status == 'unknown':
            feedInMessage['data']['connectionStatus'] = 'Disconnected'
        elif status == 'backoff':
            feedInMessage['data']['connectionStatus'] = 'Disconnected'
        else:
            feedInMessage['data']['connectionStatus'] = 'Disconnected'

        print('Notify:' + feedInMessage['data']['connectionStatus'])
        self.feedInMessage2RTMessage(json.dumps(feedInMessage))   

    def notifyReportedPropertiesChange(self, deviceId, properties):
        feedInMessage = dict()
        feedInMessage['roomId'] = self.rtMessageRoomId
        feedInMessage['data'] = dict()
        feedInMessage['data']['deviceId'] = deviceId
        feedInMessage['data']['reportedProperties'] = properties
        print('Notify:' + str(feedInMessage['data']['reportedProperties']))
        self.feedInMessage2RTMessage(json.dumps(feedInMessage))   


    # 無限迴圈讀取 Azure Message Bus 送來的訊息. 訊息格式或內容若不正確, 不予處理, 直接刪除.
    # Input: 從 Service Bus 接收訊息
    # Ouput: 無
    def run(self):
        msgQueue = ThingsProMessageBus(self.serviceBusConnectionString, self.serviceBusQueueName)
        while True:
            try:
                print("Waiting message ...")
                messages = msgQueue.readMessage()                
                if messages == None:
                    #print('Get an empty message, pass it.')
                    continue
                
            except Exception as ex:
                time.sleep(30)
                continue
            
            for message in messages:
                try:
                    message.user_properties = { y.decode('ascii'): message.user_properties.get(y).decode('ascii') for y in message.user_properties.keys() } 
                                                  
                    deviceId = message.user_properties.get('deviceId')
                    moduleId = message.user_properties.get('moduleId')
                    print("Received Message, DeviceID: " + deviceId + ", ModuleID: " + moduleId)

                    thingsproAgentFullId = deviceId + '/' + self.thingsProAgentName
                    print(str(message))
                    messageJSON = json.loads(str(message))

                    # Rule1: thingspro-agent send reported properties, which means Edge is online
                    if moduleId == self.thingsProAgentName:
                        if 'reported' in messageJSON['properties']:
                            self.notifyEdgeConnectionChange(deviceId, 'Connected')
                            self.notifyReportedPropertiesChange(deviceId, messageJSON['properties']['reported'])
                        msgQueue.deleteMessage(message)
                        continue

                    # Rule2: edgeHub send reported properties, and indicate thingspro-agent's status, such as unknow, backoff
                    if 'clients' in messageJSON['properties']['reported']:
                        if thingsproAgentFullId in messageJSON['properties']['reported']['clients']:
                            self.notifyEdgeConnectionChange(deviceId, messageJSON['properties']['reported']['clients'][thingsproAgentFullId]['status'])
                    # Rule3: edgeHub send reported properties, and indicate thingspro-agent's status, such as Connected
                    elif 'modules' in messageJSON['properties']['reported']:
                        if self.thingsProAgentName in messageJSON['properties']['reported']['modules']:
                            self.notifyEdgeConnectionChange(deviceId, messageJSON['properties']['reported']['modules'][_thingsProAgentName]['runtimeStatus'])                
                    else:
                        print("Skip message")

                    msgQueue.deleteMessage(message)
                except Exception as ex:
                    msgQueue.deleteMessage(message)
                    print('Exception: ' + str(ex) + '; message delete')
                    continue           

# 程式開始
main = programMain()
main.run()
