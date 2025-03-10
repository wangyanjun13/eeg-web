from pydantic import BaseModel
from typing import Optional, Any

class APIResponse(BaseModel):
    """统一API响应格式"""
    status: str = "success"
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None 
from typing import Optional, Any

class APIResponse(BaseModel):
    """统一API响应格式"""
    status: str = "success"
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None