from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic
from chat_template.chat_functions import chat, add_user_message, add_assistant_message,text_from_message
from tools.datetime_tool import get_current_datetime_schema

client = Anthropic()
model = "claude-sonnet-4-0"

messages = []
messages.append({
    "role": "user",
    "content": "What is the exact time, formatted as HH:MM:SS?"
})

response = client.messages.create(
    model=model,
    max_tokens=2000,
    messages=messages,
    tools=[get_current_datetime_schema],
)
