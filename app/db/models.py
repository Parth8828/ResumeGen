from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    experiences = relationship("Experience", back_populates="user", cascade="all, delete-orphan")
    education = relationship("Education", back_populates="user", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    resume_history = relationship("ResumeHistory", back_populates="user", cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Personal Information
    full_name = Column(String)
    email = Column(String)
    phone = Column(String)
    location = Column(String)
    linkedin = Column(String)
    github = Column(String)
    portfolio = Column(String)
    
    # Professional Summary
    summary = Column(Text)
    
    # Template Selection
    selected_template = Column(String, default="modern_clean")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="profile")

class Experience(Base):
    __tablename__ = "experiences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    title = Column(String)
    company = Column(String)
    location = Column(String)
    start_date = Column(String)  # e.g., "Jan 2020"
    end_date = Column(String)    # e.g., "Present" or "Dec 2022"
    is_current = Column(Boolean, default=False)
    description = Column(Text)
    achievements = Column(JSON)  # List of achievement strings
    
    order = Column(Integer, default=0)  # For ordering
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="experiences")

class Education(Base):
    __tablename__ = "education"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    degree = Column(String)
    institution = Column(String)
    location = Column(String)
    graduation_date = Column(String)  # e.g., "2020" or "May 2020"
    gpa = Column(String)
    
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="education")

class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    category = Column(String)  # e.g., "Programming Languages", "Frameworks"
    skills = Column(JSON)      # List of skill strings
    
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="skills")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    name = Column(String)
    description = Column(Text)
    date = Column(String)  # e.g., "2021" or "Jan 2021"
    url = Column(String)
    technologies = Column(JSON)  # List of technology strings
    
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="projects")

class ResumeHistory(Base):
    __tablename__ = "resume_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    title = Column(String)  # e.g., "Software Engineer Resume - Google"
    template_used = Column(String)  # e.g., "modern_clean"
    file_path = Column(String)  # Path to PDF file
    is_favorite = Column(Boolean, default=False)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="resume_history")
