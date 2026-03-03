import os
import base64
import json
import datetime
from dataclasses import dataclass
from typing import List
from openai import OpenAI
from src.core.config import AppConfig, load_config
from src.utils.logger import setup_logger

_llm_logger = setup_logger("LLM")

@dataclass
class LLMResult:
    content: str


class BaseLLMClient:

    def chat(self,messages: List[dict]) -> LLMResult:
        raise NotImplementedError
    
    def vision(
            self,
            prompt: str,
            image_paths: List[str],
            system_prompt: str = "",
    )-> LLMResult:
        raise NotImplementedError
    
    def tts(
            self,
            prompt: str,
            speed: int,
            voice: str,
            name:str,   
            output_dir: str,
            response_format: str = "mp3",
    )-> LLMResult:
        raise NotImplementedError
    
class OpenAILLMClient(BaseLLMClient):
    def __init__(self, client: OpenAI, config: AppConfig):
        self.client = client
        self.config = config
    def _response(self,mode:str, message: str) -> LLMResult:
        if mode == "chat":
            model = self.config.openai_model
        elif mode == "vision":
            model = self.config.openai_vision_model
        elif mode == "tts":
            model = self.config.openai_tts_model
        response = self.client.chat.completions.create(
            model = model,
            messages = message,
        )
        content = response.choices[0].message.content or ""
        return LLMResult(content=content)
    

    def chat(self,message: List[dict])-> LLMResult:
        _llm_logger.info("[Info][chat] model=%s", self.config.openai_model)
        _llm_logger.info("[Info][chat] message=%s", json.dumps(message, ensure_ascii=False))
        try:
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=message,
            )
            content = response.choices[0].message.content or ""
            _llm_logger.info("[Info][chat response=%s]", content)
            return LLMResult(content=content)
        except Exception as e:
            _llm_logger.error("[Error][chat] failed to process chat request: %s, message=%s", str(e), json.dumps(message, ensure_ascii=False))
            raise e
    def vision(
            self,
            prompt:str,
            image_paths: List[str],
            system_prompt:str=""
    )-> LLMResult:
        _llm_logger.info("[Info][vision] model=%s", self.config.openai_vision_model)
        _llm_logger.info("[Info][vision] prompt=%s", prompt, image_paths)
        image_blocks = []
        for path in image_paths:
            with open(path,"rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            image_blocks.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{b64}"
                    }
                }
            )
            messages: List[dict] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append(
                {
                    "role":"user",
                    "content":[
                        {"type":"text","text":prompt},
                        *image_blocks
                    ],
                }
            )
            try:
                response = self.client.chat.completions.create(
                    model=self.config.openai_vision_model,
                    messages=messages,
                )
                content = response.choices[0].message.content or ""
                _llm_logger.info("[Info][vision response=%s]", content)
                return LLMResult(content=content)
            except Exception as e:
                _llm_logger.error("[Error][vision] failed to process vision request: %s, messages=%s", str(e), json.dumps(messages, ensure_ascii=False))
                raise e
    def tts(
            self,
            prompt: str,
            speed: int,
            voice: str,
            response_format: str ,
            name:str,   
            output_dir: str,
    )-> LLMResult:
        _llm_logger.info("[Info][tts] model=%s, prompt=%s, speed=%s, voice=%s", self.config.openai_tts_model, prompt, speed, voice)
        response = self.client.audio.speech.create(
            model=self.config.openai_tts_model,
            input=prompt,
            speed=speed,
            voice=voice,
            response_format=response_format
        )
        output_file = os.path.join(output_dir, f"{name}.{response_format}")
        try:
            response.stream_to_file(output_file)
            _llm_logger.info("[Info][tts] audio saved to %s", output_file)
            return LLMResult(content=output_file)
        except Exception as e:
            _llm_logger.error("[Error][tts] failed to save audio: %s", str(e))
            raise e
def get_llm_client() -> BaseLLMClient:
    config = load_config()
    if not config.openai_api_key:
        _llm_logger.warning("[Warning] No OpenAI API key provided, please filled your API key!")
        raise ValueError("OpenAI API key is required to initialize LLM client.")
    client = OpenAI(
        api_key=config.openai_api_key,
        base_url=config.openai_base_url,
    )
    return OpenAILLMClient(client, config)