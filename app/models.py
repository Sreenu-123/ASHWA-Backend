from sqlalchemy import Column, Integer, String
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)

    age = Column(Integer, nullable=True)
    riding_experience = Column(String, nullable=True)
    riding_level = Column(String, nullable=True)
    discipline = Column(String, nullable=True)
    primary_goal = Column(String, nullable=True)

    horse_name = Column(String, nullable=True)
    profile_image = Column(String, nullable=True)