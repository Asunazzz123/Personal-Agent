from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

def _dump(model:BaseModel) -> Dict[str, Any]:
    if hasattr(model,"model_dump"):
        return model.model_dump(mode="json")
    return model.dict()


class AgentRequest(BaseModel):
    task_id: str
    target_agent: str
    action: str
    
    def to_dict(self) -> Dict[str, Any]:
        return _dump(self)
    
class TraceStep(BaseModel):
    step_id: int
    


class ApiRequest(BaseModel):
    request_url: str
    api: str
    params: Dict[str, Any]


class SafetyStatus(BaseModel):
    tool_name: str
    access_policy: str = "Denied" or "Once" or "Whitelist" or "Onced"
