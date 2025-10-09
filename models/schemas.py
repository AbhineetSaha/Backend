from pydantic import BaseModel


class ConversationCreate(BaseModel):
    """Payload for creating a new conversation."""

    title: str | None = None


class ConversationUpdate(BaseModel):
    """Payload for updating an existing conversation."""

    title: str
