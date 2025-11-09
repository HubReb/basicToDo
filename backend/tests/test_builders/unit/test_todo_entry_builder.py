"""Unit tests for ToDoEntryBuilder."""
import datetime
import uuid
from unittest.mock import MagicMock, patch

import pytest

from backend.app.business_logic.builders.todo_entry_builder import ToDoEntryBuilder
from backend.app.business_logic.exceptions import ToDoValidationError
from backend.app.models.todo import ToDoEntryData
from backend.app.schemas.data_schemes.create_todo_schema import ToDoCreateScheme


@pytest.fixture
def mock_uuid_validator():
    """Create a mock UUIDValidator."""
    return MagicMock()


@pytest.fixture
def mock_field_validator():
    """Create a mock FieldValidator."""
    return MagicMock()


@pytest.fixture
def builder(mock_uuid_validator, mock_field_validator):
    """Create ToDoEntryBuilder with mocked validators."""
    return ToDoEntryBuilder(mock_uuid_validator, mock_field_validator)


class TestToDoEntryBuilderSuccess:
    """Test ToDoEntryBuilder successful builds."""

    @pytest.mark.asyncio
    async def test_build_from_create_schema_success(self, builder, mock_uuid_validator, mock_field_validator):
        """Test building ToDoEntryData from valid schema."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(id=test_uuid, title="Test Title", description="Test Description")

        mock_uuid_validator.validate.return_value = test_uuid
        mock_field_validator.validate_required.return_value = "Test Title"
        mock_field_validator.validate_optional.return_value = "Test Description"

        with patch('backend.app.business_logic.builders.todo_entry_builder.datetime') as mock_datetime:
            mock_now = datetime.datetime(2024, 1, 1, 12, 0, 0)
            mock_datetime.datetime.now.return_value = mock_now

            result = await builder.build_from_create_schema(payload)

            assert isinstance(result, ToDoEntryData)
            assert result.id == test_uuid
            assert result.title == "Test Title"
            assert result.description == "Test Description"
            assert result.created_at == mock_now
            assert result.updated_at is None
            assert result.deleted is False
            assert result.done is False

    @pytest.mark.asyncio
    async def test_build_calls_uuid_validator(self, builder, mock_uuid_validator, mock_field_validator):
        """Test builder calls UUID validator with payload ID."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(id=test_uuid, title="Title", description="Desc")

        mock_uuid_validator.validate.return_value = test_uuid
        mock_field_validator.validate_required.return_value = "Title"
        mock_field_validator.validate_optional.return_value = "Desc"

        await builder.build_from_create_schema(payload)

        mock_uuid_validator.validate.assert_called_once_with(test_uuid)

    @pytest.mark.asyncio
    async def test_build_calls_field_validator_for_title(self, builder, mock_uuid_validator, mock_field_validator):
        """Test builder calls field validator for required title."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(id=test_uuid, title="Test Title", description="Desc")

        mock_uuid_validator.validate.return_value = test_uuid
        mock_field_validator.validate_required.return_value = "Test Title"
        mock_field_validator.validate_optional.return_value = "Desc"

        await builder.build_from_create_schema(payload)

        mock_field_validator.validate_required.assert_called_once_with("Test Title", "title")

    @pytest.mark.asyncio
    async def test_build_calls_field_validator_for_description(self, builder, mock_uuid_validator,
                                                               mock_field_validator):
        """Test builder calls field validator for optional description."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(id=test_uuid, title="Title", description="Test Desc")

        mock_uuid_validator.validate.return_value = test_uuid
        mock_field_validator.validate_required.return_value = "Title"
        mock_field_validator.validate_optional.return_value = "Test Desc"

        await builder.build_from_create_schema(payload)

        mock_field_validator.validate_optional.assert_called_once_with("Test Desc")

    @pytest.mark.asyncio
    async def test_build_with_empty_description(self, builder, mock_uuid_validator, mock_field_validator):
        """Test builder with empty description."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(id=test_uuid, title="Title", description="")

        mock_uuid_validator.validate.return_value = test_uuid
        mock_field_validator.validate_required.return_value = "Title"
        mock_field_validator.validate_optional.return_value = ""

        result = await builder.build_from_create_schema(payload)

        assert result.description == ""

    @pytest.mark.asyncio
    async def test_build_sets_created_at_timestamp(self, builder, mock_uuid_validator, mock_field_validator):
        """Test builder sets created_at to current timestamp."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(id=test_uuid, title="Title", description="Desc")

        mock_uuid_validator.validate.return_value = test_uuid
        mock_field_validator.validate_required.return_value = "Title"
        mock_field_validator.validate_optional.return_value = "Desc"

        with patch('backend.app.business_logic.builders.todo_entry_builder.datetime') as mock_datetime:
            mock_now = datetime.datetime(2024, 1, 15, 10, 30, 45)
            mock_datetime.datetime.now.return_value = mock_now

            result = await builder.build_from_create_schema(payload)

            assert result.created_at == mock_now
            mock_datetime.datetime.now.assert_called_once()


class TestToDoEntryBuilderNonePayload:
    """Test ToDoEntryBuilder with None payload."""

    @pytest.mark.asyncio
    async def test_build_with_none_payload_raises_error(self, builder):
        """Test builder raises error for None payload."""
        with pytest.raises(ToDoValidationError) as exc_info:
            await builder.build_from_create_schema(None)  # type: ignore

        assert "payload cannot be None" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_build_with_none_payload_does_not_call_validators(self, builder, mock_uuid_validator,
                                                                    mock_field_validator):
        """Test builder doesn't call validators for None payload."""
        with pytest.raises(ToDoValidationError):
            await builder.build_from_create_schema(None)  # type: ignore

        mock_uuid_validator.validate.assert_not_called()
        mock_field_validator.validate_required.assert_not_called()
        mock_field_validator.validate_optional.assert_not_called()


class TestToDoEntryBuilderNoneID:
    """Test ToDoEntryBuilder with None ID."""

    @pytest.mark.asyncio
    async def test_build_with_none_id_raises_error(self, builder):
        """Test builder raises error for None ID."""
        # Bypass Pydantic validation by creating mock payload
        payload = MagicMock(spec=ToDoCreateScheme)
        payload.id = None
        payload.title = "Title"
        payload.description = "Desc"

        with pytest.raises(ToDoValidationError) as exc_info:
            await builder.build_from_create_schema(payload)

        assert "id is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_build_with_none_id_does_not_call_validators(self, builder, mock_uuid_validator,
                                                               mock_field_validator):
        """Test builder doesn't call validators when ID is None."""
        # Bypass Pydantic validation by creating mock payload
        payload = MagicMock(spec=ToDoCreateScheme)
        payload.id = None
        payload.title = "Title"
        payload.description = "Desc"

        with pytest.raises(ToDoValidationError):
            await builder.build_from_create_schema(payload)

        mock_uuid_validator.validate.assert_not_called()
        mock_field_validator.validate_required.assert_not_called()
        mock_field_validator.validate_optional.assert_not_called()


class TestToDoEntryBuilderValidatorErrors:
    """Test ToDoEntryBuilder propagates validator errors."""

    @pytest.mark.asyncio
    async def test_build_propagates_uuid_validation_error(self, builder, mock_uuid_validator, mock_field_validator):
        """Test builder propagates UUID validation errors."""
        # Bypass Pydantic validation by creating mock payload
        test_uuid = "invalid-uuid"
        payload = MagicMock(spec=ToDoCreateScheme)
        payload.id = test_uuid
        payload.title = "Title"
        payload.description = "Desc"

        mock_uuid_validator.validate.side_effect = ToDoValidationError("Invalid UUID")

        with pytest.raises(ToDoValidationError) as exc_info:
            await builder.build_from_create_schema(payload)

        assert "Invalid UUID" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_build_propagates_title_validation_error(self, builder, mock_uuid_validator, mock_field_validator):
        """Test builder propagates title validation errors."""
        # Bypass Pydantic validation by creating mock payload
        test_uuid = uuid.uuid4()
        payload = MagicMock(spec=ToDoCreateScheme)
        payload.id = test_uuid
        payload.title = ""
        payload.description = "Desc"

        mock_uuid_validator.validate.return_value = test_uuid
        mock_field_validator.validate_required.side_effect = ToDoValidationError("title is required")

        with pytest.raises(ToDoValidationError) as exc_info:
            await builder.build_from_create_schema(payload)

        assert "title is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_build_propagates_description_validation_error(self, builder, mock_uuid_validator,
                                                                 mock_field_validator):
        """Test builder propagates description validation errors."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(id=test_uuid, title="Title", description="DROP TABLE")

        mock_uuid_validator.validate.return_value = test_uuid
        mock_field_validator.validate_required.return_value = "Title"
        mock_field_validator.validate_optional.side_effect = ToDoValidationError("SQL injection detected")

        with pytest.raises(ToDoValidationError) as exc_info:
            await builder.build_from_create_schema(payload)

        assert "SQL injection detected" in str(exc_info.value)


class TestToDoEntryBuilderDefaults:
    """Test ToDoEntryBuilder sets correct default values."""

    @pytest.mark.asyncio
    async def test_build_sets_updated_at_to_none(self, builder, mock_uuid_validator, mock_field_validator):
        """Test builder sets updated_at to None for new entries."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(id=test_uuid, title="Title", description="Desc")

        mock_uuid_validator.validate.return_value = test_uuid
        mock_field_validator.validate_required.return_value = "Title"
        mock_field_validator.validate_optional.return_value = "Desc"

        result = await builder.build_from_create_schema(payload)

        assert result.updated_at is None

    @pytest.mark.asyncio
    async def test_build_sets_deleted_to_false(self, builder, mock_uuid_validator, mock_field_validator):
        """Test builder sets deleted to False for new entries."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(id=test_uuid, title="Title", description="Desc")

        mock_uuid_validator.validate.return_value = test_uuid
        mock_field_validator.validate_required.return_value = "Title"
        mock_field_validator.validate_optional.return_value = "Desc"

        result = await builder.build_from_create_schema(payload)

        assert result.deleted is False

    @pytest.mark.asyncio
    async def test_build_sets_done_to_false(self, builder, mock_uuid_validator, mock_field_validator):
        """Test builder sets done to False for new entries."""
        test_uuid = uuid.uuid4()
        payload = ToDoCreateScheme(id=test_uuid, title="Title", description="Desc")

        mock_uuid_validator.validate.return_value = test_uuid
        mock_field_validator.validate_required.return_value = "Title"
        mock_field_validator.validate_optional.return_value = "Desc"

        result = await builder.build_from_create_schema(payload)

        assert result.done is False