import json
from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic
from chat_template.chat_functions import chat,add_assistant_message,add_user_message,text_from_message

client = Anthropic()
model = "claude-sonnet-4-0"
messages = []

add_user_message(messages, "Generate a very short dummy person info in json")
add_assistant_message(messages, "```json") # or (```bash) or (```python)

text = text_from_message(chat(model, client, messages, stop_sequences=["```"]))


# Clean up and parse the JSON
clean_json = json.loads(text.strip())