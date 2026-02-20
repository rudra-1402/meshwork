import re

def is_empty(value):
    if value is None or not isinstance(value, str):
        return True
    return value.strip() == ""

def is_valid_email(email):
    if not isinstance(email, str):
        return False
    if len(email) > 254:
        return False
    pattern = r'^[a-zA-Z0-9][\w\.\-]*[a-zA-Z0-9]@[a-zA-Z0-9][\w\.\-]*[a-zA-Z0-9]\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None