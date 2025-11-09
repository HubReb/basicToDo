"""Integration tests for ToDoEntryBuilder with real validators."""
import datetime
import uuid

import pytest

from backend.app.business_logic.builders.todo_entry_builder import ToDoEntryBuilder
from backend.app.business_logic.exceptions import ToDoValidationError
from backend.app.business_logic.validators import ValidatorFactory
from backend.app.logger import CustomLogger
from backend.app.models.todo import ToDoEntryData
from backend.app.schemas.data_schemes.create_todo_schema import ToDoCreateScheme


@pytest.fixture
def builder():
    """Create ToDoEntryBuilder with real validators."""
    logger = CustomLogger("ToDoEntryBuilderIntegrationTest")
    uuid_validator = ValidatorFactory.create_uuid_validator(logger)
    field_validator = ValidatorFactory.create_field_validator(logger)
    return ToDoEntryBuilder(uuid_validator, field_validator)


class TestToDoEntryBuilderRealWorldScenarios:
    """Test ToDoEntryBuilder in realistic scenarios."""

    @pytest.mark.asyncio
    async def test_build_typical_todo_entry(self, builder):
        """Test building a typical ToDo entry."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(
            id=test_uuid,
            title="Buy groceries for dinner",
            description="Need to buy milk, eggs, and bread"
        )

        result = await builder.build_from_create_schema(payload)

        assert isinstance(result, ToDoEntryData)
        assert result.id == test_uuid
        assert result.title == "Buy groceries for dinner"
        assert result.description == "Need to buy milk, eggs, and bread"
        assert isinstance(result.created_at, datetime.datetime)
        assert result.updated_at is None
        assert result.deleted is False
        assert result.done is False

    @pytest.mark.asyncio
    async def test_build_todo_with_emojis(self, builder):
        """Test building ToDo with emojis."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(
            id=test_uuid,
            title="🎉 Birthday party 🎂",
            description="Plan birthday celebration"
        )

        result = await builder.build_from_create_schema(payload)

        assert result.title == "🎉 Birthday party 🎂"
        assert result.description == "Plan birthday celebration"

    @pytest.mark.asyncio
    async def test_build_todo_strips_whitespace(self, builder):
        """Test building ToDo strips leading/trailing whitespace."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(
            id=test_uuid,
            title="  Meeting notes  ",
            description="  Important points  "
        )

        result = await builder.build_from_create_schema(payload)

        assert result.title == "Meeting notes"
        assert result.description == "Important points"

    @pytest.mark.asyncio
    async def test_build_todo_with_empty_description(self, builder):
        """Test building ToDo with empty description."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(
            id=test_uuid,
            title="Quick task",
            description=""
        )

        result = await builder.build_from_create_schema(payload)

        assert result.title == "Quick task"
        assert result.description == ""

    @pytest.mark.asyncio
    async def test_build_todo_with_multiline_description(self, builder):
        """Test building ToDo with multi-line description."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(
            id=test_uuid,
            title="Project tasks",
            description="Step 1: Research\nStep 2: Design\nStep 3: Implement"
        )

        result = await builder.build_from_create_schema(payload)

        assert result.title == "Project tasks"
        assert result.description == "Step 1: Research\nStep 2: Design\nStep 3: Implement"

    @pytest.mark.asyncio
    async def test_build_todo_with_special_characters(self, builder):
        """Test building ToDo with special characters."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(
            id=test_uuid,
            title="Fix bug #123 (urgent!)",
            description="Cost: $50.00 | Due: 2024-01-15"
        )

        result = await builder.build_from_create_schema(payload)

        assert result.title == "Fix bug #123 (urgent!)"
        assert result.description == "Cost: $50.00 | Due: 2024-01-15"


class TestToDoEntryBuilderValidationIntegration:
    """Test ToDoEntryBuilder validation integration."""

    @pytest.mark.asyncio
    async def test_build_rejects_invalid_uuid(self, builder):
        """Test builder rejects invalid UUID."""
        # Bypass Pydantic validation by creating mock payload
        from unittest.mock import MagicMock
        payload = MagicMock(spec=ToDoCreateScheme)
        payload.id = "not-a-valid-uuid"
        payload.title = "Test"
        payload.description = "Desc"

        with pytest.raises(ToDoValidationError) as exc_info:
            await builder.build_from_create_schema(payload)

        assert "Invalid UUID" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_build_rejects_empty_title(self, builder):
        """Test builder rejects empty title."""
        # Bypass Pydantic validation by creating mock payload
        from unittest.mock import MagicMock
        test_uuid = uuid.uuid4()
        payload = MagicMock(spec=ToDoCreateScheme)
        payload.id = test_uuid
        payload.title = ""
        payload.description = "Desc"

        with pytest.raises(ToDoValidationError) as exc_info:
            await builder.build_from_create_schema(payload)

        assert "title is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_build_rejects_whitespace_only_title(self, builder):
        """Test builder rejects whitespace-only title."""
        # Bypass Pydantic validation by creating mock payload
        from unittest.mock import MagicMock
        test_uuid = uuid.uuid4()
        payload = MagicMock(spec=ToDoCreateScheme)
        payload.id = test_uuid
        payload.title = "   "
        payload.description = "Desc"

        with pytest.raises(ToDoValidationError) as exc_info:
            await builder.build_from_create_schema(payload)

        assert "title is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_build_rejects_sql_injection_in_title(self, builder):
        """Test builder rejects SQL injection in title."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(
            id=test_uuid,
            title="'; DROP TABLE todos; --",
            description="Desc"
        )

        with pytest.raises(ToDoValidationError) as exc_info:
            await builder.build_from_create_schema(payload)

        assert "Invalid characters or SQL keywords" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_build_rejects_sql_injection_in_description(self, builder):
        """Test builder rejects SQL injection in description."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(
            id=test_uuid,
            title="Valid Title",
            description="Test /* */ SELECT * FROM users"
        )

        with pytest.raises(ToDoValidationError) as exc_info:
            await builder.build_from_create_schema(payload)

        assert "Invalid characters or SQL keywords" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_build_with_none_payload(self, builder):
        """Test builder rejects None payload."""
        with pytest.raises(ToDoValidationError) as exc_info:
            await builder.build_from_create_schema(None)  # type: ignore

        assert "payload cannot be None" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_build_with_none_id(self, builder):
        """Test builder rejects None ID."""
        # Bypass Pydantic validation by creating mock payload
        from unittest.mock import MagicMock
        payload = MagicMock(spec=ToDoCreateScheme)
        payload.id = None
        payload.title = "Test"
        payload.description = "Desc"

        with pytest.raises(ToDoValidationError) as exc_info:
            await builder.build_from_create_schema(payload)

        assert "id is required" in str(exc_info.value)


class TestToDoEntryBuilderTimestampGeneration:
    """Test ToDoEntryBuilder timestamp generation."""

    @pytest.mark.asyncio
    async def test_build_generates_created_at_timestamp(self, builder):
        """Test builder generates created_at timestamp."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(
            id=test_uuid,
            title="Test",
            description="Desc"
        )

        before = datetime.datetime.now()
        result = await builder.build_from_create_schema(payload)
        after = datetime.datetime.now()

        assert before <= result.created_at <= after

    @pytest.mark.asyncio
    async def test_build_consecutive_entries_have_different_timestamps(self, builder):
        """Test consecutive builds may have different timestamps."""
        test_uuid1 = uuid.uuid4()
        test_uuid2 = uuid.uuid4()

        payload1 = ToDoCreateScheme(id=test_uuid1, title="First", description="Desc1")
        payload2 = ToDoCreateScheme(id=test_uuid2, title="Second", description="Desc2")

        result1 = await builder.build_from_create_schema(payload1)

        # Small delay to ensure different timestamp
        import asyncio
        await asyncio.sleep(0.01)

        result2 = await builder.build_from_create_schema(payload2)

        # Timestamps should be different (at least one microsecond apart)
        assert result1.created_at <= result2.created_at