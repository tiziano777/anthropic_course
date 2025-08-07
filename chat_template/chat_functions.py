from anthropic.types import Message
from tools.datetime_tool import get_current_datetime_schema
from tools.batch_tool import batch_tool_schema
from tools.TextEditorTool import get_text_edit_schema
from tools.tool_use import run_tools

def add_user_message(messages, message):
    user_message = {
        "role": "user",
        "content": message.content if isinstance(message, Message) else message,
    }
    messages.append(user_message)

def add_assistant_message(messages, message):
    if isinstance(message, list):
        assistant_message = {
            "role": "assistant",
            "content": message,
        }
    elif hasattr(message, "content"):
        content_list = []
        for block in message.content:
            if block.type == "text":
                content_list.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                content_list.append(
                    {
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    }
                )
        assistant_message = {
            "role": "assistant",
            "content": content_list,
        }
    else:
        # String messages need to be wrapped in a list with text block
        assistant_message = {
            "role": "assistant",
            "content": [{"type": "text", "text": message}],
        }
    messages.append(assistant_message)

'''
tool_choice values: {"type":"auto"}, {"type":"any"}, {"type":"auto"}, {"type":"tool","name":"TOOL_NAME"}
'''

def chat(model, client, messages, system : str = None, temperature : float = 1.0,  stop_sequences: dict = [], tools=None, tool_choice: dict={"type":"auto"}, betas=None):
    params = {
        "model": model,
        "max_tokens": 3156,
        "messages": messages,
        "temperature": temperature,
        "stop_sequences": stop_sequences
    }
    
    if tool_choice:
        params["tool_choice"] = tool_choice
    if tools:
        params["tools"] = tools
    if system:
        params["system"] = system  # System prompt!
    if betas:
        params["betas"] = betas
    
    
    message = client.messages.create(**params)
    return message


'''
Extracting Text from Messages
Since you're now returning full message objects, create a helper to extract text when needed:
'''

def text_from_message(message):
    return "\n".join(
        [block.text for block in message.content if block.type == "text"]
    )
    

# Run the conversation in a loop until the model doesn't ask for a tool use
def run_conversation(model, client, messages):
    """
    This is not an interactive chat, is a single instruction with multiple itaration
    until the model stop to call tools, and we get in response the results as list of messages
    """
    while True:
        response = chat(
            model,
            client,
            messages,
            tools=[get_text_edit_schema(model), batch_tool_schema, get_current_datetime_schema],
        )

        add_assistant_message(messages, response)
        print(text_from_message(response))

        if response.stop_reason != "tool_use":
            break

        tool_results = run_tools(response)
        add_user_message(messages, tool_results)

    return messages
