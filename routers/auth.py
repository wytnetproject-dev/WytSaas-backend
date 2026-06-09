import logging

from fastapi import Request, APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import jwt

from passlib.context import CryptContext

from model import User
from utils.auth import *

import httpx

from db.db import get_db

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Removing missing tools import
# from utils.auth import verify_google_token


from pydantic import BaseModel 


from typing import Literal, Optional



logger = logging.getLogger("wytnet.auth")

# Note: This router is mounted with prefix="/auth" in main.py,
# so endpoints defined here like "/token" become "/auth/token".
router = APIRouter()

tokenExp = timedelta(days=365)

from fastapi.responses import JSONResponse


userRoutes = APIRouter()

userRoutes = APIRouter()


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=15) , role: str = "user"):

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    to_encode.update({"role": role})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/hash")
async def hash_password(h: str):
    return get_password_hash(h)



@router.post("/refresh")
async def refresh_token(request: Request , db:AsyncSession = Depends(get_db)):
    refresh_token = request.cookies.get("refresh")
    auth_token = request.headers.get("Authorization")
    auth_token = auth_token.replace("Bearer ", "")

    print(auth_token, refresh_token)
    
    if not refresh_token or not auth_token:
        raise HTTPException(status_code=403, detail="Invalid request")
    
    if refresh_token == "none" or  auth_token == "none":
        raise HTTPException(status_code=403, detail="Invalid request")
    

    auth_valid = check_token(auth_token)


    if auth_valid is None:
        refresh_valid = check_token(refresh_token)

        if refresh_valid is  None:
            raise HTTPException(status_code=403, detail="Invalid request")
        else:
            # print(refresh_valid)

            new_jwt = create_access_token({"id": refresh_valid["id"]},role=refresh_valid["role"])
            new_refresh = create_access_token({"id": refresh_valid["id"]}, timedelta(weeks=40), role=refresh_valid["role"])
            return {"valid":True, "reset":True, "jwt":new_jwt, "refresh": new_refresh}
    else:
        return {"valid":True,"reset":False}
    




@router.post("/token")
async def generate_token(request: Request,form_data: OAuth2PasswordRequestForm = Depends(),db:AsyncSession = Depends(get_db)):
    try:
        logger.info("TOKEN ENDPOINT HIT: username=%s", form_data.username)
        print("TOKEN ENDPOINT HIT", form_data.username)  # quick debug in dev
        print(form_data.username, form_data.password)
        userres = await db.execute(select(User).filter(User.id==str(form_data.username)))
        user = userres.scalars().first()
        if user is None:
        # If no user found, return 401 Unauthorized
            raise HTTPException(
                status_code=401,
                detail="Failed to authenticate"
            )
        
      

        access_token_expires = timedelta(minutes=10)
        access_token = create_access_token(
            data={"id": str(user.id)}, expires_delta=access_token_expires, role=user.role.__str__()
        )

        refresh_token = create_access_token(
            data={"id": str(user.id)}, expires_delta=timedelta(weeks=10), role=user.role.__str__()
        )

        print(refresh_token)
        print(access_token)
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.exception("Token generation failed")
        print(e)
        raise HTTPException(
            status_code=401,
            detail="Failed to authenticate"
        )


















# Removed missing tools import
# from  utils.auth import add_login_history 


class LoginRequest(BaseModel):
    email: str
    password: str

from fastapi import Response

@router.post("/login")
async def login(
    request: Request, 
    response: Response,
    data: LoginRequest, 
    source : Optional[Literal["web","android","ios"]] = "web",
    db:AsyncSession = Depends(get_db)):

    userres = await db.execute(select(User).filter(User.email==data.email))
    user = userres.scalars().first()
    if user is None:
    # If no user found, return 401 Unauthorized
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=404,
            detail="Invalid password"
        )

    if user.password_hash.startswith("hashed_"):
        user.password_hash = get_password_hash(data.password)
        await db.commit()
    
    access_token_expires = timedelta(minutes=10)
    access_token = create_access_token(
        data={"id": str(user.id)}, expires_delta=access_token_expires, role=user.role.__str__()
    )

    refresh_token = create_access_token(
        data={"id": str(user.id)}, expires_delta=timedelta(weeks=10), role=user.role.__str__()
    )


    # set refresh in cookies

    response.set_cookie(key="refresh", value=refresh_token, httponly=True, max_age=604800)

   


    return {
        "item": {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role
            }
        }
    }






@router.get("/refresh_token")
async def refresh_token(request: Request , db:AsyncSession = Depends(get_db)):
    refresh_token = request.cookies.get("refresh")


    refresh_valid = check_token(refresh_token)

    if refresh_valid is  None:
        raise HTTPException(status_code=403, detail="Invalid request")
    else:
        # print(refresh_valid)

        new_jwt = create_access_token({"id": refresh_valid["id"]})
        new_refresh = create_access_token({"id": refresh_valid["id"]}, timedelta(weeks=40))
        return {"jwt":new_jwt}


class LogoutRequest(BaseModel):
    fcm_token: Optional[str] = None


