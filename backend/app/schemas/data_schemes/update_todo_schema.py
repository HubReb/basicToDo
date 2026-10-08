"""Update todo entry data schema"""

from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field, WithJsonSchema, field_validator

from backend.app.schemas.data_schemes.text_rules import (
    MAX_TEXT_LENGTH,
    clean_description,
    clean_title,
)


class TodoUpdateScheme(BaseModel):
    # title and done may be left out, but not sent as null (Q6.3): None only
    # stands for "not sent", and the schema shows them as not nullable.
    # description may be null, which clears it.
    title: Annotated[
        Optional[str], WithJsonSchema({"type": "string", "maxLength": MAX_TEXT_LENGTH})
    ] = None
    description: Optional[str] = Field(
        default=None, json_schema_extra={"maxLength": MAX_TEXT_LENGTH}
    )
    done: Annotated[Optional[bool], WithJsonSchema({"type": "boolean"})] = None

    @field_validator("title", "done", mode="before")
    @classmethod
    def reject_null(cls, value: Any) -> Any:
        """Q6.3: an explicit null is a validation error, not a 500."""
        if value is None:
            raise ValueError("must not be null")
        return value

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: Optional[str]) -> Optional[str]:
        """Q6.2: no control characters, stripped, not blank, at most 255 characters."""
        return None if value is None else clean_title(value)

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: Optional[str]) -> Optional[str]:
        """Q6.2: no control characters but tab and line breaks, stripped, at most 255."""
        return clean_description(value)
