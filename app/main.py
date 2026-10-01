from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Header,
    UploadFile,
    File,
)
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import Base, engine, SessionLocal
from app import models

from app.schemas import (
    RegisterRequest,
    LoginRequest,
    UpdateProfileRequest,
    RideSessionCreate,
    RideSessionResponse,
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


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI()


# ============================================================
# PROFILE IMAGE STORAGE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

UPLOADS_DIR = BASE_DIR / "uploads"
PROFILE_IMAGES_DIR = UPLOADS_DIR / "profile_images"

PROFILE_IMAGES_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# SERVE UPLOADED FILES
# ============================================================

app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOADS_DIR)),
    name="uploads"
)


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
        "profile_image": user.profile_image,
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
    user.riding_experience = user_data.riding_experience
    user.riding_level = user_data.riding_level
    user.discipline = user_data.discipline
    user.primary_goal = user_data.primary_goal
    user.horse_name = user_data.horse_name

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
            "riding_experience": user.riding_experience,
            "riding_level": user.riding_level,
            "discipline": user.discipline,
            "primary_goal": user.primary_goal,
            "horse_name": user.horse_name,
            "profile_image": user.profile_image,
        },
    }


# ============================================================
# UPLOAD PROFILE IMAGE
# ============================================================

@app.post("/me/profile-image")
async def upload_profile_image(
    file: UploadFile = File(...),
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

    user_id = int(user_id)

    # --------------------------------------------------------
    # FIND CURRENT USER
    # --------------------------------------------------------

    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # --------------------------------------------------------
    # CHECK FILE TYPE
    # --------------------------------------------------------

    allowed_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG and WEBP images are allowed"
        )

    # --------------------------------------------------------
    # READ FILE
    # --------------------------------------------------------

    file_data = await file.read()

    # --------------------------------------------------------
    # CHECK FILE SIZE
    # Maximum: 5 MB
    # --------------------------------------------------------

    max_file_size = 5 * 1024 * 1024

    if len(file_data) > max_file_size:
        raise HTTPException(
            status_code=400,
            detail="Profile image must be smaller than 5 MB"
        )

    # --------------------------------------------------------
    # CREATE USER-SPECIFIC FILE NAME
    # --------------------------------------------------------

    extension = allowed_types[file.content_type]

    file_name = f"user_{user_id}{extension}"

    file_path = PROFILE_IMAGES_DIR / file_name

    # --------------------------------------------------------
    # DELETE OLD PROFILE IMAGE
    # --------------------------------------------------------

    for old_extension in [".jpg", ".png", ".webp"]:

        old_file = (
            PROFILE_IMAGES_DIR
            / f"user_{user_id}{old_extension}"
        )

        if old_file.exists() and old_file != file_path:
            old_file.unlink()

    # --------------------------------------------------------
    # SAVE IMAGE TO SERVER
    # --------------------------------------------------------

    with open(file_path, "wb") as image_file:
        image_file.write(file_data)

    # --------------------------------------------------------
    # SAVE IMAGE PATH TO DATABASE
    # --------------------------------------------------------

    image_url = (
        f"/uploads/profile_images/{file_name}"
    )

    user.profile_image = image_url

    try:
        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()

        # Remove uploaded file if DB update fails
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="Unable to save profile image"
        )

    # --------------------------------------------------------
    # SUCCESS RESPONSE
    # --------------------------------------------------------

    return {
        "message": "Profile image uploaded successfully",
        "profile_image": user.profile_image,
    }


# ============================================================
# CREATE RIDE SESSION
# ============================================================

@app.post(
    "/rides",
    response_model=RideSessionResponse
)
def create_ride_session(
    ride_data: RideSessionCreate,
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
    # VALIDATE DURATION
    # --------------------------------------------------------

    if ride_data.duration_seconds < 0:
        raise HTTPException(
            status_code=400,
            detail="Duration cannot be negative"
        )

    # --------------------------------------------------------
    # CREATE RIDE TIME
    # --------------------------------------------------------

    ended_at = datetime.now(timezone.utc)

    started_at = (
        ended_at
        - timedelta(
            seconds=ride_data.duration_seconds
        )
    )

    # --------------------------------------------------------
    # CREATE RIDE SESSION
    # --------------------------------------------------------

    new_ride = models.RideSession(
        user_id=user.id,
        horse_name=ride_data.horse_name,
        discipline=ride_data.discipline,
        duration_seconds=ride_data.duration_seconds,
        started_at=started_at,
        ended_at=ended_at,
    )

    # --------------------------------------------------------
    # SAVE RIDE TO DATABASE
    # --------------------------------------------------------

    try:
        db.add(new_ride)
        db.commit()
        db.refresh(new_ride)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail="Unable to save ride session"
        )

    # --------------------------------------------------------
    # RIDE SUCCESS RESPONSE
    # --------------------------------------------------------

    return {
        "id": new_ride.id,
        "user_id": new_ride.user_id,
        "horse_name": new_ride.horse_name,
        "discipline": new_ride.discipline,
        "duration_seconds": new_ride.duration_seconds,
        "started_at": new_ride.started_at.isoformat(),
        "ended_at": (
            new_ride.ended_at.isoformat()
            if new_ride.ended_at
            else None
        ),
    }


# ============================================================
# GET MY RIDE HISTORY
# ============================================================

@app.get(
    "/rides",
    response_model=list[RideSessionResponse]
)
def get_my_rides(
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
    # FIND USER
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
    # GET USER'S RIDES
    # --------------------------------------------------------

    rides = (
        db.query(models.RideSession)
        .filter(
            models.RideSession.user_id == user.id
        )
        .order_by(
            models.RideSession.started_at.desc()
        )
        .all()
    )

    # --------------------------------------------------------
    # RETURN RIDE HISTORY
    # --------------------------------------------------------

    return [
        {
            "id": ride.id,
            "user_id": ride.user_id,
            "horse_name": ride.horse_name,
            "discipline": ride.discipline,
            "duration_seconds": ride.duration_seconds,
            "started_at": ride.started_at.isoformat(),
            "ended_at": (
                ride.ended_at.isoformat()
                if ride.ended_at
                else None
            ),
        }
        for ride in rides
    ]