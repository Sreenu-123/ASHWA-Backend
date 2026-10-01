from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


# ============================================================
# USER MODEL
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    full_name = Column(
        String,
        nullable=False
    )

    email = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = Column(
        String,
        nullable=False
    )

    age = Column(
        Integer,
        nullable=True
    )

    riding_experience = Column(
        String,
        nullable=True
    )

    riding_level = Column(
        String,
        nullable=True
    )

    discipline = Column(
        String,
        nullable=True
    )

    primary_goal = Column(
        String,
        nullable=True
    )

    horse_name = Column(
        String,
        nullable=True
    )

    profile_image = Column(
        String,
        nullable=True
    )

    # --------------------------------------------------------
    # RELATIONSHIP
    # --------------------------------------------------------

    rides = relationship(
        "RideSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )


# ============================================================
# RIDE SESSION MODEL
# ============================================================

class RideSession(Base):
    __tablename__ = "ride_sessions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # --------------------------------------------------------
    # RIDE DETAILS
    # --------------------------------------------------------

    horse_name = Column(
        String,
        nullable=False
    )

    discipline = Column(
        String,
        nullable=False
    )

    duration_seconds = Column(
        Integer,
        nullable=False,
        default=0
    )

    # --------------------------------------------------------
    # RIDE TIME
    # --------------------------------------------------------

    started_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    ended_at = Column(
        DateTime,
        nullable=True
    )

    # --------------------------------------------------------
    # RELATIONSHIP
    # --------------------------------------------------------

    user = relationship(
        "User",
        back_populates="rides"
    )