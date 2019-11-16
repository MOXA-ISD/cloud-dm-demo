# -*- coding: utf-8 -*-
import time
import UtilityHelper
from azure.servicebus import ServiceBusService, Message, Queue

class ThingsProMessageBus:
    busService = None   

    def __init__(self, connectionString):
        self.connectionString = connectionString
        self.initServiceBus()
        return

    def initServiceBus(self):
        nameValue = UtilityHelper.connectStringToDictionary(self.connectionString)
        # 分拆 Connection String, 取各個值
        busNameSpace = UtilityHelper.getSubstring(nameValue['Endpoint'], '//', '.')
        ThingsProMessageBus.busService = ServiceBusService(
            service_namespace=busNameSpace,
            shared_access_key_name=nameValue['SharedAccessKeyName'],
            shared_access_key_value=nameValue['SharedAccessKey'])


    def sendMessageToQueue(self, queueName, message):
        try:
            queueMsg = Message(message)
            ThingsProMessageBus.busService.send_queue_message(queueName, queueMsg)
        except:
            raise

    # 收取訊息, Lock 它, 不刪除
    def readMessage(self, queueName):
        try:
            message = ThingsProMessageBus.busService.receive_queue_message(queueName, peek_lock=True)
            return message
        except:
            time.sleep(30)
            try:
                self.initServiceBus()
                ThingsProMessageBus.busService.readMessage(queueName)
                return b'Service Bus Connection Abord. Reconnected.'
            except:
                raise

    # 訊息處理完, 需要刪除
    # 訊息若沒主動刪除, Lock 時間 Timeout 後, 訊息會重新丟入 Message Queue
    def deleteMessage(self, message):
        try:
            message.delete()
        except:
            raise