from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
import asyncio
from sqlalchemy import select
from authx import AuthXConfig, AuthX
import os
from fastapi import Response
import json
from dotenv import load_dotenv
from jose import  JWTError ,jwt

load_dotenv()

JWT_KEY = os.getenv("JWT_SECRET_KEY")

auth_config = AuthXConfig(
    JWT_SECRET_KEY=JWT_KEY,
    JWT_ACCESS_COOKIE_NAME="access_token",
    JWT_TOKEN_LOCATION=["headers"]
)
auth  = AuthX(config=auth_config)

hasher = PasswordHasher()
def password_hasher(password:str)->str:
    return hasher.hash(password)

async def authenticate_user(credential,db,table):
    stmt = select(table).where(table.email  == credential.email)
    result  = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        return None

    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(
            None,
            hasher.verify,
            user.hashed_password,
            credential.password
        )
    except (VerifyMismatchError, InvalidHashError):
        return None
    token_data = {"id":user.id,"role":user.role}
    access_token = auth.create_access_token(uid =json.dumps(token_data))
    return access_token

def set_cookie(response:Response,access_token):
    response.set_cookie(
        key="access_token",
        value= access_token,
        httponly=True,
        secure=False,
        # samesite="none",
        max_age=900
    )
    return {"msg":"logged in"}