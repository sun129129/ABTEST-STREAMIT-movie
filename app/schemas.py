from pydantic import BaseModel
from typing import Optional, Dict, List, Any

class ChooseRequest(BaseModel):
    user_id: str
    context: Optional[Dict[str, Any]] = None

class ChooseResponse(BaseModel):
    arm: str
    items: List[str]
    debug: Dict[str, Any]

class UpdateRequest(BaseModel):
    user_id: str
    arm: str
    reward: float
    meta: Optional[Dict[str, Any]] = None
