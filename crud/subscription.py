from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.brands import BrandSubscriptionPlan
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
