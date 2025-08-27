from chat_template import chat, add_user_message, text_from_message

# Add context to a single chunk
def add_context(text_chunk, source_text):
    prompt = f"""
    Write a short and succinct snippet of text to situate this chunk within the 
    overall source document for the purposes of improving search retrieval of the chunk. 

    Here is the original source document:
    <document> 
    {source_text}
    </document> 

    Here is the chunk we want to situate within the whole document:
    <chunk> 
    {text_chunk}
    </chunk>
    
    Answer only with the succinct context and nothing else. 
    """

    messages = []

    add_user_message(messages, prompt)
    result = chat(messages)

    # Note: updated to use 'text_from_message' helper fn
    return text_from_message(result) + "\n" + text_chunk