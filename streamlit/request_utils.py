import requests
from requests.exceptions import RequestException

def get_request(url, params=None, headers=None):
    try:
        print(url)
        response = requests.get(url, params=params, headers=headers,  verify=False)
        print(response)
        response.raise_for_status()  # Check if the request was successful
        return response, None
    except RequestException as e:
        print(f'An error occurred: {e}')
        return None, e

def post_request(url, data=None, headers=None):
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Check if the request was successful
        return response, None
    except RequestException as e:
        print(f'An error occurred: {e}')
        return None, e
