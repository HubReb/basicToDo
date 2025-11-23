""" Data schemes for the API responses"""

from typing import Optional

from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None
    error: Optional[str] = None