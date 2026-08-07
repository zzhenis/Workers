from sqlalchemy import select, func, join
from sqlalchemy.orm import selectinload, joinedload
from src.models.models import Job, Application, Location
from src.core.dependency import get_db, AsyncSession
from fastapi import Depends, HTTPException
from src.schemas.schemas import JobFilterSchema
from typing import Optional

async def get_jobs(
    offset:int,
    limit:int,
    page:int,
    db:AsyncSession,
    company_id: Optional[int]= None
):
    stmt = select(Job).order_by(Job.id).offset(offset).limit(limit).options(selectinload(Job.company), selectinload(Job.location))

    if company_id:
        stmt = stmt.where(company_id == company_id)

    result = await db.execute(stmt)
    jobs = result.scalars().all()

    if not jobs:
        return "No jobs yet"
    
    total_query = select(func.count()).select_from(Job)
    total = await db.scalar(total_query)
    
    return {
        "page": page,
        "size": limit,
        "total": total,
        "pages": (total + limit - 1)//limit,
        "data": [
            {
                "job_id":job.id,
                "job_title":job.title,
                "experience":job.experience,
                "company_name":job.company.name,
                "work_format":job.work_format,
                "employment":job.employment,
                "salary_low":job.salary_low,
                "salary_high":job.salary_high,
                "salary_currency":job.currency,
                "job_description":job.description,
                "location":job.location.city,
                "company_name":job.company.name,
                "company_id":job.company_id,
                "job_status":job.status
            }
            for job in jobs
        ] 
    }
async def get_applications(
    worker_id:int,
    db:AsyncSession
):
    stmt = (select(Application)
        .where(Application.worker_id == worker_id)
        .options(
            selectinload(Application.worker),
            selectinload(Application.job).selectinload(Job.company)
            )
        )
    result = await db.execute(stmt)
    applications = result.scalars().all()

    if not result:
        raise HTTPException(status_code=404, detail="Applications not found")
    
    return [
        {
            "title":application.job.title,
            "status":application.status,
            "company":application.job.company.name
        } for application in applications
    ]

async def get_applications_company(
    db,limit, offset, page, company
):
    company_id = company.id
    stmt = select(Application).join(Job, Application.job_id == Job.id).where(Job.company_id == company_id).where(Application.status == "pending").offset(offset).limit(limit).options(selectinload(Application.job), selectinload(Application.worker))
    result = await db.execute(stmt)
    applications = result.scalars().all()
    if not applications:
        raise HTTPException(status_code=404, detail="No applications")
    total_query = select(func.count()).select_from(Application)
    total = await db.scalar(total_query)

    return [
        {
            "page":page,
            "size":limit,
            "total":total,
            "pages": (total + limit - 1)//limit,
            "application_id":app.id,
            "application_title":app.job.title,
            "applicant":app.worker.name
        } for app in applications
    ]

async def get_application(
    application_id:int,
    db,
    company
):
    company_id = company.id
    stmt = select(Application).join(Job, Application.job_id == Job.id).where(Application.id == application_id).where(Job.company_id == company_id).options(selectinload(Application.worker), selectinload(Application.job))
    result = await db.execute(stmt)
    application = result.scalar_one_or_none()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return {
        "application_title":application.job.title,
        "applicant":application.worker.name,
        "applicant_id":application.worker.id
    }


async def get_cities(db):
    stmt = select(Location)
    result = await db.execute(stmt)
    cites = result.scalars().all()
    return [
        {
            "city_id":city.id,
            "city_name":city.city
        } for city in cites
    ]

async def get_job(job_id:int, db):
    stmt = select(Job).where(Job.id == job_id).options(selectinload(Job.company), selectinload(Job.location))
    result = await db.execute(stmt)
    if not result:
        raise HTTPException(status_code=404, detail="Job opening not found")
    job = result.scalar_one_or_none()

    return {
            "job_id":job.id,
            "job_title":job.title,
            "experience":job.experience,
            "work_format":job.work_format,
            "employment":job.employment,
            "salary_low":job.salary_low,
            "salary_high":job.salary_high,
            "salary_currency":job.currency,
            "job_description":job.description,
            "location":job.location.city,
            "company_name":job.company.name,
            "company_id":job.company_id
        }

async def filter_jobs(filter:JobFilterSchema,db):
    query = select(Job).options(selectinload(Job.location), selectinload(Job.company))

    if filter.experience:
        query = query.where(Job.experience == filter.experience)

    if filter.employment_type:
        query = query.where(Job.employment == filter.employment_type)

    if filter.work_format:
        query = query.where(Job.work_format == filter.work_format)

    if filter.city_id:
        query = query.where(Job.location_id == filter.city_id)
    
    if filter.salary_low:
        query = query.where(Job.salary_low >= filter.salary_low)

    if filter.salary_high:
        query = query.where(Job.salary_high <= filter.salary_high)
    
    
    result = await db.execute(query)
    jobs = result.scalars().all()

    return [
        {
            "job_id":job.id,
            "job_title":job.title,
            "experience":job.experience,
            "work_format":job.work_format,
            "employment":job.employment,
            "salary_low":job.salary_low,
            "salary_high":job.salary_high,
            "salary_currency":job.currency,
            "job_description":job.description,
            "location":job.location.city,
            "company_name":job.company.name,
            "company_id":job.company_id
        } for job in jobs
    ]

