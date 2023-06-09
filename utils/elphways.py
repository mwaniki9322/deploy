import requests
from django.conf import settings


def get_elphways_access_token():
    url = "https://www.elphways.com/api/token/"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "api_key": settings.ELPHWAYS_API_KEY
    }

    try:
        response = requests.post(url=url, json=payload, headers=headers)
        response.raise_for_status()

        r = response.json()

        return r

    except requests.exceptions.HTTPError as err:
        return None


def send_sms(msg, phone_numbers):
    access_token = get_elphways_access_token()

    if not access_token:
        # There was an error with access token
        return None

    url = "https://www.elphways.com/api/bulk-sms/send-sms/"
    headers = {
        "Authorization": "Bearer {}".format(access_token['access']),
        "Content-Type": "application/json"
    }

    payload = {
        "message": msg,
        "phone_numbers": phone_numbers,
        "sender_id": settings.ELPHWAYS_SENDER_ID
    }

    try:
        response = requests.post(url=url, json=payload, headers=headers)
        response.raise_for_status()

        r = response.json()

        return {'sent': True, 'response': r}

    except requests.exceptions.HTTPError as err:
        return {'sent': False, 'err': err}
