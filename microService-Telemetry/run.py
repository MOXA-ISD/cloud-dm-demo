# -*- coding: utf-8 -*-
import UtilityHelper
import asyncio, requests, datetime, os, json
from azure.storage.blob import BlockBlobService

from azure.eventprocessorhost import (
    AbstractEventProcessor,
    AzureStorageCheckpointLeaseManager,
    EventHubConfig,
    EventProcessorHost,
    EPHOptions)

class EventProcessor(AbstractEventProcessor):
    def __init__(self, params=None):
        super().__init__(params)
        self.webAppURL = params[0]     
        self.rtMessageRoomId = params[1]

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
            if eventData.application_properties.get(b'messageType') == None:
                continue
                        
            messageType = eventData.application_properties.get(b'messageType').decode("utf-8")

            print(str(eventData.message))
            if messageType == "deviceMonitor":
                feedInMessage = dict()
                feedInMessage['roomId'] = self.rtMessageRoomId
                feedInMessage['data'] = dict()
                feedInMessage['data']['deviceId'] = eventData.device_id.decode("utf-8")  
                feedInMessage['data']['message'] = json.loads(str(eventData.message))
                await self.feedInMessage2SignalR(json.dumps(feedInMessage))
        
        await context.checkpoint_async()
        
    # Processor Host indicate error happen, it will try to continuing to pump message. No action is required.
    async def process_error_async(self, context, error):     
        print("Event Processor Error {!r}".format(error))

    # Feed in message to SignalR Web API
    async def feedInMessage2SignalR(self, data):
        headers = {
        'Content-Type': 'application/json',
        }
        url = self.webAppURL + 'api/v1/rtmessage'
        response = requests.post(url, headers=headers, params=None, json=json.loads(data))
        print(response.content.decode("utf-8"))


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

                self.storageContainer = config['azureResource']['StorageContainer']
                self.eventHubConnectionString = config['azureResource']['IoT-EventHubConnectionString']
                self.eventHubName = config['azureResource']['IoT-EventHubName']        
                self.consumerGroup = config['azureResource']['IoT-ConsumerGroup']
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
            endpointSuffix = UtilityHelper.getSubstring(nameValue['Endpoint'], '.', '/')
            user = nameValue['SharedAccessKeyName']
            key = nameValue['SharedAccessKey']
            ehConfig = EventHubConfig(nameSpace, self.eventHubName, user, key, 
                consumer_group=self.consumerGroup,
                namespace_suffix=endpointSuffix)
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
        ehOptions.max_batch_size = 120
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
        
        blobs = blobService.list_blobs(self.storageContainer)
        for blob in blobs:
            blobService.delete_blob(self.storageContainer, blob.name)
            print('delete blob : ' + blob.name)

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
                ep_params=[self.webAppURL,self.rtMessageRoomId],
                eph_options=ehOptions,
                loop=loop)

            # Below line was must for China Azure
            storageManager.storage_client = BlockBlobService(account_name=self.storageAccountName,
                                                      account_key=self.storageAccountKey,
                                                      endpoint_suffix=self.storageEndpointSuffix)

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

main = HotdataReceiverMain()
main.run()
