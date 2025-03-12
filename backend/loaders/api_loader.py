import logging
import backoff
import requests
from requests.exceptions import RequestException
from datetime import datetime
from typing import Dict


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class TooManyRequestsException(Exception):
    """
    Raise when too many request sent to API
    """


class BearerAuthApi:

    def __init__(self, api_key, host):
        self.api_key = api_key
        self.host = host

    def create_header(self, extra_headers: Dict = None):
        header = {
            "Authorization": f"Bearer {self.api_key}"
        }
        if extra_headers:
            header.update(extra_headers)
        return header

    @backoff.on_exception(backoff.expo, (RequestException,
                                         TooManyRequestsException))
    def get(self, endpoint, params=None, extra_headers: Dict = None, **kwargs):
        url = self.host + endpoint
        r = requests.get(
            url=url,
            params=params,
            headers=self.create_header(extra_headers),
            **kwargs
        )
        if r.status_code == 429:
            raise TooManyRequestsException
        return r

    @backoff.on_exception(backoff.expo, (RequestException,
                                         TooManyRequestsException))
    def post(self, endpoint, data=None, extra_headers: Dict = None, **kwargs):
        url = self.host + endpoint
        r = requests.post(
            url=url,
            data=data,
            headers=self.create_header(extra_headers),
            **kwargs
        )
        if r.status_code == 429:
            raise TooManyRequestsException
        return r


class BasicAPIKeyAuth:

    def __init__(self, api_key, host):
        self.api_key = api_key
        self.host = host

    def create_header(self, extra_headers: Dict = None):
        header = {
            "Authorization": f"Basic {self.api_key}"
        }
        if extra_headers:
            header.update(extra_headers)
        return header

    @backoff.on_exception(backoff.expo, (RequestException,
                                         TooManyRequestsException))
    def get(self, endpoint, params=None, extra_headers: Dict = None, **kwargs):
        url = self.host + endpoint
        r = requests.get(
            url=url,
            params=params,
            headers=self.create_header(extra_headers),
            **kwargs
        )
        if r.status_code == 429:
            raise TooManyRequestsException
        return r

    @backoff.on_exception(backoff.expo, (RequestException,
                                         TooManyRequestsException))
    def post(self, endpoint, data=None, extra_headers: Dict = None, **kwargs):
        url = self.host + endpoint
        r = requests.post(
            url=url,
            data=data,
            headers=self.create_header(extra_headers),
            **kwargs
        )
        if r.status_code == 429:
            raise TooManyRequestsException
        return r


# # Example usage
# EXAMPLE_API_KEY = "your_api_key_here"
# EXAMPLE_API_HOST = "https://api.example.com"

# # Basic API key authentication
# api = BasicAPIKeyAuth(
#     api_key=EXAMPLE_API_KEY,
#     host=EXAMPLE_API_HOST
# )

# # OR

# # Bearer token authentication
# api = BearerAuthApi(
#     api_key=EXAMPLE_API_KEY,
#     host=EXAMPLE_API_HOST
# )

# NOTE: Consider to use secrets for storing API keys

# def get_request() -> dict:
#     """
#     Get data from the API.
#     :return: dict
#     """

#     response = api.get(
#         endpoint="/example/endpoint/v1/data",
#         params={
#             'param1': "value1",
#             'param2': "value2",
#             'param3': 1111,
#             'dimensions': 9999
#         },
#         extra_headers={"Content-Type": "application/json"}
#     )
#     if not response.ok:
#         logging.error(
#             f"There was an error with API endpoint ({response.status_code})."
#         )
#         logging.error(f"Response:\n {response.text}")
#         raise Exception(f"API Error: error code {response.status_code}")

#     return response.json()
