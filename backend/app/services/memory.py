"""Memory service - Manages conversation history per user."""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.models import Message
from app.core.config import settings
from app.core.logging import logger


class MemoryService:
    """Manages per-user conversation memory backed by the database."""

    def __init__(self) -> None:
        self.max_messages = settings.MAX_MEMORY_MESSAGES

    def get_history(self, db: Session, phone: str) -> List[dict]:
        """Retrieve the last N messages for a user."""
        messages = (
            db.query(Message)
            .filter(Message.phone == phone)
            .order_by(Message.created_at.desc())
            .limit(self.max_messages)
            .all()
        )
        # Return in chronological order
        messages.reverse()
        return [
            {
                "direction": msg.direction,
                "content": msg.content,
                "agent_type": msg.agent_type,
                "created_at": str(msg.created_at) if msg.created_at else None,
            }
            for msg in messages
        ]

    def save_message(
        self,
        db: Session,
        phone: str,
        direction: str,
        content: str,
        message_type: str = "text",
        whatsapp_message_id: Optional[str] = None,
        agent_type: Optional[str] = None,
    ) -> Message:
        """Save a message to the database."""
        msg = Message(
            phone=phone,
            direction=direction,
            content=content,
            message_type=message_type,
            whatsapp_message_id=whatsapp_message_id,
            agent_type=agent_type,
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        logger.info(f"Saved {direction} message for {phone}")
        return msg


# Singleton instance
memory_service = MemoryService()
