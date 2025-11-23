""" Update todo entry data schema"""
from typing import Optional

from pydantic import BaseModel


class TodoUpdateScheme(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    done: Optional[bool] = None