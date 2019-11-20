# -*- coding: utf-8 -*-
import time
import UtilityHelper
from azure.servicebus import ServiceBusClient, Message

class ThingsProMessageBus:
    def __init__(self, connectionString, queueName):
        self.sb_client = ServiceBusClient.from_connection_string(connectionString)
        self.queue_client = self.sb_client.get_queue(queueName)
        return

    def sendMessageToQueue(self, message):
        try:
            queueMsg = Message(message)
            self.queue_client.send(queueMsg)
        except:
            raise

    # 收取訊息, Lock 它, 不刪除
    def readMessage(self):
        try:
            messages = self.queue_client.get_receiver()
            return messages
        except:
            time.sleep(30)
            try:
                self.readMessage()
                return b'Service Bus Connection Abord. Reconnected.'
            except:
                raise

    # 訊息處理完, 需要刪除
    # 訊息若沒主動刪除, Lock 時間 Timeout 後, 訊息會重新丟入 Message Queue
    def deleteMessage(self, message):
        try:
            message.complete()
        except:
            raise