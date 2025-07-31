def add_user_message(messages, text):
    user_message = {"role": "user", "content": text}
    messages.append(user_message)

def add_assistant_message(messages, text):
    assistant_message = {"role": "assistant", "content": text}
    messages.append(assistant_message)

def chat(model, client, messages, system : str = None, temperature : float = 1.0,  stop_sequences: dict = []):
    params = {
        "model": model,
        "max_tokens": 3156,
        "messages": messages,
        "temperature": temperature,
        "stop_sequences": stop_sequences
    }
    
    if system:
        params["system"] = system  # System prompt!
    if stop_sequences:
        params["stop_sequences"] = stop_sequences # Used for Formatted Output!
    
    message = client.messages.create(**params)
    return message.content[0].text
