import os

from sqlalchemy import (
    create_engine,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from datetime import datetime

from enums.ConversionStatus import ConversionStatus

engine = create_engine(os.environ.get("DATABASE_URL"))
session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(20))
    email = Column(String(40))
    password = Column(String(50))


class Video(Base):
    __tablename__ = "video"

    conversion_extension = Column(String(255), nullable=False)
    converted_path = Column(String(255), nullable=False)
    id = Column(Integer, primary_key=True)
    original_path = Column(String(255), nullable=False)
    status = Column(Enum(ConversionStatus), default=ConversionStatus.PENDING)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
