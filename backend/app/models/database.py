import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    ws_tickets = relationship("WSTicket", back_populates="user", cascade="all, delete-orphan")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" o "assistant"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sources = Column(Text, nullable=True)  # JSON string con las fuentes

    session = relationship("ChatSession", back_populates="messages")


class WSTicket(Base):
    __tablename__ = "ws_tickets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="ws_tickets")


def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
