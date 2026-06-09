from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_db
from schemas.brand import BrandCreate, BrandUpdate, BrandResponse, BrandWhitePassReviewCreate, BrandWhitePassReviewResponse
from schemas.response import APIResponse
from crud.brand import (
    create_brand, get_brand_by_id, get_brand_by_slug,
    list_brands, update_brand, delete_brand
)
from utils.auth import UserJWT, get_user_token

router = APIRouter(prefix="/brands", tags=["Brands"])

# Create a new brand
@router.post("/", response_model=APIResponse[BrandResponse], status_code=status.HTTP_201_CREATED)
async def create_new_brand(
    brand: BrandCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    # Check if brand with same slug exists
    existing = await get_brand_by_slug(db, brand.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Brand with this slug already exists"
        )
    
    created_brand = await create_brand(db, brand, creator_id=current_user.id)
    return APIResponse[BrandResponse](
        item=created_brand,
        detail="Brand created successfully"
    )

# List all brands
@router.get("/", response_model=APIResponse[BrandResponse])
async def list_all_brands(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
    brands = await list_brands(db, skip=skip, limit=limit)
    return APIResponse[BrandResponse](
        items=brands,
        detail="Brands retrieved successfully",
        itemCount=len(brands)
    )

# Get a brand by ID
@router.get("/{brand_id}", response_model=APIResponse[BrandResponse])
async def retrieve_brand(brand_id: int, db: AsyncSession = Depends(get_db)):
    brand = await get_brand_by_id(db, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    return APIResponse[BrandResponse](
        item=brand,
        detail="Brand retrieved successfully"
    )

# Update a brand by ID
@router.patch("/{brand_id}", response_model=APIResponse[BrandResponse])
async def modify_brand(
    brand_id: int, 
    brand_update: BrandUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    brand = await get_brand_by_id(db, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    
    # Ensure slug uniqueness if changed
    if brand_update.slug:
        existing = await get_brand_by_slug(db, brand_update.slug)
        if existing and existing.id != brand_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Brand with this slug already exists"
            )

    updated_brand = await update_brand(db, brand_id, brand_update)
    return APIResponse[BrandResponse](
        item=updated_brand,
        detail="Brand updated successfully"
    )

# Delete a brand by ID
@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_brand(
    brand_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    success = await delete_brand(db, brand_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    return None

# Submit WhitePass SSO Integration Review
@router.post("/{brand_id}/whitepass-review", response_model=APIResponse[BrandWhitePassReviewResponse])
async def submit_whitepass_review(
    brand_id: int,
    review_data: BrandWhitePassReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    brand = await get_brand_by_id(db, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    
    from models.brands import BrandWhitePassReview
    from sqlalchemy import select
    result = await db.execute(select(BrandWhitePassReview).where(BrandWhitePassReview.brand_id == brand_id))
    db_review = result.scalars().first()

    if db_review:
        db_review.sdk_installed = review_data.sdk_installed
        db_review.callback_verified = review_data.callback_verified
        db_review.domain_verified = review_data.domain_verified
        db_review.integration_status = "pending"
    else:
        db_review = BrandWhitePassReview(
            brand_id=brand_id,
            sdk_installed=review_data.sdk_installed,
            callback_verified=review_data.callback_verified,
            domain_verified=review_data.domain_verified,
            integration_status="pending"
        )
        db.add(db_review)

    brand.is_wytpass_integration_accepted = True
    brand.current_stage = "whitepass_review"

    await db.commit()
    await db.refresh(db_review)

    return APIResponse[BrandWhitePassReviewResponse](
        item=db_review,
        detail="SSO Review requested successfully"
    )

# Retrieve WhitePass SSO Integration Review
@router.get("/{brand_id}/whitepass-review", response_model=APIResponse[BrandWhitePassReviewResponse])
async def get_whitepass_review(
    brand_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    brand = await get_brand_by_id(db, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    
    from models.brands import BrandWhitePassReview
    from sqlalchemy import select
    result = await db.execute(select(BrandWhitePassReview).where(BrandWhitePassReview.brand_id == brand_id))
    db_review = result.scalars().first()

    if not db_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No WhitePass review found for this brand"
        )

    return APIResponse[BrandWhitePassReviewResponse](
        item=db_review,
        detail="SSO Review retrieved successfully"
    )

