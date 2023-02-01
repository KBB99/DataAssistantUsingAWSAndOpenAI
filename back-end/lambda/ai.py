import requests
import json
import os 
import boto3

openai_api_key_ssm_parameter_name = os.environ['OPENAI_API_KEY_SSM_PARAMETER_NAME']

class AI():
    def __init__(self):
        self.openai_api_key = self.get_openai_api_key()
     
    def get_ai_response(self, prompt):
            openai_response = self.openai(prompt)
            split_openai_response = openai_response.split("Human:")
            if len(split_openai_response) > 1:
                print("AI is simulating human, cutting out AI's simulated response")
                openai_response = split_openai_response[0].strip()
            return openai_response

    def openai(self,prompt,tokens=30,temperature=1):
        headers = { "content-type": "application/json", 'Authorization': f'Bearer {self.openai_api_key}'}
        data = {"model": "text-davinci-003", "prompt": prompt, "temperature": temperature, "max_tokens": tokens}
        r = requests.post("https://api.openai.com/v1/completions", headers = headers, auth=None,  data=json.dumps(data))
        r = r.json()
        print(r)
        return r['choices'][0]['text'].strip()

    def get_openai_api_key(self):
        ssm = boto3.client('ssm')
        response = ssm.get_parameter(Name=openai_api_key_ssm_parameter_name)
        return response['Parameter']['Value']