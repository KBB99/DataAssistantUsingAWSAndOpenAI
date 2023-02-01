import boto3
import os
from boto3.dynamodb.types import TypeSerializer
from datetime import datetime, timedelta
import json

now = datetime.utcnow()
pinpoint = boto3.client('pinpoint')
dynamodb = boto3.client('dynamodb')
ts= TypeSerializer()

openai_api_key_ssm_parameter_name = os.environ['OPENAI_API_KEY_SSM_PARAMETER_NAME']
pinpoint_project_id = os.environ['PINPOINT_APPLICATION_ID']
chat_index_table_name = os.environ['CONVERSATION_INDEX_TABLE_NAME']
conversation_table_name = os.environ['CONVERSATION_TABLE_NAME']

class Chat():
    def __init__(self, event):
        self.set_user_number(event)
        self.set_bot_number(event)
        self.set_chat_index()
    
    def load_chat_log(self):
        self.chat_log = self.get_chat_log()

    def send_sms_without_specifying_bot_number(self, message):
        pinpoint = boto3.client('pinpoint')
        pinpoint.send_messages(
            ApplicationId=pinpoint_project_id,
            MessageRequest={
                    'Addresses': {
                        self.user_number: {'ChannelType': 'SMS'}
                    },
                    'MessageConfiguration': {
                        'SMSMessage': {
                            'Body': message,
                            'MessageType': 'TRANSACTIONAL'
                        }
                    }
                }
        )
    
    def send_sms(self, message):
        pinpoint = boto3.client('pinpoint')
        pinpoint.send_messages(
            ApplicationId=pinpoint_project_id,
            MessageRequest={
                    'Addresses': {
                        self.user_number: {'ChannelType': 'SMS'}
                    },
                    'MessageConfiguration': {
                        'SMSMessage': {
                            'Body': message,
                            'MessageType': 'TRANSACTIONAL',
                            'OriginationNumber': self.bot_number
                        }
                    }
                }
        )
    
    def send_welcome_sms_message(self, welcome_message):
        self.send_sms_without_specifying_bot_number(welcome_message)
        return
    
    def set_prompt(self, prompt):
        self.chat_log = prompt
        self.record_chat()

    def record_chat(self):
        conversation_id = f"{self.user_number}-{self.chat_index}"
        input = {
            'id':conversation_id,
            'chat_log': self.chat_log,
            'updated_at': str(now)
        }
        dynamodb.put_item(TableName=conversation_table_name, Item=ts.serialize(input)['M'])
    
    def get_chat_log(self):
        conversation_id = f"{self.user_number}-{self.chat_index}"
        chat = dynamodb.get_item(TableName=conversation_table_name, Key=ts.serialize({'id':conversation_id})['M'])
        if 'Item' in chat:
            return chat['Item']['chat_log']['S']
        return ''

    def get_chat_index(self):
        key = {'phone_number':self.user_number}
        chat_index = dynamodb.get_item(TableName=chat_index_table_name, Key=ts.serialize(key)['M'])
        if 'Item' in chat_index:
            return int(chat_index['Item']['chat_index']['N'])
        return 0

    def increment_chat_index(self):
        self.chat_index += 1
        input = {
            'phone_number': self.user_number,
            'chat_index': self.chat_index,
            'updated_at': str(now)
        }
        dynamodb.put_item(TableName=chat_index_table_name, Item=ts.serialize(input)['M'])

    def create_new_chat(self):
        self.increment_chat_index()
        self.chat_log = ''
        self.record_chat()

    def set_user_number(self,event):
        if is_http_request(event):
            body = json.loads(event['body'])
            self.user_number = body['phone_number']
        else:
            body = json.loads(event['Records'][0]['Sns']['Message'])
            self.user_number = body['originationNumber']

    def set_chat_index(self):
        self.chat_index = self.get_chat_index()

    def set_bot_number(self,event):
        if is_http_request(event):
            self.bot_number = None
        else:
            body = json.loads(event['Records'][0]['Sns']['Message'])
            self.bot_number = body['destinationNumber']

    def append_latest_interaction(self, user_message, openai_response):
        self.chat_log = f'{self.chat_log}Human: {user_message}\nAI: {openai_response}\n'

    def http_response(self, message):
        return {
            'statusCode': 200,
            'body': json.dumps(message),
            'headers': {
                "Access-Control-Allow-Origin" : "*", # Required for CORS support to work
                "Access-Control-Allow-Credentials" : True # Required for cookies, authorization headers with HTTPS
            },
        }

def is_http_request(event):
    return 'httpMethod' in event