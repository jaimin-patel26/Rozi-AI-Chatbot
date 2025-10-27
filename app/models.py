from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Float
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    firstname = Column(String, nullable=False)
    lastname = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    phone = Column(String, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)
    street = Column(String, nullable=True)
    billing_city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    post_code = Column(String, nullable=True)
    billing_country = Column(String, nullable=True)
    linkedin = Column(String, nullable=True)
    instagram = Column(String, nullable=True)
    facebook = Column(String, nullable=True)
    x = Column(String, nullable=True)
    photo = Column(String, nullable=True)

    api_keys = relationship("APIKEY", back_populates="user", cascade="all, delete-orphan")
    agents = relationship("Agent", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessages", back_populates="user", cascade="all, delete-orphan")
    uploaded_files = relationship("UploadedFile", back_populates="user", cascade="all, delete-orphan")
    faiss_databases = relationship("FaissDatabase", back_populates="user", cascade="all, delete-orphan")


class APIKEY(Base):
    __tablename__ = "apikey"
 
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agent.id", ondelete="CASCADE"), nullable=False)
    api_key = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
 
    user = relationship("User", back_populates="api_keys")
    agent = relationship("Agent", back_populates="api_keys")
    chat_sessions = relationship("ChatSession", back_populates="apikey", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessages", back_populates="apikey", cascade="all, delete-orphan")

class Agent(Base):
    __tablename__ = "agent"	
 
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    purpose = Column(String, nullable=True)
    chatbot_type = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="agents")
    api_keys = relationship("APIKEY", back_populates="agent", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="agent", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessages", back_populates="agent", cascade="all, delete-orphan")

class ChatSession(Base):
    __tablename__ = "chat_session"
 
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agent.id", ondelete="CASCADE"), nullable=False)
    apikey_id = Column(UUID(as_uuid=True), ForeignKey("apikey.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 

    user = relationship("User", back_populates="chat_sessions")
    agent = relationship("Agent", back_populates="chat_sessions")
    apikey = relationship("APIKEY", back_populates="chat_sessions")
    chat_messages = relationship("ChatMessages", back_populates="session", cascade="all, delete-orphan")

class ChatMessages(Base):
    __tablename__ = "chat_message"
 
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    apikey_id = Column(UUID(as_uuid=True), ForeignKey("apikey.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_session.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agent.id", ondelete="CASCADE"), nullable=False)
 
    messages = Column(JSONB, default=list, nullable=False)
    chatbot_type = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
 
    __table_args__ = (
        Index('ix_chat_message_user_session', 'user_id', 'session_id'),
    )

    user = relationship("User", back_populates="chat_messages")
    apikey = relationship("APIKEY", back_populates="chat_messages")
    session = relationship("ChatSession", back_populates="chat_messages")
    agent = relationship("Agent", back_populates="chat_messages")
    

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    s3_url = Column(String, nullable=False)
    filetype = Column(String, nullable=False)
    filesize=Column(String,nullable=False)
    uploaded_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="uploaded_files")

class FaissDatabase(Base):
    __tablename__ = "faiss_databases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    faiss_url = Column(String, nullable=False)  
    pkl_url = Column(String, nullable=False)
    uploaded_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="faiss_databases")


