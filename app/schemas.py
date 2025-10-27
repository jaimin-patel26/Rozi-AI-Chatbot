from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    firstname: str
    lastname: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RefreshRequest(BaseModel):
    refresh_token: str

class APIKeyCreate(BaseModel):
    agent_id: UUID
    name: str

class AgentCreate(BaseModel):
    name: str
    purpose : str | None
    chatbot_type: str

class APIKeyDeleteRequest(BaseModel):
    id: UUID

class APIKeyInfo(BaseModel):
    id: UUID
    name: str | None
    api_key: str
    agent_id: UUID
    agent_name: str
    purpose: str | None
    chatbot_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class AgentInfo(BaseModel):
    id: UUID
    name: str
    purpose: str | None
    chatbot_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class AgentDeleteRequest(BaseModel):
    id: UUID

class AgentIDRequest(BaseModel):
    agent_id: UUID

class ChatbotQuery(BaseModel):
    session_id: UUID | None
    input: str

class ConversationHistory(BaseModel):
    session_id: UUID

class ChatbotAPIEndpointV1(BaseModel):
    input: str

class UploadedFileDelete(BaseModel):
    id: UUID

class DeleteSessionRequest(BaseModel):
    session_id: UUID

class ConversationHistoryInfo(BaseModel):
    session_id: UUID
    messages: list
    created_at: datetime

    class Config:
        from_attributes = True

class DownloadFileIDRequest(BaseModel):
    file_id: UUID

class PropertyInput(BaseModel):
    Country: str = Field(..., description="Location of Country")
    state: str = Field(..., description="State")
    accommodation : Optional[int] = Field(None, description="Accommodation count (optional)")


class UserResponse(BaseModel):
    id: UUID
    firstname: str
    lastname: str
    email: str
    phone: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    street: Optional[str] = None
    billing_city: Optional[str] = None
    state: Optional[str] = None
    post_code: Optional[str] = None
    billing_country: Optional[str] = None
    linkedin: Optional[str] = None
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    x: Optional[str] = None
    photo: Optional[str] = None

    class Config:
        from_attributes = True
