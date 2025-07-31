from dotenv import load_dotenv
load_dotenv()

from chat_template.chat_functions import chat, add_assistant_message, add_user_message
import json

def generate_dataset(client, model, prompt, start_string : str, stop_string : str):
    messages = []
    add_user_message(messages, prompt)
    add_assistant_message(messages, start_string or "```json")
    text = chat(model, client, messages, stop_sequences= [stop_string] or ["```"])
    return json.loads(text)