from src.config import async_session_factory, AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.models.models import Worker, Company, Job, Employee, Application
from src.core.security import JWTError, auth_config, jwt
from fastapi import HTTPException, Cookie, Depends
from dotenv import load_dotenv
import os
import json
load_dotenv()

ALGORITHM  = os.getenv("ALGORITHM")

async def get_db():
    async with async_session_factory() as session:
        yield session

async def get_token_payload(access_token:str = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(
            access_token,
            auth_config.JWT_SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        # print(access_token)
        # print(payload)
        return payload
    except JWTError:
         raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(
        db: AsyncSession = Depends(get_db),
        payload = Depends(get_token_payload)
    ):
    data = json.loads(payload.get("sub"))
    # print(data)
    user_id = data.get("id")
    role = data.get("role")

    if not user_id or not role:
        raise HTTPException(status_code=401, detail="Invalid payload")
    
    table = {
        "worker": Worker,
        "company": Company
    }.get(role)

    if not table:
        raise HTTPException(status_code=401, detail="invalid role")
    
    stmt = select(table).filter(table.id == int(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    

    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    return {"user":user, "role":role}

def require_role(required_role:str):
    async def role_checker(current=Depends(get_current_user)):
        if current["role"] != required_role:
            raise HTTPException(status_code=403, detail=f"Only {required_role}s allowed")

        return current["user"]
    
    return role_checker

# def require_employement():
#     async def role_checker(current = Depends(get_current_user)):
#         if current["role"] !=



async def get_application(
    application_id :int,
    db:AsyncSession
):
    stmt = select(Application).where(Application.id == application_id).options(selectinload(Application.job).selectinload(Job.company))
    result = await db.execute(stmt)
    application = result.scalar_one_or_none()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return application

async def verify_employee(
    required_role:str,
    company_id:int,
    db :AsyncSession,
    current_user = Depends(get_current_user)
):
    if current_user["role"] == "worker":
        user_id = current_user["user"].id

        stmt  = select(Employee).where(Employee.worker_id == user_id and Employee.role == required_role and Employee.company_id == company_id)

        res= await db.execute(stmt)
        employee = res.scalar_one_or_none()

        if not employee:
            raise HTTPException(status_code=404, detail="Employee does not exist")
        
        return employee