from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import Base, engine, SessionLocal
from app import models
from app.schemas import (
    RegisterRequest,
    LoginRequest,
    UpdateProfileRequest,
)
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token,
)


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(bind=engine)

app = FastAPI()


# ============================================================
# DATABASE SESSION
# ============================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "ASHWA Backend is running!"
    }


# ============================================================
# TEST ENDPOINT
# ============================================================

@app.get("/hello")
def hello():
    return {
        "message": "Hello from ASHWA"
    }


# ============================================================
# REGISTER ENDPOINT
# ============================================================

@app.post("/register")
def register(
    user: RegisterRequest,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # CHECK WHETHER EMAIL ALREADY EXISTS
    # --------------------------------------------------------

    existing_user = (
        db.query(models.User)
        .filter(models.User.email == user.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # --------------------------------------------------------
    # CREATE NEW USER
    # --------------------------------------------------------

    new_user = models.User(
        full_name=user.full_name,
        email=user.email,
        password_hash=hash_password(user.password),
        age=user.age,
        riding_experience=user.riding_experience,
        riding_level=user.riding_level,
        discipline=user.discipline,
        primary_goal=user.primary_goal,
        horse_name=user.horse_name,
    )

    # --------------------------------------------------------
    # SAVE USER TO DATABASE
    # --------------------------------------------------------

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # --------------------------------------------------------
    # REGISTER SUCCESS RESPONSE
    # --------------------------------------------------------

    return {
        "message": "User registered successfully",
        "user_id": new_user.id,
        "email": new_user.email,
        "horse_name": new_user.horse_name,
    }


# ============================================================
# LOGIN ENDPOINT
# ============================================================

@app.post("/login")
def login(
    user: LoginRequest,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # FIND USER BY EMAIL
    # --------------------------------------------------------

    existing_user = (
        db.query(models.User)
        .filter(models.User.email == user.email)
        .first()
    )

    # --------------------------------------------------------
    # USER NOT FOUND
    # --------------------------------------------------------

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # --------------------------------------------------------
    # VERIFY PASSWORD
    # --------------------------------------------------------

    password_correct = verify_password(
        user.password,
        existing_user.password_hash
    )

    if not password_correct:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # --------------------------------------------------------
    # CREATE JWT ACCESS TOKEN
    # --------------------------------------------------------

    access_token = create_access_token(
        data={
            "sub": str(existing_user.id),
            "email": existing_user.email,
        }
    )

    # --------------------------------------------------------
    # LOGIN SUCCESS RESPONSE
    # --------------------------------------------------------

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": existing_user.id,
        "email": existing_user.email,
    }


# ============================================================
# GET CURRENT USER
# ============================================================

@app.get("/me")
def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # CHECK AUTHORIZATION HEADER
    # --------------------------------------------------------

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing"
        )

    # --------------------------------------------------------
    # CHECK BEARER FORMAT
    # --------------------------------------------------------

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format"
        )

    # --------------------------------------------------------
    # EXTRACT TOKEN
    # --------------------------------------------------------

    token = authorization.split(" ")[1]

    # --------------------------------------------------------
    # VERIFY JWT TOKEN
    # --------------------------------------------------------

    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    # --------------------------------------------------------
    # GET USER ID FROM TOKEN
    # --------------------------------------------------------

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload"
        )

    # --------------------------------------------------------
    # FIND USER IN DATABASE
    # --------------------------------------------------------

    user = (
        db.query(models.User)
        .filter(models.User.id == int(user_id))
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # --------------------------------------------------------
    # RETURN CURRENT USER
    # --------------------------------------------------------

    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "age": user.age,
        "riding_experience": user.riding_experience,
        "riding_level": user.riding_level,
        "discipline": user.discipline,
        "primary_goal": user.primary_goal,
        "horse_name": user.horse_name,
    }


# ============================================================
# UPDATE CURRENT USER PROFILE
# ============================================================

@app.put("/me")
def update_current_user(
    user_data: UpdateProfileRequest,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # CHECK AUTHORIZATION HEADER
    # --------------------------------------------------------

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing"
        )

    # --------------------------------------------------------
    # CHECK BEARER FORMAT
    # --------------------------------------------------------

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format"
        )

    # --------------------------------------------------------
    # EXTRACT TOKEN
    # --------------------------------------------------------

    token = authorization.split(" ")[1]

    # --------------------------------------------------------
    # VERIFY JWT TOKEN
    # --------------------------------------------------------

    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    # --------------------------------------------------------
    # GET USER ID FROM TOKEN
    # --------------------------------------------------------

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload"
        )

    # --------------------------------------------------------
    # FIND CURRENT USER
    # --------------------------------------------------------

    user = (
        db.query(models.User)
        .filter(models.User.id == int(user_id))
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # --------------------------------------------------------
    # CHECK WHETHER NEW EMAIL BELONGS TO ANOTHER USER
    # --------------------------------------------------------

    existing_email = (
        db.query(models.User)
        .filter(
            models.User.email == user_data.email,
            models.User.id != user.id
        )
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # --------------------------------------------------------
    # UPDATE USER DATA
    # --------------------------------------------------------

    user.full_name = user_data.full_name

    user.email = user_data.email

    user.age = user_data.age

    user.riding_experience = (
        user_data.riding_experience
    )

    user.riding_level = (
        user_data.riding_level
    )

    user.discipline = (
        user_data.discipline
    )

    user.primary_goal = (
        user_data.primary_goal
    )

    user.horse_name = (
        user_data.horse_name
    )

    # --------------------------------------------------------
    # SAVE CHANGES
    # --------------------------------------------------------

    try:
        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail="Unable to update profile"
        )

    # --------------------------------------------------------
    # UPDATE SUCCESS RESPONSE
    # --------------------------------------------------------

    return {
        "message": "Profile updated successfully",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "age": user.age,
            "riding_experience":
                user.riding_experience,
            "riding_level":
                user.riding_level,
            "discipline":
                user.discipline,
            "primary_goal":
                user.primary_goal,
            "horse_name":
                user.horse_name,
        },
    }