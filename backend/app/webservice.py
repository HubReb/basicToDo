""" The webservice base class """

import uuid

from typing import Literal, Any, List
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError


from app.todo import ToDoRepository
from app.models import ToDo
import app.schemas as schemas

class Webservice:
    """ Webservice """

    def __init__(self):
        self.repository = ToDoRepository()


    def raise_http_exception(self, status_code: Literal[409] | Literal [500] | Literal[404], id_code: uuid.UUID) -> HTTPException:
        """Raise an exception error"""
        match status_code:
            case status.HTTP_409_CONFLICT:
                raise HTTPException(
                status_code=status_code,
                detail="A ToDo with the given details does already exists.",
                )
            case status.HTTP_500_INTERNAL_SERVER_ERROR:
                raise HTTPException(
                    status_code=status_code,
                    detail="An errror occurred while creating the ToDo entry.",
                )
            case status.HTTP_404_NOT_FOUND: 
                raise HTTPException(
                    status_code=status_code,
                    detail=f"No ToDo entry with id {id_code} found.",
                )
            case _:
                raise ValueError("{status_code} is unknown.")
        
    def update_entry( self, to_do_id: uuid.UUID, payload: schemas.ToDo) -> schemas.ToDoResponse | HTTPException:
        """Update an existing entry."""
        update_data: dict[str, Any] = payload.model_dump()
        try:
            updated_entry = self.repository.update_to_do(str(to_do_id), update_data)
            to_do_schema = schemas.ToDo.model_validate(updated_entry)
            return schemas.ToDoResponse(
                status=schemas.Status.SUCCESS, todo_entry=to_do_schema
            )
        except ValueError:
            return self.raise_http_exception(status.HTTP_404_NOT_FOUND, to_do_id)
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with the given details already exists.",
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An errror occurred while creating the ToDo entry.",
            ) from exc
        
    def get_to_do_entry(self, to_do_id: uuid.UUID) -> schemas.GetToDoResponse | HTTPException:
        """ Get an entry. """
        try:
            entry = self.repository.get_to_do_entry(str(to_do_id))
        except ValueError as exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No entry with this id: {to_do_id} found.",
            ) from exp
        try:
            return schemas.GetToDoResponse(
                status=schemas.Status.SUCCESS,
                todo_entry=schemas.ToDo.model_validate(entry),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while fetching the ToDo entry.",
            ) from e

    def add_entry(self, payload: ToDo) -> schemas.ToDoResponse | HTTPException:
        """ Add a new entry. """
        try:
            self.repository.add_to_do(payload)
        except IntegrityError as exp:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A ToDo with the given details already exists.",
            ) from exp
        to_do_schema = schemas.ToDo.model_validate(payload)
        return schemas.ToDoResponse(
            status=schemas.Status.SUCCESS, todo_entry=to_do_schema
        )
    
    def delete_entry(self, to_do_id: uuid.UUID) -> schemas.DeleteToDoResponse | HTTPException:
        """ Delete a todo entry. """
        try:
            self.repository.delete_to_do(str(to_do_id))
            return schemas.DeleteToDoResponse(
                status=schemas.Status.SUCCESS, message="ToDo deleted successfully."
            )
        except ValueError as exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No ToDo entry with id {to_do_id} found.",
            ) from exp
        except Exception as exp:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while deleting the ToDo entry.",
            ) from exp

    def get_all_to_do_entries(self)  -> List[ToDo]:
        """ Get all to do entries. """
        return self.repository.get_all_to_do_entries()