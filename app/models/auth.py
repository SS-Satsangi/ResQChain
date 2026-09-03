from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class CreateAgentRequest(BaseModel):
    admin_username: str
    admin_password: str
    username: str
    password: str