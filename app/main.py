from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal
from app import models
from app.schemas import RegisterRequest
from app.auth import hash_password


# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()


# Database session
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# Root endpoint
@app.get("/")
def root():
    return {"message": "ASHWA Backend is running!"}


# Test endpoint
@app.get("/hello")
def hello():
    return {"message": "Hello from ASHWA"}


# Register endpoint
@app.post("/register")
def register(user: RegisterRequest, db: Session = Depends(get_db)):

    # Check whether email already exists
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

    # Create new user
    new_user = models.User(
        full_name=user.full_name,
        email=user.email,
        password_hash=hash_password(user.password),
        age=user.age,
        riding_experience=user.riding_experience,
        riding_level=user.riding_level,
        discipline=user.discipline,
        primary_goal=user.primary_goal,
    )

    # Save user to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user_id": new_user.id,
        "email": new_user.email,
    }