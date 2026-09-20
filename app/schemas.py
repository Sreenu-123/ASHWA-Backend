from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    age: int
    riding_experience: str
    riding_level: str
    discipline: str
    primary_goal: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str