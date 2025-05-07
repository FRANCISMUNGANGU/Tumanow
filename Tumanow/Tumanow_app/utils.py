import re
import requests
from requests.auth import HTTPBasicAuth

def normalize_phone(phone):
    """
    Normalize phone numbers to Safaricom format: 2547XXXXXXXX
    Accepts: +2547..., 07..., 2547..., 7...
    Returns: normalized phone number as string or None if invalid.
    """
    phone = phone.strip()

    # Remove any leading '+'
    if phone.startswith('+'):
        phone = phone[1:]

    # Convert 07... to 2547...
    if phone.startswith('07') and len(phone) == 10:
        phone = '254' + phone[1:]

    # Convert 7... to 2547...
    if phone.startswith('7') and len(phone) == 9:
        phone = '254' + phone

    # Final check: must be 12 digits and all numeric, start with 2547
    if re.fullmatch(r'2547\d{8}', phone):
        return phone
    return None


def get_access_token():
    from django.conf import settings  # Import settings from Django configuration
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    response = requests.get(url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        raise Exception(f"Failed to generate access token: {response.text}")
