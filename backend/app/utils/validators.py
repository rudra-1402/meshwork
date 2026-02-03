import re

def is_empty(value):
    return value is None or value.strip()==""

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None