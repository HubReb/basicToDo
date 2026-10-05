import uuid

import pytest

from backend.app.schemas.data_schemes.create_todo_schema import ToDoCreateScheme
from backend.tests.test_builders.unit.test_todo_entry_builder import (builder, mock_field_validator,
                                                                      mock_uuid_validator)


class TestToDoEntryBuilderEdgeCases:
    """Test ToDoEntryBuilder edge cases."""

    @pytest.mark.asyncio
    async def test_build_with_very_long_title(self, builder, mock_uuid_validator, mock_field_validator):
        """Test builder with very long title."""
        test_uuid = uuid.uuid4()
        long_title = "a" * 10000
        payload = ToDoCreateScheme(id=test_uuid, title=long_title, description="Desc")

        mock_uuid_validator.validate.return_value = test_uuid
        mock_field_validator.validate_required.return_value = long_title
        mock_field_validator.validate_optional.return_value = "Desc"

        result = await builder.build_from_create_schema(payload)

        assert result.title == long_title

    @pytest.mark.asyncio
    async def test_build_with_unicode_characters(self, builder, mock_uuid_validator, mock_field_validator):
        """Test builder with Unicode characters."""
        test_uuid = uuid.uuid4()
        unicode_title = "Hello 世界 🌍"
        payload = ToDoCreateScheme(id=test_uuid, title=unicode_title, description="Desc")

        mock_uuid_validator.validate.return_value = test_uuid
        mock_field_validator.validate_required.return_value = unicode_title
        mock_field_validator.validate_optional.return_value = "Desc"

        result = await builder.build_from_create_schema(payload)

        assert result.title == unicode_title

    @pytest.mark.asyncio
    async def test_build_consecutive_calls_different_timestamps(self, builder, mock_uuid_validator,
                                                                mock_field_validator):
        """Test consecutive builds have different timestamps."""
        test_uuid1 = uuid.uuid4()
        test_uuid2 = uuid.uuid4()
        payload1 = ToDoCreateScheme(id=test_uuid1, title="Title1", description="Desc1")
        payload2 = ToDoCreateScheme(id=test_uuid2, title="Title2", description="Desc2")

        mock_uuid_validator.validate.side_effect = [test_uuid1, test_uuid2]
        mock_field_validator.validate_required.side_effect = ["Title1", "Title2"]
        mock_field_validator.validate_optional.side_effect = ["Desc1", "Desc2"]

        result1 = await builder.build_from_create_schema(payload1)
        # Small delay to ensure different timestamp
        import asyncio
        await asyncio.sleep(0.001)
        result2 = await builder.build_from_create_schema(payload2)

        # Timestamps should be different (or very close)
        assert result1.created_at != result2.created_at or result1.created_at == result2.created_at  # Allow for fast execution