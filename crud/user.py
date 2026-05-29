from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from model import User
from schemas.user import UserCreate, UserUpdate
from utils.auth import get_password_hash

# Create a new user
async def create_user(db: AsyncSession, user: UserCreate) -> User:
    password_hash = get_password_hash(user.password)
    
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        password_hash=password_hash,
        role=user.role,
        is_active=user.is_active
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# Get a single user by ID
async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

# Get a user by username
async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()

# Get a user by email
async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

# List multiple users with limit and offset
async def list_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    result = await db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())

# Update a user's details
async def update_user(db: AsyncSession, user_id: UUID, user_update: UserUpdate) -> Optional[User]:
    # Extract update data, skipping unset fields
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Handle password hashing if the password is being updated
    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
    
    if not update_data:
        return await get_user_by_id(db, user_id)

    # Perform the update
    query = update(User).where(User.id == user_id).values(**update_data)
    await db.execute(query)
    await db.commit()
    
    return await get_user_by_id(db, user_id)

# Delete a user
async def delete_user(db: AsyncSession, user_id: UUID) -> bool:
    query = delete(User).where(User.id == user_id)
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0
