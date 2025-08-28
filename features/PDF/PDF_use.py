from chat_template.chat_functions import add_user_message, chat
import base64

file_name = "file.pdf"

with open(file_name , "rb") as f:
    file_bytes = base64.standard_b64encode(f.read()).decode("utf-8")

prompt = "Summarize the document in one sentence"
messages = []

add_user_message(
    messages,
    [
        {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": file_bytes,
            },
            "title": file_name,
            "citations": { "enabled": True } # false to disable citations
        },
        {"type": "text", "text": prompt },
        
    ],
)

chat(messages)