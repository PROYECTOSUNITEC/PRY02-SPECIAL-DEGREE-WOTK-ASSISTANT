from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    is_active: bool
    is_admin: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

class WSTicketResponse(BaseModel):
    ticket_id: str
    expires_at: datetime

class ChatSessionCreate(BaseModel):
    pass

class ChatSessionResponse(BaseModel):
    id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    timestamp: datetime
    sources: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True

class UserPasswordReset(BaseModel):
    new_password: str

class UserRoleUpdate(BaseModel):
    is_admin: bool

