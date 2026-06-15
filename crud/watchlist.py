from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from models.brands import BrandWatchlist
from uuid import UUID

async def add_to_watchlist(db: AsyncSession, user_id: UUID, brand_id: int) -> BrandWatchlist:
    # Check if already exists
    existing = await db.execute(
        select(BrandWatchlist)
        .where(BrandWatchlist.user_id == user_id, BrandWatchlist.brand_id == brand_id)
    )
    db_item = existing.scalars().first()
    if db_item:
        return db_item
        
    db_item = BrandWatchlist(user_id=user_id, brand_id=brand_id)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

async def remove_from_watchlist(db: AsyncSession, user_id: UUID, brand_id: int) -> bool:
    query = delete(BrandWatchlist).where(
        BrandWatchlist.user_id == user_id, 
        BrandWatchlist.brand_id == brand_id
    )
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0

async def get_user_watchlist(db: AsyncSession, user_id: UUID) -> List[BrandWatchlist]:
    query = (
        select(BrandWatchlist)
        .options(selectinload(BrandWatchlist.brand))
        .where(BrandWatchlist.user_id == user_id)
    )
    result = await db.execute(query)
    return list(result.scalars().all())
