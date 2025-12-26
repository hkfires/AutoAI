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
        model="gemini-claude-sonnet-4-5",
    )

    assert task.name == "Test Task"
    assert task.api_key == "sk-secret-key"
    assert task.model == "gemini-claude-sonnet-4-5"
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
        model="gpt-4",
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
            model="gpt-4",
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
        model="gemini-claude-sonnet-4-5",
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
        model="gpt-4",
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
        model = "gemini-claude-sonnet-4-5"
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
            model="gpt-4",
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
            model="gpt-4",
        )

    assert "interval_minutes or interval_seconds must be greater than 0" in str(exc_info.value)


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
            model="gpt-4",
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
            model="gpt-4",
        )

    assert "HH:MM" in str(exc_info.value)


def test_task_create_invalid_interval_minutes():
    """Test TaskCreate validates interval must be greater than 0."""
    from app.schemas import TaskCreate

    with pytest.raises(ValidationError) as exc_info:
        TaskCreate(
            name="Test",
            api_endpoint="https://api.example.com",
            api_key="key",
            schedule_type="interval",
            interval_minutes=0,  # Invalid: must be > 0
            interval_seconds=0,  # Also 0, so total interval is 0
            message_content="Test",
            model="gpt-4",
        )

    assert "interval_minutes or interval_seconds must be greater than 0" in str(exc_info.value)


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


def test_task_create_with_interval_seconds():
    """Test TaskCreate accepts interval_seconds field."""
    from app.schemas import TaskCreate

    task = TaskCreate(
        name="Test",
        api_endpoint="https://api.example.com",
        api_key="key",
        schedule_type="interval",
        interval_minutes=1,
        interval_seconds=30,
        message_content="Test",
        model="gpt-4",
    )

    assert task.interval_minutes == 1
    assert task.interval_seconds == 30


def test_task_create_seconds_only():
    """Test TaskCreate accepts seconds-only interval."""
    from app.schemas import TaskCreate

    task = TaskCreate(
        name="Test",
        api_endpoint="https://api.example.com",
        api_key="key",
        schedule_type="interval",
        interval_minutes=0,
        interval_seconds=10,
        message_content="Test",
        model="gpt-4",
    )

    assert task.interval_minutes == 0
    assert task.interval_seconds == 10


def test_task_create_negative_interval_seconds():
    """Test TaskCreate rejects negative interval_seconds."""
    from app.schemas import TaskCreate

    with pytest.raises(ValidationError) as exc_info:
        TaskCreate(
            name="Test",
            api_endpoint="https://api.example.com",
            api_key="key",
            schedule_type="interval",
            interval_minutes=1,
            interval_seconds=-5,
            message_content="Test",
            model="gpt-4",
        )

    assert "non-negative" in str(exc_info.value)


def test_task_update_with_interval_seconds():
    """Test TaskUpdate accepts interval_seconds field."""
    from app.schemas import TaskUpdate

    task_update = TaskUpdate(interval_seconds=30)
    assert task_update.interval_seconds == 30


def test_task_create_large_interval_seconds():
    """Test TaskCreate accepts large interval_seconds values."""
    from app.schemas import TaskCreate

    task = TaskCreate(
        name="Test",
        api_endpoint="https://api.example.com",
        api_key="key",
        schedule_type="interval",
        interval_minutes=0,
        interval_seconds=120,  # 2 minutes expressed in seconds
        message_content="Test",
        model="gpt-4",
    )

    assert task.interval_seconds == 120


def test_task_create_boundary_one_second():
    """Test TaskCreate accepts minimum 1 second interval."""
    from app.schemas import TaskCreate

    task = TaskCreate(
        name="Test",
        api_endpoint="https://api.example.com",
        api_key="key",
        schedule_type="interval",
        interval_minutes=0,
        interval_seconds=1,
        message_content="Test",
        model="gpt-4",
    )

    assert task.interval_seconds == 1
