from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from db.db import get_db
from schemas.developer_bank_account import (
    DeveloperBankAccountCreate,
    DeveloperBankAccountUpdate,
    DeveloperBankAccountResponse,
)
from schemas.response import APIResponse
from crud.developer_bank_account import (
    get_developer_bank_account_by_user_id,
    create_developer_bank_account,
    update_developer_bank_account,
    delete_developer_bank_account,
)
from utils.auth import UserJWT, get_user_token

router = APIRouter(prefix="/developer/bank-account", tags=["Developer Bank Accounts"])

def verify_developer_role(current_user: UserJWT):
    if current_user.role not in ["developer", "wytsaas_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Developer role required."
        )

@router.get("/", response_model=APIResponse[DeveloperBankAccountResponse])
async def get_bank_account(
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    verify_developer_role(current_user)
    user_id = UUID(str(current_user.id))
    db_account = await get_developer_bank_account_by_user_id(db, user_id)
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer bank account details not found."
        )
    return APIResponse[DeveloperBankAccountResponse](
        item=db_account,
        detail="Bank account details retrieved successfully"
    )

@router.post("/", response_model=APIResponse[DeveloperBankAccountResponse], status_code=status.HTTP_201_CREATED)
async def create_bank_account(
    account: DeveloperBankAccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    verify_developer_role(current_user)
    user_id = UUID(str(current_user.id))
    
    # Check if entry already exists
    existing_account = await get_developer_bank_account_by_user_id(db, user_id)
    if existing_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Developer bank account details already exist."
        )
        
    created_account = await create_developer_bank_account(db, user_id, account)
    return APIResponse[DeveloperBankAccountResponse](
        item=created_account,
        detail="Bank account details created successfully"
    )

@router.patch("/", response_model=APIResponse[DeveloperBankAccountResponse])
async def update_bank_account(
    account_update: DeveloperBankAccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    verify_developer_role(current_user)
    user_id = UUID(str(current_user.id))
    
    existing_account = await get_developer_bank_account_by_user_id(db, user_id)
    if not existing_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer bank account details not found."
        )
        
    updated_account = await update_developer_bank_account(db, user_id, account_update)
    return APIResponse[DeveloperBankAccountResponse](
        item=updated_account,
        detail="Bank account details updated successfully"
    )

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bank_account(
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    verify_developer_role(current_user)
    user_id = UUID(str(current_user.id))
    
    existing_account = await get_developer_bank_account_by_user_id(db, user_id)
    if not existing_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer bank account details not found."
        )
        
    await delete_developer_bank_account(db, user_id)
    return None
