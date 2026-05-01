"""Tests for ToDoService.count_deleted()."""
import pytest


class TestCountDeleted:
    @pytest.mark.asyncio
    async def test_count_deleted_returns_repository_value(
        self, todo_service_with_mock_repo, mock_repository
    ):
        mock_repository.count_deleted.return_value = 7

        result = await todo_service_with_mock_repo.count_deleted()

        assert result == 7
        mock_repository.count_deleted.assert_awaited_once_with()

    @pytest.mark.asyncio
    async def test_count_deleted_returns_zero_when_none(
        self, todo_service_with_mock_repo, mock_repository
    ):
        mock_repository.count_deleted.return_value = 0

        result = await todo_service_with_mock_repo.count_deleted()

        assert result == 0
