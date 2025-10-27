from langchain.schema import SystemMessage, HumanMessage, AIMessage

def serialize_message(message):
    if isinstance(message, SystemMessage):
        return {"role": "system", "content": message.content}
    elif isinstance(message, AIMessage):
        return {"role": "assistant", "content": message.content}
    elif isinstance(message, HumanMessage):
        return {"role": "user", "content": message.content}
    raise ValueError(f"Unsupported message type: {type(message)}")

def deserialize_message(data):
    role = data["role"]
    content = data["content"]
    if role == "system":
        return SystemMessage(content=content)
    elif role == "assistant":
        return AIMessage(content=content)
    elif role == "user":
        return HumanMessage(content=content)
    raise ValueError(f"Unsupported role: {role}")

def set_messages(messages):
    messages = [serialize_message(msg) for msg in messages]
    return messages

def get_messages(messages):
    messages = [deserialize_message(msg) for msg in messages]
    return messages
