from sqlalchemy import update, select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from fastapi import Depends, HTTPException
from src.core.dependency import get_db, AsyncSession
from src.api.get_data import get_job
# from api.get_data import get_applications
from src.models.models import Application, Employee, Job, Company, Worker
from src.schemas.categorial_db_columns import ApplicationDecision

# async def hire_employee(
#     reply:str,
#     application_id:int,
#     db:AsyncSession = Depends(get_db),
#     application = Depends(get_applications(application_id))
# ):
#     if reply:
#         stmt = update(Application).where(Application.id == application_id)
#         hired= True
#     else:
#         stmt = update(Application).where(Application.id == application_id)
#         hired= False
    
#     try:
#         await db.execute(stmt)
#         await db.commit()  
#     except Exception as e:
#         raise HTTPException(status_code=401)

#     return hired

async def create_application(
    job_id:int,
    db:AsyncSession,
    worker:Worker,
):
    stmt = select(Job).where(Job.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    application = Application(
        worker_id = worker.id,
        job_id = job_id
    )
    db.add(application)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Already applied")

    return {"message":"Applied successfully"}

async def recruitment(
    decision:ApplicationDecision,
    application_id:int,
    company,
    db:AsyncSession
):
    try:
        company_id = company.id

        stmt = select(Application).join(Job, Application.job_id == Job.id).where(Application.id == application_id).options(selectinload(Application.job)).where(Job.company_id == company_id)
        result = await db.execute(stmt)
        application = result.scalar_one_or_none()

        if not application:
            raise HTTPException(status_code=404, detail="Apllication not found")
        
        if application.status != "pending":
            raise HTTPException(status_code=409, detail="Already recruited")
        
        stmt = update(Application).where(Application.id == application_id).values(status = decision)

        await db.execute(stmt)
        
        if decision == ApplicationDecision.hire:

            
            new_employee  = Employee(
                company_id = company_id,
                worker_id =  application.worker_id,
                role = application.job.title
            )

            db.add(new_employee)
        
        await db.commit()
        return {"msg":"Application rejected"}
    
    except:
        await db.rollback()
        raise
    
async def update_job_opening(
    job_id:int,
    changes,
    company:Company,
    db:AsyncSession
):
    company_id = company.id
    print(f"Company id: {company_id}")
    stmt = select(Job).where(Job.id == job_id).where(Job.company_id == company_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.title = changes.title
    job.description = changes.description
    job.experience = changes.experience
    job.salary_low = changes.salary_low
    job.salary_high = changes.salary_high
    job.employment = changes.employment
    job.work_format = changes.work_format
    job.location_id = changes.location_id
    
    await db.commit()