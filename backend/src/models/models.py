from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, Boolean, func, text , UniqueConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.config import Base
from datetime import datetime
from src.schemas.categorial_db_columns import ExperienceLevel, WorkFormat, EmploymentType

class Location(Base):
    __tablename__="locations"

    id :Mapped[int]= mapped_column(
        primary_key=True,
        autoincrement=True
    )
    city :Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True
    )
    country :Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    jobs: Mapped[list["Job"]] = relationship(
        back_populates="location"
    )

class Company(Base):
    __tablename__="companies"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    name:Mapped[str]= mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    description:Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    website:Mapped[str] = mapped_column(
        String(200),
        unique=True,
        nullable=False
    )
    email:Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    hashed_password: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    role:Mapped[str] = mapped_column(
        String(10),
        nullable=True,
        default="user",
        server_default=text("'company'")
    )
    jobs: Mapped[list["Job"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan"
    )
    employees :Mapped[list["Employee"]] = relationship(
        back_populates="company"
    )
    
class Skills(Base):
    __tablename__="skills"
    id:Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    name : Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True
    )

class Job(Base):
    __tablename__="jobs"

    id :Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        index=True
    )

    title:Mapped[str]= mapped_column(
        String(100),
        nullable=False
    )
    experience:Mapped[ExperienceLevel] = mapped_column(
        Enum(ExperienceLevel),
        server_default=text("'junior'"),
        nullable=False
    )
    status: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default="True",
        server_default=text("'true'")
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id")
    )
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=func.now()
    )
    salary_low:Mapped[int] = mapped_column(
        nullable=True,
    )
    salary_high:Mapped[int] = mapped_column(
        nullable=True,
    )
    currency :Mapped[str] = mapped_column(
        nullable=False,
        server_default=text("'tenge'")
    )
    employment:Mapped[EmploymentType] = mapped_column(
        Enum(EmploymentType),
        server_default=text("'full_time'"),
        nullable=False
    )
    work_format :Mapped[WorkFormat] = mapped_column(
        Enum(WorkFormat),
        nullable=False,
        server_default=text("'office'")
    )
    description:Mapped[str]  =mapped_column(
        Text,
        nullable =True
    )
    company: Mapped[Company] = relationship(
        back_populates="jobs"
    )
    applications:Mapped[list["Application"]] = relationship(
        back_populates="job"
    )
    location: Mapped[Location] = relationship(
        back_populates="jobs"
    )
class Worker(Base):
    __tablename__="workers"

    id :Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    name :Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    work: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    experience: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )
    email:Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    hashed_password: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    role:Mapped[str] = mapped_column(
        String(10),
        nullable=True,
        default="user",
        server_default=text("'worker'")
    )
    # skills: Mapped[list[Skills_table]] = relationship(
    #     back_populates="worker"
    # )
    applications:Mapped[list["Application"]] = relationship(
        back_populates="worker"
    )
    employment:Mapped[list["Employee"]] = relationship(
        back_populates="worker"
    )

class JobSkills(Base):
    __tablename__="job_skills"

    job_id :Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        primary_key=True
    )
    skill_id :Mapped[int] = mapped_column(
        ForeignKey("skills.id"),
        primary_key=True
    )


class Application(Base):
    __tablename__="applications"

    id:Mapped[int] = mapped_column(
        primary_key=True,
        nullable=False
    )
    worker_id: Mapped[int] = mapped_column(
        ForeignKey("workers.id"),
        nullable=False
    )
    job_id :Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        server_default=text("'pending'"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=func.now()
    )
    worker = relationship("Worker", back_populates="applications")

    job = relationship("Job", back_populates="applications")

    __table_args__ = (
        UniqueConstraint("worker_id", "job_id", name = "uix_worker_job"),
    )

class Employee(Base):
    __tablename__="employees"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        nullable=False,
        autoincrement=True
    )

    worker_id : Mapped[int]  =mapped_column(
        ForeignKey("workers.id")
    )
    company_id  :Mapped[int] = mapped_column(
        ForeignKey("companies.id")
    )
    role :Mapped[str]  = mapped_column(
        String(100),
        nullable=False
    )
    hired_at : Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now()
    )

    worker:Mapped[Worker] = relationship(
        back_populates="employment"
    )
    company:Mapped[Company] = relationship(
        back_populates="employees"
    )