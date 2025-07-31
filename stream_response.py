from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic

client = Anthropic()
model = "claude-sonnet-4-0"
messages = []

with client.messages.stream(
    model=model,
    max_tokens=1000,
    messages=messages
) as stream:
    for text in stream.text_stream:
        # Send each chunk to your client
        print(text, end="")
    '''
    While streaming individual chunks is great for user experience,
    you often need the complete message for storage or further processing.
    After streaming completes, you can get the assembled final message:
    '''
    # Get the complete message for database storage
    final_message = stream.get_final_message()