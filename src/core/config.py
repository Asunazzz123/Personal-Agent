from dataclasses import dataclass
from decouple import config
from typing import Optional

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
class OutConfig:
    api_list: tuple[str, ...]
    api_key_list: tuple[dict[str, str], ...]


def load_out_config(*api_names: str) -> OutConfig:
    return OutConfig(
        api_list=tuple(api_names),
        api_key_list=tuple(
            {name: config(f"{name.upper()}_API_KEY")} for name in api_names
        ),
    )


