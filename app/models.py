"""ORM Models for AutoAI.

Task and ExecutionLog models for storing task configurations
and execution history.
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Task(Base):
    """Task configuration model.

    Stores scheduled task definitions including API endpoint,
    credentials, scheduling rules, and message content.
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    api_endpoint: Mapped[str] = mapped_column(String(500))
    api_key: Mapped[str] = mapped_column(String(500))  # Encrypted storage
    schedule_type: Mapped[str] = mapped_column(String(20))  # interval | fixed_time
    interval_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fixed_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # HH:MM
    message_content: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(100))  # AI model name
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    execution_logs: Mapped[List["ExecutionLog"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, name='{self.name}', enabled={self.enabled})>"


class ExecutionLog(Base):
    """Execution log model.

    Records the history of task executions including status,
    response summary, and error messages.
    """

    __tablename__ = "execution_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    executed_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20))  # success | failed
    response_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship
    task: Mapped["Task"] = relationship(back_populates="execution_logs")

    def __repr__(self) -> str:
        return f"<ExecutionLog(id={self.id}, task_id={self.task_id}, status='{self.status}')>"
