from uapi import UapiClient
from uapi.errors import UapiError
from src.core.config import load_single_api_config
from src.core.schema import ApiRequest
from src.utils.logger import setup_tool_logger
from src.utils.constant import StoragePaths
_uapi_logger = setup_tool_logger("UAPI")
config = load_single_api_config("UAPI")
client = UapiClient(config.base_url, token = config.api_key)


def get_weather(city:str, adcode: str) -> str:
    try:
        _uapi_logger.info(f"[Tool][Uapi][Weather] Fetching weather data for {city}")
        result = client.misc.get_misc_weather(city=city, adcode=adcode, extend=True, forecast = True, forecast = True)
        _uapi_logger.info(f"[Tool][Uapi][Weather] Weather data for {city}: {result}")
        return result
    except UapiError as e:
        _uapi_logger.error(f"[Tool][Uapi][Weather] UapiError: {str(e)}")
        return f"Error fetching weather data: {str(e)}"


def web_to_markdown(url: str, name: str) -> str:
    try: 
        _uapi_logger.info(f"[Tool][Uapi][WebToMarkdown] Converting {url} to markdown")
        result = client.webparse.post_web_tomarkdown_async(url=url)
        _uapi_logger.info(f"[Tool][Uapi][WebToMarkdown] Markdown content for {url}: {result}")
        result_path = StoragePaths.MARKDOWN_DIR / name
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(result)
        _uapi_logger.info(f"[Tool][Uapi][WebToMarkdown] Markdown saved to {result_path}")
        return result
    except UapiError as e:
        _uapi_logger.error(f"[Tool][Uapi][WebToMarkdown] UapiError: {str(e)}")
        return f"Error converting to markdown: {str(e)}"
