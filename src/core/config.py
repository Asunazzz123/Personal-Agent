from dataclasses import dataclass
from decouple import config
from typing import Dict, Optional, Tuple

@dataclass(frozen=True)
class AppConfig:
    openai_api_key: Optional[str]
    openai_base_url: Optional[str]
    openai_model: str
    openai_vision_model: str
    openai_tts_model: str
    rag_embedding_model: str
    
def load_config() -> AppConfig:
    return AppConfig(
        openai_api_key=config("OPENAI_API_KEY", default=None),
        openai_base_url=config("OPENAI_BASE_URL", default=None),
        openai_model=config("OPENAI_MODEL"),
        openai_vision_model=config("OPENAI_VISION_MODEL"),
        openai_tts_model=config("OPENAI_TTS_MODEL"),
        rag_embedding_model=config("RAG_EMBEDDING_MODEL")
    )


@dataclass(frozen=True)
class SingleApiConfig:
    api_name: str
    base_url: Optional[str]
    api_key: Optional[str]


@dataclass(frozen=True)
class OutConfig:
    apis: Tuple[SingleApiConfig, ...]

    @property
    def api_list(self) -> Tuple[str, ...]:
        return tuple(api.api_name for api in self.apis)

    @property
    def api_key_list(self) -> Tuple[Dict[str, Optional[str]], ...]:
        return tuple({api.api_name: api.api_key} for api in self.apis)

    def get_api(self, api_name: str) -> Optional[SingleApiConfig]:
        for api in self.apis:
            if api.api_name == api_name:
                return api
        return None


def load_single_api_config(api_name: str) -> SingleApiConfig:
    api_key_prefix = api_name.upper()
    return SingleApiConfig(
        api_name=api_name,
        base_url=config(f"{api_key_prefix}_BASE_URL", default=None),
        api_key=config(f"{api_key_prefix}_API_KEY", default=None),
    )


def load_out_config(*api_names: str) -> OutConfig:
    return OutConfig(
        apis=tuple(load_single_api_config(name) for name in api_names),
    )


