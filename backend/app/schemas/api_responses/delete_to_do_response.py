from typing import Optional

from backend.app.schemas.api_responses.api_response import ApiResponse


class DeleteToDoResponse(ApiResponse):
    """Response to delete user request"""
    message: Optional[str] = None