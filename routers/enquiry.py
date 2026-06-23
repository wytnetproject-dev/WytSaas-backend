from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from db.db import get_db
from schemas.enquiry import EnquiryCreate, EnquiryResponse
from schemas.response import APIResponse
from crud.enquiry import (
    create_enquiry,
    get_enquiry_by_id,
    get_enquiries,
    delete_enquiry,
)
from utils.auth import UserJWT, get_user_token

router = APIRouter(prefix="/enquiries", tags=["Enquiries"])

def verify_admin_role(current_user: UserJWT):
    """Enforce wytsaas_admin role for admin operations."""
    if current_user.role != "wytsaas_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required."
        )

@router.post("/", response_model=APIResponse[EnquiryResponse], status_code=status.HTTP_201_CREATED)
async def create_new_enquiry(enquiry: EnquiryCreate, db: AsyncSession = Depends(get_db)):
    """Create a new enquiry. Publicly accessible endpoint."""
    created = await create_enquiry(db, enquiry)
    return APIResponse[EnquiryResponse](
        item=created,
        detail="Enquiry submitted successfully"
    )

@router.get("/", response_model=APIResponse[EnquiryResponse])
async def list_enquiries(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    """List all enquiries. Restricted to wytsaas_admin."""
    verify_admin_role(current_user)
    items = await get_enquiries(db, skip, limit)
    return APIResponse[EnquiryResponse](
        items=items,
        detail="Enquiries retrieved successfully"
    )

@router.get("/{enquiry_id}", response_model=APIResponse[EnquiryResponse])
async def retrieve_enquiry(
    enquiry_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    """Retrieve details of a single enquiry. Restricted to wytsaas_admin."""
    verify_admin_role(current_user)
    db_enquiry = await get_enquiry_by_id(db, enquiry_id)
    if not db_enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enquiry not found"
        )
    return APIResponse[EnquiryResponse](
        item=db_enquiry,
        detail="Enquiry details retrieved successfully"
    )

@router.delete("/{enquiry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_enquiry(
    enquiry_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    """Delete an enquiry record. Restricted to wytsaas_admin."""
    verify_admin_role(current_user)
    db_enquiry = await get_enquiry_by_id(db, enquiry_id)
    if not db_enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enquiry not found"
        )
    await delete_enquiry(db, enquiry_id)
    return None
