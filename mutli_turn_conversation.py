from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic
from chat_template.chat_functions import chat,add_assistant_message,add_user_message


client = Anthropic()
model = "claude-sonnet-4-0"

# Start with an empty message list
messages = []

# Add the initial user question
add_user_message(messages, "Define quantum computing in one sentence")

# Get Claude's response
answer = chat(model, client, messages)

# Add Claude's response to the conversation history
add_assistant_message(messages, answer)

# Add a follow-up question
add_user_message(messages, "Write another sentence")

# Get the follow-up response with full context
final_answer = chat(messages)
