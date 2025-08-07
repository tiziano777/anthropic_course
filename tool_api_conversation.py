from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic
from chat_template.chat_functions import chat, add_user_message, add_assistant_message,text_from_message
from tools.datetime_tool import get_current_datetime_schema
from tools.batch_tool import batch_tool_schema
from tools.TextEditorTool import get_text_edit_schema
from tools.tool_use import run_tools
from tools.web_search_tool.web_tool import WebSearchTool

client = Anthropic()
model = "claude-sonnet-4-0"
web_search_tool = WebSearchTool()

messages = []
messages.append({
    "role": "user",
    "content": "What is the exact time, formatted as HH:MM:SS?"
})


def run_conversation(model, client, messages):
    
    while True:
        response =  chat(model,
                        client,
                        messages,
                        tools=[get_text_edit_schema(model),
                               web_search_tool.get_web_search_schema(model=model, user_location="Italy"),
                               get_current_datetime_schema,
                               batch_tool_schema,
                               ]
                    )
        add_assistant_message(messages, response)
        print(text_from_message(response))
        
        if response.stop_reason != "tool_use":
            break
            
        tool_results = run_tools(response)
        add_user_message(messages, tool_results)
    
    return messages


