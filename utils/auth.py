from typing import Optional
import uuid
from fastapi import HTTPException, Depends, Request, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime
from jose import jwt
import os
from datetime import datetime, timezone


# IMPORTANT: tokenUrl must match the actual mounted token endpoint path.
# Using a leading "/" prevents Swagger from treating it as a relative URL.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")





SECRET_KEY = os.getenv("NO_AUTH_SECRET")
if not isinstance(SECRET_KEY, (str, bytes)) or not SECRET_KEY:
    raise RuntimeError(
        "Missing/invalid NO_AUTH_SECRET. Set NO_AUTH_SECRET in the environment (or in .env) "
        "to a non-empty string so JWTs can be signed/verified."
    )

ALGORITHM = "HS256"

class UserJWT():
    id: Optional[uuid.UUID] = None
    role: Optional[str] = None



def get_user_token(token: str = Depends(oauth2_scheme)) -> UserJWT:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # print(payload)
        username: str = payload.get("id")
        role: str = payload.get("role")

        if(username is None):
            raise credentials_exception
        
        user = UserJWT()

        user.id = username
        user.role = role


        # print(is_token_valid(payload=payload))

        # if(is_token_valid(payload=payload) is False):
        #     raise credentials_exception
        return user
    except Exception as e:
        print(e)
        raise credentials_exception
    





def get_role(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("role")

        if(username is None):
            return None
        
    except jwt.JWTError:
        raise credentials_exception
    
    return username



    

NOAUTH_SECRET = os.getenv("NO_AUTH_SECRET")

def verify_csrf(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
    )
    print("Hiiii ", token)
    if token == NOAUTH_SECRET:
        return 1
    
    return credentials_exception


def check_token(token: str, check:str = "id" ):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        
        return payload
    except jwt.JWTError:
        
        return None
    

def is_token_valid(payload: dict) -> bool:

    exp_timestamp = payload.get("exp")

    if exp_timestamp is None:
        return False

    # Convert the expiration timestamp to a UTC datetime object
    exp_time_utc = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    current_time_utc = datetime.now(timezone.utc)

    # print(f"Token Expiration Time (UTC): {exp_time_utc}")
    # print(f"Current Time (UTC): {current_time_utc}")

    return exp_time_utc > current_time_utc





from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_db
import httpx


 
    

from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from sqlalchemy.future import select

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False

    try:
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        # Backward compatibility for legacy values saved as "hashed_<password>"
        if hashed_password.startswith("hashed_"):
            return hashed_password[7:] == plain_password
        return False



def get_default_member_role_id() -> str:
    return "f9fabbb2-4d1b-43b2-b192-b34fdaf77e16"

