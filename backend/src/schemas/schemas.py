from pydantic import BaseModel, Field, EmailStr
from src.schemas.categorial_db_columns import WorkFormat, EmploymentType, ExperienceLevel
class Job_schema(BaseModel):
    title:str = Field(
        max_length=40,
        min_length=3,
        description="job_title"
    )
    experience:ExperienceLevel
    salary_low:int
    salary_high:int
    employment:EmploymentType
    work_format:WorkFormat
    location_id:int
    description:str

class Company_schema(BaseModel):
    name:str = Field(
        min_length=2,
        max_length=100
    )
    describtion:str= Field(
        min_length=3,
        max_length=1000
    )
    website:str = Field(
        max_length=200
    )
    
class Worker_schema(BaseModel):
    name:str = Field(
        min_length=3,
        max_length=100
    )
    work:str = Field(
        min_length=2
    )
    experience:str = Field(
        ge=0,
        le=50
    )

class Location_schema(BaseModel):
    city:str = Field(
        min_length=2,
        max_length=100
    )
    country:str = Field(
        min_length=2
    )

class Employee_schema(BaseModel):
    role: str = Field(
        min_length=2,
        max_length=100
    )
    worker_id:int

    company_id:int

class JobFilterSchema(BaseModel):
    experience: ExperienceLevel | None = None
    work_format: WorkFormat | None = None
    employment_type: EmploymentType | None = None
    city_id: int | None = None
    salary_low: int | None = None
    salary_high: int | None = None