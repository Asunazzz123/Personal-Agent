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

