from anthropic.types import Message

def extended_thinking_chat(model, client, messages, system : str = None, temperature : float = 1.0,  stop_sequences: dict = [], tools=None, thinking=False, thinking_budget=1024):
    
    params = {
        "model": model,
        "max_tokens": 4000,
        "messages": messages,
        "temperature": temperature,
        "stop_sequences": stop_sequences,
    }

    if thinking:
        params["thinking"] = {
            "type": "enabled",
            "budget_tokens": thinking_budget,
        }

    if tools:
        params["tools"] = tools

    if system:
        params["system"] = system

    message = client.messages.create(**params)
    return message
