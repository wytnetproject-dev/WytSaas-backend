from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_db
from schemas.user import UserCreate, UserUpdate, UserResponse
from schemas.response import APIResponse
from crud.user import (
    create_user, get_user_by_id, get_user_by_username,
    get_user_by_email, list_users, update_user, delete_user
)
from utils.auth import UserJWT, get_user_token

router = APIRouter(prefix="/users", tags=["Users"])

# Create a new user
@router.post("/", response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def create_new_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if a user with the same username exists
    existing_username = await get_user_by_username(db, user.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if a user with the same email exists
    existing_email = await get_user_by_email(db, user.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    created_user = await create_user(db, user)
    return APIResponse[UserResponse](
        item=created_user,
        detail="User created successfully"
    )

# Retrieve a specific user by ID
@router.get("/{user_id}", response_model=APIResponse[UserResponse])
async def retrieve_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return APIResponse[UserResponse](
        item=db_user,
        detail="User retrieved successfully"
    )

# List all users with optional pagination
@router.get("/", response_model=APIResponse[List[UserResponse]])
async def list_all_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db),user: UserJWT = Depends(get_user_token)):
    users = await list_users(db, skip=skip, limit=limit)
    return APIResponse[List[UserResponse]](
        items=users,
        detail="Users retrieved successfully",
        itemCount=len(users)
    )

# Update an existing user's information
@router.patch("/{user_id}", response_model=APIResponse[UserResponse])
async def modify_user(user_id: UUID, user_update: UserUpdate, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Optional: Validation for new username/email (similar to creation) if provided
    if user_update.username:
        existing_username = await get_user_by_username(db, user_update.username)
        if existing_username and existing_username.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

    updated_user = await update_user(db, user_id, user_update)
    return APIResponse[UserResponse](
        item=updated_user,
        detail="User updated successfully"
    )

# Delete a user account
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    # 204 No Content doesn't require a return body
    return None
