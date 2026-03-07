import requests
from src.core.config import load_single_api_config
from src.core.schema import ApiRequest, SafetyStatus
from src.utils.logger import setup_tool_logger
from src.utils.access import  access_validator, load_access_policy

_amap_logger = setup_tool_logger("AMAP")
config = load_single_api_config("AMAP") 
access_policy = load_access_policy("AMAP")
tool_list = ["get_city_code"]



@access_validator
def get_city_code(city_name: str)-> str:
    base_url = config.base_url
    api_key = config.api_key
    url = f"{base_url}keywords={city_name}&region={city_name}&key={api_key}"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "1" and data.get("pois"):
            _amap_logger.info(f"[Tool][AMAP] AMAP API response: {data}")
            return data["pois"][0]["adacode"]
        else:
            _amap_logger.error(f"[Tool][AMAP] AMAP API error: {data.get('info')}")
        
    except requests.RequestException as e:
        _amap_logger.error(f"[Tool][AMAP] AMAP API request failed: {str(e)}")



