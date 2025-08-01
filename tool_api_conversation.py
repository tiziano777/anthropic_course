from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic
from chat_template.chat_functions import chat, add_user_message, add_assistant_message,text_from_message
from tools.datetime_tool import get_current_datetime_schema
from tools.batch_tool import batch_tool_schema
from tools.tool_use import run_tools

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
    tools=[get_current_datetime_schema, batch_tool_schema],
)


def run_conversation(messages):
    while True:
        response = chat(messages, tools=[get_current_datetime_schema])
        add_assistant_message(messages, response)
        print(text_from_message(response))
        
        if response.stop_reason != "tool_use":
            break
            
        tool_results = run_tools(response)
        add_user_message(messages, tool_results)
    
    return messages


