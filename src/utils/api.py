import requests
from src.core.config import load_single_api_config
from src.core.schema import ApiRequest


class ApiClient:
    def __init__(self, api_name: str):
        api_config = load_single_api_config(api_name)
        self.api_name = api_name
        self.base_url = api_config.base_url
        self.api_key = api_config.api_key



