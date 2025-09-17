"""
SQLAlchemy ORM models.
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class UserORM(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    subscription_tier = Column(String, nullable=False, default="free")
    usage_count = Column(Integer, nullable=False, default=0)
    monthly_limit = Column(Integer, nullable=False, default=100)
    password_hash = Column(String, nullable=False)


class ConversationORM(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_conversations_user_updated", "user_id", "updated_at"),
    )


class MessageORM(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String, nullable=False)  # user | assistant | system
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_messages_conv_time", "conversation_id", "timestamp"),
    )
