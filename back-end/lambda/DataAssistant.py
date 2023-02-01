import boto3
import os
from boto3.dynamodb.types import TypeSerializer
from datetime import datetime
import uuid
import json
from chat import Chat
from ai import AI

now = datetime.utcnow()
dynamodb = boto3.client('dynamodb')
ts= TypeSerializer()
extracted_data_table_name = os.environ['EXTRACTED_DATA_TABLE_NAME']

class DataAssistant():
    def __init__(self, event):
        self.chat = Chat(event)
        self.ai = AI()
    
    def start_data_collection(self,data_collection_prompt):
        self.chat.increment_chat_index()
        self.chat.set_prompt(data_collection_prompt)

    def register_data_and_set_thank_you_message(self, user_message):
        prompt = f"{self.chat.chat_log}Human: {user_message}\nAI:EODC\nJSON:"
        json_fields = self.extract_json_fields(prompt)
        self.record_json_fields(json_fields)
        looking_for = "something"
        if "departure_location" in json_fields:
            looking_for = "flights"
        elif "restaurant_name" in json_fields:
            looking_for = "restaurants"
        thank_you_message = f"Got it! Thank you for your time, {json_fields['user_name']}. I'll be looking for {looking_for} and text you when I find some good options!"
        chat_log = f'{self.chat.chat_log}Human: {user_message}\nAI:EODC\nJSON:{json_fields}\nAI: {thank_you_message}\n'
        self.thank_you_message = thank_you_message
        self.chat.chat_log = chat_log
        self.chat.record_chat()
        
    def record_json_fields(self,json_fields):
        dynamodb.put_item(TableName=extracted_data_table_name,Item=ts.serialize(json_fields)['M'])

    def extract_json_fields(self,prompt):
        json_fields = self.ai.openai(prompt,tokens=800,temperature=0.2)
        json_fields = json_fields.split("}")[0]+"}"
        json_fields = json.loads(json_fields)
        json_fields["id"] = self.chat.user_number + "_" + str(uuid.uuid4())
        json_fields["createdAt"] = str(now)
        print("Cleaned JSON",json_fields)
        return json_fields
