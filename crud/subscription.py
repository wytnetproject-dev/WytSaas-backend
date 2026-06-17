from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.brands import BrandSubscriptionPlan, UserSubscription
from schemas.subscription import BrandSubscriptionPlanCreate, BrandSubscriptionPlanUpdate

# Create a new subscription plan for a brand
async def create_subscription_plan(db: AsyncSession, brand_id: int, plan: BrandSubscriptionPlanCreate) -> BrandSubscriptionPlan:
    db_plan = BrandSubscriptionPlan(
        brand_id=brand_id,
        name=plan.name,
        description=plan.description,
        price=plan.price,
        features=plan.features,
        billing_cycle=plan.billing_cycle,
        external_plan_id=plan.external_plan_id,
        status=plan.status
    )
    db.add(db_plan)
    await db.commit()
    await db.refresh(db_plan)
    return db_plan

# Get a single subscription plan by ID
async def get_subscription_plan(db: AsyncSession, plan_id: int) -> Optional[BrandSubscriptionPlan]:
    result = await db.execute(select(BrandSubscriptionPlan).where(BrandSubscriptionPlan.id == plan_id))
    return result.scalars().first()

# List multiple subscription plans (optionally filtered by brand_id)
async def list_subscription_plans(db: AsyncSession, brand_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[BrandSubscriptionPlan]:
    query = select(BrandSubscriptionPlan)
    if brand_id is not None:
        query = query.where(BrandSubscriptionPlan.brand_id == brand_id)
    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())

# Update an existing subscription plan
async def update_subscription_plan(db: AsyncSession, plan_id: int, plan_update: BrandSubscriptionPlanUpdate) -> Optional[BrandSubscriptionPlan]:
    db_plan = await get_subscription_plan(db, plan_id)
    if not db_plan:
        return None
    
    update_data = plan_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_plan, key, value)
        
    await db.commit()
    await db.refresh(db_plan)
    return db_plan

# Delete a subscription plan by ID
async def delete_subscription_plan(db: AsyncSession, plan_id: int) -> bool:
    query = delete(BrandSubscriptionPlan).where(BrandSubscriptionPlan.id == plan_id)
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0


# Add a user subscription mapping
async def add_user_subscription(db: AsyncSession, user_id: UUID, brand_id: int, plan_id: int) -> UserSubscription:
    # Check if already exists for this brand/app
    existing = await db.execute(
        select(UserSubscription)
        .where(UserSubscription.user_id == user_id, UserSubscription.brand_id == brand_id)
    )
    db_item = existing.scalars().first()
    if db_item:
        db_item.plan_id = plan_id
        db_item.status = "active"
        await db.commit()
        await db.refresh(db_item)
        return db_item
        
    db_item = UserSubscription(user_id=user_id, brand_id=brand_id, plan_id=plan_id, status="active")
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


# Remove a user subscription mapping
async def remove_user_subscription(db: AsyncSession, user_id: UUID, brand_id: int) -> bool:
    query = delete(UserSubscription).where(
        UserSubscription.user_id == user_id, 
        UserSubscription.brand_id == brand_id
    )
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0


# Get all user subscriptions
async def get_user_subscriptions(db: AsyncSession, user_id: UUID) -> List[UserSubscription]:
    query = (
        select(UserSubscription)
        .where(UserSubscription.user_id == user_id)
        .order_by(UserSubscription.subscribed_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


# Get all subscribers for a specific brand/app
async def get_brand_subscribers(db: AsyncSession, brand_id: int) -> List[UserSubscription]:
    query = (
        select(UserSubscription)
        .where(UserSubscription.brand_id == brand_id)
        .order_by(UserSubscription.subscribed_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())

