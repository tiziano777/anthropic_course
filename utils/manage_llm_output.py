from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic
from chat_template.chat_functions import chat,add_assistant_message,add_user_message,text_from_message

client = Anthropic()
model = "claude-sonnet-4-0"
messages = []


### Prefilled Assistant Messages
messages = []
add_user_message(messages, "Is tea or coffee better at breakfast?")
add_assistant_message(messages, "Coffee is better because")
answer = text_from_message(chat(model, client, messages))


### Stop Sequences

