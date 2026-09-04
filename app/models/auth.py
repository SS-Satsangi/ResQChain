from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class CreateAgentRequest(BaseModel):
    admin_username: str
    admin_password: str
    username: str
    password: str

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class UserUpdateRequest(BaseModel):
    username: str | None = None
    password: str | None = None
    role: str | None = None