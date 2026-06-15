from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_db
from schemas.subscription import (
    BrandSubscriptionPlanCreate,
    BrandSubscriptionPlanUpdate,
    BrandSubscriptionPlanResponse
)
from schemas.response import APIResponse
from crud.subscription import (
    create_subscription_plan,
    get_subscription_plan,
    list_subscription_plans,
    update_subscription_plan,
    delete_subscription_plan
)
from crud.brand import get_brand_by_id
from utils.auth import UserJWT, get_user_token

router = APIRouter(prefix="/brands", tags=["Brand Subscriptions"])

# List all subscription plans, optionally filter by brand_id
@router.get("/subscription-plans/", response_model=APIResponse[BrandSubscriptionPlanResponse])
async def list_all_subscription_plans(
    brand_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    plans = await list_subscription_plans(db, brand_id=brand_id, skip=skip, limit=limit)
    return APIResponse[BrandSubscriptionPlanResponse](
        items=plans,
        detail="Subscription plans retrieved successfully",
        itemCount=len(plans)
    )

# Create a new subscription plan for a brand
@router.post("/{brand_id}/subscription-plans", response_model=APIResponse[BrandSubscriptionPlanResponse], status_code=status.HTTP_201_CREATED)
async def create_new_subscription_plan(
    brand_id: int,
    plan: BrandSubscriptionPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    brand = await get_brand_by_id(db, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    created_plan = await create_subscription_plan(db, brand_id, plan)
    return APIResponse[BrandSubscriptionPlanResponse](
        item=created_plan,
        detail="Subscription plan created successfully"
    )

# Update a subscription plan by ID
@router.patch("/subscription-plans/{plan_id}", response_model=APIResponse[BrandSubscriptionPlanResponse])
async def modify_subscription_plan(
    plan_id: int,
    plan_update: BrandSubscriptionPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    plan = await get_subscription_plan(db, plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found"
        )
    updated_plan = await update_subscription_plan(db, plan_id, plan_update)
    return APIResponse[BrandSubscriptionPlanResponse](
        item=updated_plan,
        detail="Subscription plan updated successfully"
    )

# Delete a subscription plan by ID
@router.delete("/subscription-plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_subscription_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserJWT = Depends(get_user_token)
):
    success = await delete_subscription_plan(db, plan_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found"
        )
    return None
