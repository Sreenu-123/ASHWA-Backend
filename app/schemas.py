from pydantic import BaseModel, EmailStr


# ============================================================
# REGISTER REQUEST
# ============================================================

class RegisterRequest(BaseModel):

    full_name: str

    email: EmailStr

    password: str

    age: int

    riding_experience: str

    riding_level: str

    discipline: str

    primary_goal: str

    horse_name: str


# ============================================================
# LOGIN REQUEST
# ============================================================

class LoginRequest(BaseModel):

    email: EmailStr

    password: str


# ============================================================
# UPDATE PROFILE REQUEST
# ============================================================

class UpdateProfileRequest(BaseModel):

    full_name: str

    email: EmailStr

    age: int

    riding_experience: str

    riding_level: str

    discipline: str

    primary_goal: str

    horse_name: str


# ============================================================
# CREATE RIDE SESSION REQUEST
# ============================================================

class RideSessionCreate(BaseModel):

    horse_name: str

    discipline: str

    duration_seconds: int


# ============================================================
# RIDE SESSION RESPONSE
# ============================================================

class RideSessionResponse(BaseModel):

    id: int

    user_id: int

    horse_name: str

    discipline: str

    duration_seconds: int

    started_at: str

    ended_at: str | None