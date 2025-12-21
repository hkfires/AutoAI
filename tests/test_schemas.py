"""Tests for Pydantic schemas."""

import os
import pytest
from datetime import datetime
from cryptography.fernet import Fernet
from pydantic import ValidationError


@pytest.fixture(autouse=True)
def setup_encryption_key(monkeypatch):
    """Set up environment for schema tests."""
    test_key = Fernet.generate_key().decode()
    monkeypatch.setenv("ENCRYPTION_KEY", test_key)
    monkeypatch.setenv("ADMIN_PASSWORD", "test123")


def test_task_create_valid():
    """Test TaskCreate with all required fields."""
    from app.schemas import TaskCreate

    task = TaskCreate(
        name="Test Task",
        api_endpoint="https://api.example.com/v1/chat",
        api_key="sk-secret-key",
        schedule_type="interval",
        interval_minutes=30,
        message_content="Hello!",
    )

    assert task.name == "Test Task"
    assert task.api_key == "sk-secret-key"
    assert task.enabled is True  # Default


def test_task_create_fixed_time():
    """Test TaskCreate with fixed_time schedule."""
    from app.schemas import TaskCreate

    task = TaskCreate(
        name="Daily Task",
        api_endpoint="https://api.example.com",
        api_key="key",
        schedule_type="fixed_time",
        fixed_time="09:30",
        message_content="Morning report",
        enabled=False,
    )

    assert task.schedule_type == "fixed_time"
    assert task.fixed_time == "09:30"
    assert task.enabled is False


def test_task_create_missing_required_field():
    """Test TaskCreate raises error when required field is missing."""
    from app.schemas import TaskCreate

    with pytest.raises(ValidationError) as exc_info:
        TaskCreate(
            name="Test",
            api_endpoint="https://api.example.com",
            # Missing api_key
            schedule_type="interval",
            message_content="Test",
        )

    assert "api_key" in str(exc_info.value)


def test_task_update_all_optional():
    """Test TaskUpdate allows all optional fields."""
    from app.schemas import TaskUpdate

    # Empty update is valid
    update = TaskUpdate()
    assert update.name is None
    assert update.api_key is None

    # Partial update
    update = TaskUpdate(name="New Name", enabled=False)
    assert update.name == "New Name"
    assert update.enabled is False
    assert update.api_endpoint is None


def test_task_response_masks_api_key():
    """Test TaskResponse automatically masks api_key."""
    from app.schemas import TaskResponse

    response = TaskResponse(
        id=1,
        name="Test Task",
        api_endpoint="https://api.example.com",
        api_key="sk-1234567890abcdef",  # Long key
        schedule_type="interval",
        interval_minutes=30,
        message_content="Hello",
        enabled=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # Key should be masked
    assert response.api_key == "sk-1...cdef"


def test_task_response_masks_short_key():
    """Test TaskResponse masks short api_key as ***."""
    from app.schemas import TaskResponse

    response = TaskResponse(
        id=1,
        name="Test",
        api_endpoint="https://api.example.com",
        api_key="short",  # Short key
        schedule_type="interval",
        interval_minutes=30,
        message_content="Hello",
        enabled=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    assert response.api_key == "***"


def test_task_response_from_attributes():
    """Test TaskResponse can be created from ORM attributes."""
    from app.schemas import TaskResponse

    class MockTask:
        """Mock Task ORM object."""
        id = 1
        name = "Test Task"
        api_endpoint = "https://api.example.com"
        api_key = "sk-1234567890abcdef"
        schedule_type = "interval"
        interval_minutes = 30
        fixed_time = None
        message_content = "Hello"
        enabled = True
        created_at = datetime.now()
        updated_at = datetime.now()

    response = TaskResponse.model_validate(MockTask())

    assert response.id == 1
    assert response.name == "Test Task"
    assert response.api_key == "sk-1...cdef"  # Masked


def test_execution_log_response_valid():
    """Test ExecutionLogResponse with all fields."""
    from app.schemas import ExecutionLogResponse

    log = ExecutionLogResponse(
        id=1,
        task_id=5,
        executed_at=datetime.now(),
        status="success",
        response_summary="Task completed",
    )

    assert log.id == 1
    assert log.task_id == 5
    assert log.status == "success"
    assert log.error_message is None  # Optional


def test_execution_log_response_with_error():
    """Test ExecutionLogResponse with error message."""
    from app.schemas import ExecutionLogResponse

    log = ExecutionLogResponse(
        id=2,
        task_id=5,
        executed_at=datetime.now(),
        status="failed",
        error_message="Connection timeout",
    )

    assert log.status == "failed"
    assert log.error_message == "Connection timeout"
    assert log.response_summary is None


def test_task_create_invalid_schedule_type():
    """Test TaskCreate rejects invalid schedule_type."""
    from app.schemas import TaskCreate

    with pytest.raises(ValidationError) as exc_info:
        TaskCreate(
            name="Test",
            api_endpoint="https://api.example.com",
            api_key="key",
            schedule_type="invalid",  # Invalid type
            interval_minutes=30,
            message_content="Test",
        )

    assert "schedule_type" in str(exc_info.value)


def test_task_create_interval_requires_interval_minutes():
    """Test TaskCreate requires interval_minutes when schedule_type is interval."""
    from app.schemas import TaskCreate

    with pytest.raises(ValidationError) as exc_info:
        TaskCreate(
            name="Test",
            api_endpoint="https://api.example.com",
            api_key="key",
            schedule_type="interval",
            # Missing interval_minutes
            message_content="Test",
        )

    assert "interval_minutes is required" in str(exc_info.value)


def test_task_create_fixed_time_requires_fixed_time():
    """Test TaskCreate requires fixed_time when schedule_type is fixed_time."""
    from app.schemas import TaskCreate

    with pytest.raises(ValidationError) as exc_info:
        TaskCreate(
            name="Test",
            api_endpoint="https://api.example.com",
            api_key="key",
            schedule_type="fixed_time",
            # Missing fixed_time
            message_content="Test",
        )

    assert "fixed_time is required" in str(exc_info.value)


def test_task_create_invalid_fixed_time_format():
    """Test TaskCreate validates fixed_time format."""
    from app.schemas import TaskCreate

    with pytest.raises(ValidationError) as exc_info:
        TaskCreate(
            name="Test",
            api_endpoint="https://api.example.com",
            api_key="key",
            schedule_type="fixed_time",
            fixed_time="25:00",  # Invalid hour
            message_content="Test",
        )

    assert "HH:MM" in str(exc_info.value)


def test_task_create_invalid_interval_minutes():
    """Test TaskCreate validates interval_minutes is positive."""
    from app.schemas import TaskCreate

    with pytest.raises(ValidationError) as exc_info:
        TaskCreate(
            name="Test",
            api_endpoint="https://api.example.com",
            api_key="key",
            schedule_type="interval",
            interval_minutes=0,  # Invalid: must be positive
            message_content="Test",
        )

    assert "positive" in str(exc_info.value)


def test_task_update_validates_schedule_type():
    """Test TaskUpdate validates schedule_type if provided."""
    from app.schemas import TaskUpdate

    with pytest.raises(ValidationError) as exc_info:
        TaskUpdate(schedule_type="invalid")

    assert "schedule_type" in str(exc_info.value)


def test_task_update_validates_fixed_time_format():
    """Test TaskUpdate validates fixed_time format if provided."""
    from app.schemas import TaskUpdate

    with pytest.raises(ValidationError) as exc_info:
        TaskUpdate(fixed_time="99:99")

    assert "HH:MM" in str(exc_info.value)
