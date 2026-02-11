from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class Response(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class PaginatedResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int

class StatisticsResponse(BaseModel):
    total_users: int
    total_tasks: int
    completed_tasks: int
    pending_submissions: int
    pending_withdrawals: int
    total_naira: float
    total_dollar: float