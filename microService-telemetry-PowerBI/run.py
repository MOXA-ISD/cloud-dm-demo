# -*- coding: utf-8 -*-
from azure.storage.blob import BlockBlobService
import UtilityHelper 
import asyncio
import requests, datetime
import os, json, threading
import multiprocessing 

from azure.eventprocessorhost import (
    AbstractEventProcessor,
    AzureStorageCheckpointLeaseManager,
    EventHubConfig,
    EventProcessorHost,
    EPHOptions)

_httpRequest = requests.session()
_headers = {
        'Content-Type': 'application/json',
    }
def Send2PowerBI(jsonData):
    _httpRequest.post(jsonData['pushURL'], headers=_headers, params=None, json=jsonData)
    print('send:' + str(jsonData))

class PowerBIHelper:    
    _dataQueue = []

    def __init__(self):
            self.httpRequest = requests.session()
    def feedIn(self, jsonData):
        try:
            PowerBIHelper._dataQueue.append(jsonData)
        except Exception as ex:
            print(str(ex))

    def start(self):
        print('PowerBIHelper Instant started')
        threading.Thread(target=self.emit, daemon=True, args=()).start()
    
    def emit(self):
        while True:
            if (len(PowerBIHelper._dataQueue) > 0):
                postData = PowerBIHelper._dataQueue.pop(0)
                p = multiprocessing.Process(target=Send2PowerBI, args=(postData,))
                p.start() 
                print('PowerBI queue length:' + str(len(PowerBIHelper._dataQueue)))


class EventProcessor(AbstractEventProcessor):
    def __init__(self, params=None):
        super().__init__(params)

    # Initialize Event Processor Host
    async def open_async(self, context):
        print("Connection established {}".format(context.partition_id))

    # Processor Host indicate the event processor is being stopped.
    async def close_async(self, context, reason):      
        print("Connection closed (reason {}, id {}, offset {}, sq_number {})".format(
            reason,
            context.partition_id,
            context.offset,
            context.sequence_number))

    # Processor Host received a batch of events.
    # We retrieve Tenant Id from application properties
    # and, feed in message to Web API of SignalR
    async def process_events_async(self, context, messages):
        for eventData in messages:
            deviceId = eventData._annotations[b'iothub-connection-device-id'].decode("utf-8")
            try:
                pushURL = _deviceMap[deviceId]                
                messageJSON = json.loads(str(eventData.message))                
                _pushData[deviceId]['pushURL'] = pushURL
                _pushData[deviceId]['SourceTimestamp'] = messageJSON['timestamp']
                for tag in messageJSON['tags']:
                    if tag['Name'] == 'TEMP':
                        #pushData['TEMP'] = tag['Value'] * 1.8 + 32                            
                        _pushData[deviceId]['TEMP'] = tag['Value'] 
                    elif tag['Name'] == 'IRR':
                        _pushData[deviceId]['IRR'] = tag['Value']
                    elif tag['Name'] == 'INV':
                        _pushData[deviceId]['INV'] = tag['Value']
                powerBI.feedIn(_pushData[deviceId])
            except:
                print('Exception on handle deviceId: ' + deviceId)
        await context.checkpoint_async()
        
    # Processor Host indicate error happen, it will try to continuing to pump message. No action is required.
    async def process_error_async(self, context, error):     
        print("Event Processor Error {!r}".format(error))   

# Endless Loop
async def noneStop(host):
    while True:
        await asyncio.sleep(600)


class HotdataReceiverMain:    
    def __init__(self):
         # Load Configuration from file
        try:
            configFile = os.path.join(os.path.dirname((os.path.dirname(os.path.abspath(__file__)))), 'config.json')
            with open(configFile) as json_file:
                config = json.load(json_file)                
                nameValue = UtilityHelper.connectStringToDictionary(config['azureResource']['StorageAccountConnectionString'])
                self.storageAccountName = nameValue['AccountName']
                self.storageAccountKey = nameValue['AccountKey']
                self.storageEndpointSuffix = nameValue['EndpointSuffix']

                self.storageContainer = config['azureResource']['StorageContainerPowerBI']
                self.eventHubConnectionString = config['azureResource']['IoT-EventHubConnectionString']
                self.eventHubName = config['azureResource']['IoT-EventHubName']        
                self.consumerGroup = config['azureResource']['IoT-ConsumerGroupPowerBI']
                self.webAppURL = config['appSetting']['webAppURL']    
                if (not self.webAppURL.endswith('/')):
                    self.webAppURL = self.webAppURL + '/'  
                self.rtMessageRoomId = config['appSetting']['rtMessageRoomId']
        except:
            raise
        return

    # Event Hub Configuration
    def loadEventHubConfig(self):
        try:
            nameValue = UtilityHelper.connectStringToDictionary(self.eventHubConnectionString)
            nameSpace = UtilityHelper.getSubstring(nameValue['Endpoint'], '//', '.')
            user = nameValue['SharedAccessKeyName']
            key = nameValue['SharedAccessKey']
            ehConfig = EventHubConfig(nameSpace, self.eventHubName, user, key, consumer_group=self.consumerGroup)
        except:
            raise
        return ehConfig
    
    # CheckPoint Store Configuration
    def loadStorageManager(self):
        try:
            storageManager = AzureStorageCheckpointLeaseManager(
                storage_account_name=self.storageAccountName, 
                storage_account_key=self.storageAccountKey, 
                lease_container_name=self.storageContainer)
        except:
            raise
        return storageManager

    # Event Hub Optional Configuration
    def loadEventHostOptions(self):
        ehOptions = EPHOptions()
        ehOptions.max_batch_size = 10
        ehOptions.receive_timeout = 300
        ehOptions.keep_alive_interval = 290                     # We don't want receiver get timeout, so send a ping before it time out.
        ehOptions.release_pump_on_timeout = False
        ehOptions.initial_offset_provider = '@latest'           # Always get message from latest         
        ehOptions.debug_trace = False
        return ehOptions

    # Clear Storage Old Data
    def clearStorageOldData(self):
        blobService = BlockBlobService(
            account_name=self.storageAccountName,
            account_key=self.storageAccountKey,
            endpoint_suffix=self.storageEndpointSuffix
        )

        try:        
            blobs = blobService.list_blobs(self.storageContainer)
            for blob in blobs:
                blobService.delete_blob(self.storageContainer, blob.name)
                print('delete blob : ' + blob.name)
        except:
            print('blob was locked. Re-try after 30 seconds.')
            time.sleep(30)
            self.clearStorageOldData()

    def run(self):
        try:
            print('Loading EventHub Config...') 
            ehConfig = self.loadEventHubConfig()         

            print('Loading Storage Manager...')  
            storageManager = self.loadStorageManager()

            print('Clear Storage Old Data...')
            self.clearStorageOldData()

            print('Loading Event Host Options...')
            ehOptions = self.loadEventHostOptions()
        except Exception as ex:
            print('Exception on loading config. Error:' + str(ex))
            return

        try:
            # Event loop and host
            print('Start Event Processor Host Loop...')
            loop = asyncio.get_event_loop()
            host = EventProcessorHost(
                EventProcessor,
                ehConfig,
                storageManager,
                ep_params=["param1","param2"],
                eph_options=ehOptions,
                loop=loop)

            tasks = asyncio.gather(
                host.open_async(),
                noneStop(host))
            loop.run_until_complete(tasks)
        except Exception as ex:
            # Canceling pending tasks and stopping the loop
            print('Exception, leave loop. Error:' + str(ex))
            for task in asyncio.Task.all_tasks():
                task.cancel()
            loop.run_forever()
            tasks.exception()
        finally:
            loop.stop()


# 程式開始
# Load Device-> PushRUL Mapping
_deviceMap = dict()
_pushData = dict()
with open('deviceMapping.json') as json_file:
    deviceList = json.load(json_file)
    for device in deviceList:
        _deviceMap[device['deviceId']] = device['pushURL']
        deviceData = dict()
        deviceData['TEMP_Min'] = 50
        deviceData['TEMP_Max'] = 125
        deviceData['IRR_Min'] = 0
        deviceData['IRR_Max'] = 100
        deviceData['INV_Min'] = 0
        deviceData['INV_Max'] = 10
        _pushData[device['deviceId']] = deviceData

# Start Power BI Thread
powerBI = PowerBIHelper()
powerBI.start()

# Start Main Program Process
main = HotdataReceiverMain()
main.run()
