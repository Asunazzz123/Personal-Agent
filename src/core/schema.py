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
    