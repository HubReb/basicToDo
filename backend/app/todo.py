"""A ToDo data class"""

from typing import Any
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import app.schemas as schemas
from app.database import get_db
import app.models as models


def exists(value: Any) -> Any:
    """Verify value is not null."""
    if value is not None:
        return value
    raise ValueError("value must not be None.")


class ToDoRepository:
    """Repository for ToDos"""

    def __init__(self, db: Session = Depends(get_db)):
        """Initialize repository"""
        for val in get_db():
            self.database_connection: Session = val

    def add_to_do(self, payload: models.ToDo):
        """Add a new ToDo entry."""
        try:
            self.database_connection.add(payload)
            self.database_connection.commit()
            self.database_connection.refresh(payload)

        except IntegrityError as e:
            self.database_connection.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A ToDo with the given details already exists.",
            ) from e
        except Exception as e:
            self.database_connection.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An errror occurred while creating the ToDo entry.",
            ) from e

        to_do_schema = schemas.ToDo.model_validate(payload)
        return schemas.ToDoResponse(
            status=schemas.Status.SUCCESS, todo_entry=to_do_schema
        )

    def delete_to_do(self, to_do_id: str):
        """Delete a ToDo."""
        try:
            to_do_query = self.database_connection.query(models.ToDo).filter_by(
                id=to_do_id
            )
            if not to_do_query.first():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No ToDo entry with id {to_do_id} found.",
                )
            to_do_query.delete(synchronize_session=False)
            self.database_connection.commit()
            return schemas.DeleteToDoResponse(
                status=schemas.Status.SUCCESS, message="ToDo deleted successfully."
            )
        except Exception as e:
            self.database_connection.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while deleting the ToDo entry.",
            ) from e

    def update_to_do(self, to_do_id: str, payload: schemas.ToDo):
        """Update an existing ToDo entry."""
        try:
            to_do_query = self.database_connection.query(models.ToDo).filter_by(
                id=to_do_id
            )
            to_do_entry = to_do_query.first()
            if not to_do_entry:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No ToDo entry with id {to_do_id} found.",
                )
            update_data = payload.model_dump()
            to_do_entry.update(update_data)
            self.database_connection.commit()
            self.database_connection.refresh(to_do_entry)
            to_do_schema = schemas.ToDo.model_validate(to_do_entry)
            return schemas.ToDoResponse(
                status=schemas.Status.SUCCESS, todo_entry=to_do_schema
            )
        except IntegrityError as e:
            self.database_connection.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with the given details already exists.",
            ) from e

        except Exception as e:
            self.database_connection.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while updating the ToDo entry.",
            ) from e

    def get_to_do_entry(self, to_do_entry_id: str):
        """Get an ToDo entry."""
        to_do_query = self.database_connection.query(models.ToDo).filter_by(
            id=to_do_entry_id
        )
        to_do_entry = to_do_query.first()
        if not to_do_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No entry with this id: {to_do_entry_id} found.",
            )
        try:
            return schemas.GetToDoResponse(
                status=schemas.Status.SUCCESS,
                todo_entry=schemas.ToDo.model_validate(to_do_entry),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while fetching the ToDo entry.",
            ) from e

    def get_all_to_do_entries(self, limit: int = 10, page: int = 1):
        """Search all ToDo entries for the search string."""
        skip = (page - 1) * limit
        to_do_entries = (
            self.database_connection.query(models.ToDo).limit(limit).offset(skip).all()
        )
        return to_do_entries
