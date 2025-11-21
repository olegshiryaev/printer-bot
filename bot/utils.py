import json

def encode_payload(prefix: str, data: dict) -> str:
    """
    Кодирование данных для callback_data.
    """
    return f"{prefix}:{json.dumps(data, ensure_ascii=False)}"


def decode_payload(raw: str) -> dict:
    """
    Декодирование данных из callback_data.
    """
    try:
        prefix, payload = raw.split(":", 1)
        return json.loads(payload)
    except Exception:
        return {}
