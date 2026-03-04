import requests
from datetime import datetime
from decouple import config
from src.core.config import load_single_api_config
from src.core.schema import ApiRequest
from src.utils.logger import setup_tool_logger
from src.utils.constant import StoragePaths

config = load_single_api_config("SERP")
_serp_logger = setup_tool_logger("SERP")

def finance(stock:str):
    base_url = config.base_url
    api_key = config.api_key
    path = StoragePaths.TEMP_DIR / "serp.json"
    url = f"{base_url}engine=google_finance&q=GOOGLE:{stock}"
    params = {
    "engine": "google_finance",
    "q": f"GOOGLE:{stock}",
    "api_key": api_key
    }
    _serp_logger.info(f"[Tool][SERP] Fetching finance data for stock: {stock}")
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        _serp_logger.info(f"[Tool][SERP] API response: {data}")
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(data))
        _serp_logger.info(f"[Tool][SERP] Finance data saved to {path}")
        return data
    except requests.RequestException as e:
        _serp_logger.error(f"[Tool][SERP] API request failed: {str(e)}")
        return f"Error fetching finance data: {str(e)}"
