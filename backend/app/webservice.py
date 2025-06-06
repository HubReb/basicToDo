""" The webservice base class """

import uuid

from typing import Literal
from fastapi import HTTPException, status

from app.logger import CustomLogger

class Webservice:
    """ Webservice """

    def __init__(self, logger: CustomLogger):
        self.logger = logger;

    def raise_http_exception(self, status_code: Literal[409] | Literal [500] | Literal[404], id_code: uuid.UUID) -> HTTPException:
        """Raise an exception error"""
        if not status_code:
            self.logger.log_missing_parameter('status_code')
            raise ValueError("status_code is None")
        if not id_code:
            self.logger.log_missing_parameter('id_cde')
            raise ValueError("id_code is None")
        if not status_code:
            self.logger.log_missing_parameter('exceptiontype')
            raise ValueError("exceptiontype is None")
    
        if status_code == status.HTTP_409_CONFLICT:
                raise HTTPException(
                status_code=status_code,
                detail="A ToDo with the given details does already exists.",
            )
        if status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            raise HTTPException(
                status_code=status_code,
                detail="An errror occurred while creating the ToDo entry.",
            )

        if status_code == status.HTTP_404_NOT_FOUND: 
            raise HTTPException(
                status_code=status_code,
                detail=f"No ToDo entry with id {id_code} found.",
            )
        raise ValueError("{status_code} is unknown.")
        
