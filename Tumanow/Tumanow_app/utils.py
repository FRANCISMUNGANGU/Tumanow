import re

def clean_input(value: str) -> str:
    return value.strip() if value else ''

def is_valid_email(email: str) -> bool:
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(email_regex, email) is not None

def validate_profile_pic(file):
    return file and file.content_type.startswith('image/')

def validate_signup_data(data):
    print(data)
    required_fields = ['name', 'username', 'email', 'phone_number', 'password', 'confirm_password', 'profile_pic']
    for field in required_fields:
        if not data.get(field):
            return False, "All fields are required."

    if not is_valid_email(data['email']):
        return False, "Invalid email format."

    if data['password'] != data['confirm_password']:
        return False, "Passwords do not match."

    if len(data['password']) < 8:
        return False, "Password must be at least 8 characters long."

    if not validate_profile_pic(data['profile_pic']):
        return False, "Profile picture must be an image."

    return True, ""
