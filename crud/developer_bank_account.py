from typing import Optional
from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.brands import DeveloperBankAccount
from schemas.developer_bank_account import DeveloperBankAccountCreate, DeveloperBankAccountUpdate

async def get_developer_bank_account_by_user_id(db: AsyncSession, user_id: UUID) -> Optional[DeveloperBankAccount]:
    """Retrieve bank account details by user ID."""
    result = await db.execute(
        select(DeveloperBankAccount).where(DeveloperBankAccount.user_id == user_id)
    )
    return result.scalars().first()

async def create_developer_bank_account(
    db: AsyncSession, user_id: UUID, account: DeveloperBankAccountCreate
) -> DeveloperBankAccount:
    """Create a new bank account entry for a developer user."""
    db_account = DeveloperBankAccount(
        user_id=user_id,
        bank_name=account.bank_name,
        account_holder_name=account.account_holder_name,
        account_number=account.account_number,
        routing_number=account.routing_number,
        swift_code=account.swift_code,
        ifsc_code=account.ifsc_code,
        account_type=account.account_type,
        bank_address=account.bank_address,
    )
    db.add(db_account)
    await db.commit()
    await db.refresh(db_account)
    return db_account

async def update_developer_bank_account(
    db: AsyncSession, user_id: UUID, account_update: DeveloperBankAccountUpdate
) -> Optional[DeveloperBankAccount]:
    """Update existing bank account details for a developer user."""
    update_data = account_update.model_dump(exclude_unset=True)
    if not update_data:
        return await get_developer_bank_account_by_user_id(db, user_id)

    query = (
        update(DeveloperBankAccount)
        .where(DeveloperBankAccount.user_id == user_id)
        .values(**update_data)
    )
    await db.execute(query)
    await db.commit()
    return await get_developer_bank_account_by_user_id(db, user_id)

async def delete_developer_bank_account(db: AsyncSession, user_id: UUID) -> bool:
    """Delete a developer's bank account details."""
    query = delete(DeveloperBankAccount).where(DeveloperBankAccount.user_id == user_id)
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0
