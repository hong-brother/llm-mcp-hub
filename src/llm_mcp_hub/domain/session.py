"""Session domain model"""
from datetime import datetime
from enum import Enum
from typing import Any
import uuid

from pydantic import BaseModel, Field

from .message import Message


class SessionStatus(str, Enum):
    """Session status enum"""

    ACTIVE = "active"
    CLOSED = "closed"
    EXPIRED = "expired"


class SessionContext(BaseModel):
    """Session context for initialization"""

    memory: str | None = Field(default=None, description="Project memory (e.g., CLAUDE.md content)")
    previous_summary: str | None = Field(default=None, description="Previous session summary")
    files: list[dict[str, str]] = Field(default_factory=list, description="Reference files")

    def to_system_prompt(self) -> str | None:
        """Convert context to system prompt format"""
        parts = []

        if self.memory:
            parts.append(f"# Project Context\n{self.memory}")

        if self.previous_summary:
            parts.append(f"# Previous Session Summary\n{self.previous_summary}")

        if self.files:
            files_content = "\n".join(
                f"## {f['name']}\n{f['content']}" for f in self.files if "name" in f and "content" in f
            )
            if files_content:
                parts.append(f"# Reference Files\n{files_content}")

        return "\n\n".join(parts) if parts else None


class Session(BaseModel):
    """Chat session model"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider: str = Field(description="LLM provider (claude, gemini)")
    model: str = Field(description="Default model for this session")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE)
    system_prompt: str | None = Field(default=None, description="System prompt/instruction")
    context: SessionContext | None = Field(default=None, description="Session context")
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_message(self, message: Message) -> None:
        """Add message to session"""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()

    def add_user_message(self, content: str, **metadata) -> Message:
        """Add user message"""
        message = Message.user(content, **metadata)
        self.add_message(message)
        return message

    def add_assistant_message(self, content: str, **metadata) -> Message:
        """Add assistant message"""
        message = Message.assistant(content, **metadata)
        self.add_message(message)
        return message

    def get_conversation_for_llm(self) -> list[dict[str, str]]:
        """Get conversation in LLM-compatible format"""
        result = []

        # Add system prompt if exists
        combined_system = self._build_system_prompt()
        if combined_system:
            result.append({"role": "system", "content": combined_system})

        # Add conversation messages
        for msg in self.messages:
            result.append({"role": msg.role.value, "content": msg.content})

        return result

    def _build_system_prompt(self) -> str | None:
        """Build combined system prompt from context and system_prompt"""
        parts = []

        if self.system_prompt:
            parts.append(self.system_prompt)

        if self.context:
            context_prompt = self.context.to_system_prompt()
            if context_prompt:
                parts.append(context_prompt)

        return "\n\n".join(parts) if parts else None

    def is_active(self) -> bool:
        """Check if session is active"""
        if self.status != SessionStatus.ACTIVE:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True

    def close(self) -> None:
        """Close the session"""
        self.status = SessionStatus.CLOSED
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "provider": self.provider,
            "model": self.model,
            "status": self.status.value,
            "system_prompt": self.system_prompt,
            "context": self.context.model_dump() if self.context else None,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        """Create from dictionary"""
        messages = [Message.from_dict(m) for m in data.get("messages", [])]
        context = SessionContext(**data["context"]) if data.get("context") else None

        return cls(
            id=data["id"],
            provider=data["provider"],
            model=data["model"],
            status=SessionStatus(data.get("status", "active")),
            system_prompt=data.get("system_prompt"),
            context=context,
            messages=messages,
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.utcnow()),
            updated_at=datetime.fromisoformat(data["updated_at"]) if isinstance(data.get("updated_at"), str) else data.get("updated_at", datetime.utcnow()),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            metadata=data.get("metadata", {}),
        )
