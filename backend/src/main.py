from fastapi import FastAPI, Depends, HTTPException, Response, Query
import uvicorn
from src.core.dependency import get_db, get_current_user, require_role,  get_application, verify_employee
from src.config import AsyncSession
from src.core.security import authenticate_user, set_cookie
from src.schemas.schemas import Company_schema, Worker_schema, Job_schema, Employee_schema, JobFilterSchema
from src.schemas.registration import CreateCompany, CreateWorker
from src.schemas.login import LoginCompany, LoginWorker
from src.models.models import Worker, Company, Job, Application, Employee
from src.core.security import password_hasher
from src.api.get_data import get_jobs, get_applications, get_cities ,get_job, filter_jobs , get_applications_company, get_application
from src.api.post_update_data import recruitment, update_job_opening, create_application
from fastapi.middleware.cors import CORSMiddleware
import os

app =  FastAPI()
web_url = os.getenv("web_url")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[web_url],
    allow_credentials=True,                  
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
def greetings():
    return "App running"

@app.get("/cities")
async def cites_list(
    db:AsyncSession = Depends(get_db)
):
    return await get_cities(db)

@app.post("/register/worker")
async def register_worker(
    worker:CreateWorker,
    db:AsyncSession = Depends(get_db)
):
    new_worker=Worker(
        name = worker.name,
        work =worker.work,
        experience = worker.experience,
        email = worker.email,
        role = "worker",
        hashed_password = password_hasher(worker.password)
    )
    db.add(new_worker)
    await db.commit()
    await db.refresh(new_worker)
    return {"Worker created":new_worker.name,"worker_id":new_worker.id}

@app.post("/register/company")
async def register_company(
    company:CreateCompany,
    db:AsyncSession = Depends(get_db)
):
    new_company=Company(
        name = company.name,
        description =company.description,
        website = company.website,
        role = "company",
        email = company.email,
        hashed_password = password_hasher(company.password)
    )
    db.add(new_company)
    await db.commit()
    await db.refresh(new_company)
    return {"Company created":new_company.name,"company_id":new_company.id}

@app.post("/login/worker")
async def login(
    credential:LoginWorker,
    response:Response,
    db:AsyncSession = Depends(get_db)
):
    access_token  = await authenticate_user(credential=credential,db = db,table=Worker)
    if not access_token:
        raise HTTPException(status_code=401,detail="invalid credentials")
    set_cookie(response,access_token=access_token)
    return {"msg":"logged in"}

@app.post("/login/company")
async def login(
    credential:LoginCompany,
    response:Response,
    db:AsyncSession = Depends(get_db)
):
    access_token  = await authenticate_user(credential=credential,db = db,table=Company)
    if not access_token:
        raise HTTPException(status_code=401,detail="invalid credentials")
    set_cookie(access_token=access_token,response=response)
    return {"msg":"logged in"}

@app.get("/profile")
async def get_profile(
    current_user  = Depends(get_current_user)
):
    return {
        "name":current_user["user"].name,
        "email":current_user["user"].email,
        "role":current_user["role"]
    }

@app.get("/logout")
def logout(response:Response): #dependencies = Depends(get_current_user)
    response.delete_cookie(key="access_token")
    return {"message":"logged out"}

@app.post("/jobs/add")
async def add_job(
    job:Job_schema,
    db:AsyncSession = Depends(get_db),
    current_user = Depends(require_role("company")),
):
    new_job = Job(
        title = job.title,
        experience = job.experience,
        company_id = current_user.id,
        status = True,
        salary_low = job.salary_low,
        salary_high = job.salary_high,
        employment = job.employment,
        work_format = job.work_format,
        location_id = job.location_id,
        description = job.description
    )
    db.add(new_job)
    await db.commit()   
    await db.refresh(new_job)

    return {new_job.id: new_job.title}

@app.get("/jobs")
async def jobs(
    page: int = Query(1, ge=1),
    size: int = Query(10,ge=1,le=100),
    db:AsyncSession = Depends(get_db)
):
    offset = (page-1)*size
    jobs = await get_jobs(offset =offset,limit = size,page =page,db=db)
    return jobs
    
@app.post("/jobs/filtered")
async def get_filtered_jobs(
    filter:JobFilterSchema,
    db:AsyncSession = Depends(get_db)
):
    jobs = await filter_jobs(filter, db)
    return jobs

@app.get("/jobs/{job_id}")
async def get_job_info(
    job_id:int,
    db:AsyncSession = Depends(get_db)
):
    job = await get_job(job_id = job_id,db= db)
    return job

@app.put("company/jobs/{job_id}")
async def update_job(
    job_id:int,
    changes:Job_schema,
    db:AsyncSession = Depends(get_db),
    company = Depends(require_role("company"))
):
    await update_job_opening(job_id = job_id, changes = changes, db=db, company= company)

    return {"message":"updated"}

@app.post("/jobs/{job_id}/application")
async def apply_to_job(
    job_id:int,
    db:AsyncSession = Depends(get_db),
    worker = Depends(require_role("worker"))
):
    response = await create_application(job_id = job_id,db=db ,worker=worker)
    return response

@app.get("/company/jobs")
async def get_job_openings_of_company(
    page: int = Query(1, ge=1),
    size: int = Query(10,ge=1,le=100),
    db:AsyncSession = Depends(get_db),
    company = Depends(require_role("company"))
):
    company_id = company.id
    offset = (page-1)*size
    jobs = await get_jobs(offset =offset,limit = size,page =page,db=db, company_id=company_id)
    
    return jobs


@app.post("/company/application/{application_id}")
async def process_application(
    application_id:int,
    decision:str,
    db:AsyncSession = Depends(get_db),
    company = Depends(require_role("company"))
):
    response = await recruitment(
        application_id=application_id,
        decision=decision,
        company=company,
        db = db
    )
    return response

@app.get("/worker/applications")
async def show_applications(
    db:AsyncSession = Depends(get_db),
    worker = Depends(require_role("worker"))
):
    applications= await get_applications(db= db, worker_id=worker.id)
    return applications

@app.get("/company/applications")
async def get_company_applications(
    page: int = Query(1, ge=1),
    size: int = Query(10,ge=1,le=100),
    db:AsyncSession = Depends(get_db),
    company = Depends(require_role("company"))
):
    company_id = company.id
    offset = (page-1)*size
    applications = await get_applications_company(
        db=db,
        page=page,
        limit=size,
        offset= offset,
        company= company
    )
    return applications

@app.get("/company/application/{application_id}")
async def show_application(
    application_id:int,
    db:AsyncSession = Depends(get_db),
    company = Depends(require_role("company"))
):
    application = await get_application(application_id=application_id, db=db, company=company)

    return application

# @app.post("/create_employee")
# async def create_employee(
#     employee : Employee_schema,
#     db:AsyncSession = Depends(get_db)
# ):
#     new_employee = Employee(
#         company_id = employee.company_id,
#         worker_id = employee.worker_id,
#         role = employee.role
#     )
#     db.add(new_employee)
#     await db.commit()
#     await db.refresh(new_employee)

#     return {"New epmloyee":new_employee.id}

if __name__ =="__main__":
    uvicorn.run("main:app",reload=True)
