import uuid
import enum
import os
from sqlalchemy import (
    Column, String, ForeignKey, Boolean, Integer,
    Text, Enum as SQLAlchemyEnum, Float, TIMESTAMP
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID  # ✅ Import essencial
from .database import Base
from .db_types import JSONB_FALLBACK  # ✅ Import seguro para testes/local


class UserRole(str, enum.Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    users = relationship("User", back_populates="tenant")

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    tenant = relationship("Tenant", back_populates="users")
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    full_name = Column(String(255), nullable=False)
    current_goal = Column(String(100))
    user = relationship("User", back_populates="profile")

class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    student_profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    teacher = relationship("Profile", foreign_keys=[teacher_profile_id])
    student = relationship("Profile", foreign_keys=[student_profile_id])

class Question(Base):
    __tablename__ = "questions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    # ALTERADO: Usando o tipo personalizado JSONB_FALLBACK
    options = Column(JSONB_FALLBACK, nullable=False)
    correct_option = Column(String(10), nullable=False)
    subject = Column(String(100), nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True)
    source = Column(String(100))
    vector_id = Column(String(255), unique=True, index=True)

class StudentAnswer(Base):
    __tablename__ = "student_answers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False, index=True)
    selected_option = Column(String(10), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    time_taken_ms = Column(Integer)
    # ALTERADO: Usando o tipo personalizado JSONB_FALLBACK
    ai_analysis = Column(JSONB_FALLBACK)
    answered_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    profile = relationship("Profile")
    question = relationship("Question")

class StudentProficiencyMap(Base):
    __tablename__ = "student_proficiency_map"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    topic = Column(String(100), nullable=False)
    proficiency_score = Column(Float, nullable=False, default=0.0)
    last_updated = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    profile = relationship("Profile")
