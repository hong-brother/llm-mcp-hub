"""Message domain model"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Message role enum"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Chat message model"""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create from dictionary"""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if isinstance(data.get("timestamp"), str) else data.get("timestamp", datetime.utcnow()),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def user(cls, content: str, **metadata) -> "Message":
        """Create user message"""
        return cls(role=MessageRole.USER, content=content, metadata=metadata)

    @classmethod
    def assistant(cls, content: str, **metadata) -> "Message":
        """Create assistant message"""
        return cls(role=MessageRole.ASSISTANT, content=content, metadata=metadata)

    @classmethod
    def system(cls, content: str, **metadata) -> "Message":
        """Create system message"""
        return cls(role=MessageRole.SYSTEM, content=content, metadata=metadata)
