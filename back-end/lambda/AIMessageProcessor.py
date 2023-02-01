import json
from chat import Chat
from ai import AI
from DataAssistant import DataAssistant

book_flight_data_collection_prompt = """The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly. If the user wants they can talk about anything as soon as the assistant finishes collecting the following fields from the user:

The user's name
The user's departure location
The user's destination location
The user's dates of travel
The user's budget for the trip
Any additional preferences or constraints the user may have

After collecting all these fields the AI should thank the human for their time. It should then write EODC (for end of data collection) and on a new line output all these fields as JSON. {"user_name": "<user_name>", "departure_location": <departure_location>, "destination_location": "<destination_location>", "dates_of_travel": "<dates_of_travel>", "budget": <budget>, "additional_preferences": "<additional_preferences>"}
AI: Sure! I can help you book a flight. Can I start by getting your name?
"""
restaurant_suggestion_data_collection_prompt = """The following is a conversation with an AI assistant. The assistant is knowledgeable about local restaurants and can suggest options based on the user's preferences. The assistant needs to collect the following information from the user:
The user's name
The user's location
The user's preferred cuisine
The user's desired price range
Any dietary restrictions or allergies the user may have

After collecting all these fields the AI should thank the human for their time. It should then write EODC (for end of data collection) and on a new line output all these fields as JSON. {"user_name": "<user_name>", "location": "<location>", "cuisine": "<cuisine>", "price_range": "<price_range>", "dietary_restrictions": "<dietary_restrictions>"}
AI: Great! Let's find you a delicious meal. Can I start by getting your name?
"""
def lambda_handler(event, context):
    print(event)
    chat = Chat(event)
    if is_user_request_to_start_new_conversation(event):
        print("Starting a new conversation")
        chat.create_new_chat()
        response_message = 'Your previous conversation has been saved. You are now ready to begin a new conversation.'
        if is_http_request(event):
            return chat.http_response(response_message)
        else:
            chat.send_sms(response_message)
    elif is_request_to_book_flight(event):
        print("Starting a new conversation to book a flight")
        data_assistant = DataAssistant(event)
        data_assistant.start_data_collection(book_flight_data_collection_prompt)
        welcome_message = 'Sure! I can help you book a flight. Can I start by getting your name?'
        if is_http_request(event):
            return chat.http_response(welcome_message)
        else:
            chat.send_welcome_sms_message(welcome_message)
    elif is_request_to_find_restaurant(event):
        print("Starting a new conversation to find a restaurant")
        data_assistant = DataAssistant(event)
        data_assistant.start_data_collection(restaurant_suggestion_data_collection_prompt)
        welcome_message = 'Sure! I can help you find a restaurant. Can I start by getting your name?'
        if is_http_request(event):
            return chat.http_response(welcome_message)
        else:
            chat.send_welcome_sms_message(welcome_message)
    else:
        print("Continue an existing conversation")
        chat.load_chat_log()
        user_message = get_user_message(event)
        ai = AI()
        prompt = f"{chat.chat_log}Human: {user_message}\nAI:"
        ai_response = ai.get_ai_response(prompt)
        if all_data_fields_collected(ai_response):
            data_assistant = DataAssistant(event)
            data_assistant.chat = chat
            data_assistant.register_data_and_set_thank_you_message(user_message)
            message = data_assistant.thank_you_message
        else:
            chat.append_latest_interaction(user_message, ai_response)
            chat.record_chat()
            message = ai_response
        if is_http_request(event):
            return chat.http_response(message)
        else:
            chat.send_sms(message)

def all_data_fields_collected(openai_response):
    temp_openai_response = openai_response.split("EODC")
    json_split_temp_openai_response = openai_response.split("JSON")
    return len(temp_openai_response) > 1 or len(json_split_temp_openai_response) > 1

def is_http_request(event):
    return 'httpMethod' in event

def is_user_request_to_start_new_conversation(event):
    user_message = get_user_message(event)
    return "start a new conversation" in user_message.strip().lower()

def is_request_to_book_flight(event):
    user_message = get_user_message(event)
    return "book a flight" in user_message.strip().lower()

def is_request_to_find_restaurant(event):
    user_message = get_user_message(event)
    return "find a restaurant" in user_message.strip().lower()

def get_user_message(event):
    body = load_body(event)
    return body['messageBody']

def load_body(event):
    if is_http_request(event):
        body = json.loads(event['body'])
    else:
        body = json.loads(event['Records'][0]['Sns']['Message'])
    return body