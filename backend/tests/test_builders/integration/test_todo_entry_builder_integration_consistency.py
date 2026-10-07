import uuid

import pytest
from pydantic import ValidationError

from backend.app.business_logic.builders.todo_entry_builder import ToDoEntryBuilder
from backend.app.business_logic.validators import ValidatorFactory
from backend.app.logger import CustomLogger
from backend.app.schemas.data_schemes.create_todo_schema import ToDoCreateScheme

# pytest fixtures shared from the sibling test module: the import is what
# makes them available, hence noqa F401 here and F811 on the test parameters.
from backend.tests.test_builders.integration.test_todo_entry_builder_integration import (  # noqa: F401
    builder,
)


class TestToDoEntryBuilderDataConsistency:
    """Test ToDoEntryBuilder maintains data consistency."""

    @pytest.mark.asyncio
    async def test_build_same_payload_produces_consistent_structure(
        self, builder  # noqa: F811
    ):
        """Test same payload produces consistent structure."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(
            id=test_uuid, title="Test Title", description="Test Description"
        )

        result1 = await builder.build_from_create_schema(payload)
        result2 = await builder.build_from_create_schema(payload)

        assert result1.id == result2.id
        assert result1.title == result2.title
        assert result1.description == result2.description
        assert result1.deleted == result2.deleted is False
        assert result1.done == result2.done is False
        assert result1.updated_at == result2.updated_at is None

    @pytest.mark.asyncio
    async def test_build_different_builders_same_result(self):
        """Test different builder instances produce same result."""
        logger1 = CustomLogger("Test1")
        logger2 = CustomLogger("Test2")

        builder1 = ToDoEntryBuilder(
            ValidatorFactory.create_uuid_validator(logger1),
            ValidatorFactory.create_field_validator(logger1),
        )
        builder2 = ToDoEntryBuilder(
            ValidatorFactory.create_uuid_validator(logger2),
            ValidatorFactory.create_field_validator(logger2),
        )

        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(id=test_uuid, title="Test", description="Desc")

        result1 = await builder1.build_from_create_schema(payload)
        result2 = await builder2.build_from_create_schema(payload)

        assert result1.id == result2.id
        assert result1.title == result2.title
        assert result1.description == result2.description


class TestToDoEntryBuilderBoundaryConditions:
    """Test ToDoEntryBuilder boundary conditions."""

    @pytest.mark.asyncio
    async def test_build_with_single_character_title(self, builder):  # noqa: F811
        """Test builder with single character title."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(id=test_uuid, title="X", description="Desc")

        result = await builder.build_from_create_schema(payload)

        assert result.title == "X"

    def test_over_length_text_never_reaches_the_builder(self):
        """Q6.2: the schema refuses more than 255 characters."""
        with pytest.raises(ValidationError):
            ToDoCreateScheme(id=uuid.uuid4(), title="a" * 1000, description="b" * 5000)

    @pytest.mark.asyncio
    async def test_build_with_maximal_text(self, builder):  # noqa: F811
        """Q6.2: 255 characters (code points, here 4-byte UTF-8) pass through."""
        title, description = "\U0001f600" * 255, "\U0001f601" * 255
        payload = ToDoCreateScheme(
            id=uuid.uuid4(), title=title, description=description
        )

        result = await builder.build_from_create_schema(payload)

        assert (result.title, result.description) == (title, description)

    @pytest.mark.asyncio
    async def test_build_with_nil_uuid(self, builder):  # noqa: F811
        """Test builder with nil (all zeros) UUID."""
        nil_uuid = uuid.UUID("00000000-0000-0000-0000-000000000000")
        payload = ToDoCreateScheme(id=nil_uuid, title="Test", description="Desc")

        result = await builder.build_from_create_schema(payload)

        assert result.id == nil_uuid

    @pytest.mark.asyncio
    async def test_build_preserves_unicode_and_special_chars(
        self, builder  # noqa: F811
    ):
        """Test builder preserves Unicode and special characters."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(
            id=test_uuid,
            title="Hello 世界 🌍 @ #tags",
            description="Symbols: €¥£ © ® ™",
        )

        result = await builder.build_from_create_schema(payload)

        assert result.title == "Hello 世界 🌍 @ #tags"
        assert result.description == "Symbols: €¥£ © ® ™"
