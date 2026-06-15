from typing import List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from models.brands import Brand, BrandReview
from schemas.brand import BrandCreate, BrandUpdate, BrandReviewCreate
from uuid import UUID

# Helper function to get or create BrandTag instances
async def get_or_create_tags(db: AsyncSession, tag_names: List[str]) -> List:
    from models.brands import BrandTag
    if not tag_names:
        return []
    normalized_names = list(set([t.strip().lower() for t in tag_names if t.strip()]))
    if not normalized_names:
        return []
    result = await db.execute(select(BrandTag).where(BrandTag.name.in_(normalized_names)))
    existing_tags = list(result.scalars().all())
    existing_map = {t.name: t for t in existing_tags}
    
    tags_to_return = []
    for name in normalized_names:
        if name in existing_map:
            tags_to_return.append(existing_map[name])
        else:
            new_tag = BrandTag(name=name)
            db.add(new_tag)
            tags_to_return.append(new_tag)
    return tags_to_return

# Create a new brand
async def create_brand(db: AsyncSession, brand: BrandCreate, creator_id: Optional[UUID] = None) -> Brand:
    db_brand = Brand(
        name=brand.name,
        slug=brand.slug,
        short_description=brand.short_description,
        full_description=brand.full_description,
        logo_url=brand.logo_url,
        banner_url=brand.banner_url,
        brand_type=brand.brand_type,
        company_name=brand.company_name,
        is_wytpass_integration_accepted=brand.is_wytpass_integration_accepted,
        is_payment_integration_accepted=brand.is_payment_integration_accepted,
        is_featured=brand.is_featured,
        status=brand.status,
        current_stage=brand.current_stage,
        created_by=creator_id
    )
    if brand.links:
        from models.brands import BrandLink
        db_brand.links = [
            BrandLink(
                link_type=link.link_type,
                title=link.title,
                url=link.url,
                is_primary=link.is_primary
            ) for link in brand.links
        ]
    if brand.tags:
        db_brand.tags = await get_or_create_tags(db, brand.tags)
    if brand.media:
        from models.brands import BrandMedia
        db_brand.media = [
            BrandMedia(
                media_type=item.media_type,
                media_url=item.media_url,
                sort_order=item.sort_order
            ) for item in brand.media
        ]

    db.add(db_brand)
    await db.commit()
    await db.refresh(db_brand)
    return db_brand

# Get a single brand by ID
async def get_brand_by_id(db: AsyncSession, brand_id: int) -> Optional[Brand]:
    result = await db.execute(
        select(Brand)
        .options(selectinload(Brand.reviews).selectinload(BrandReview.user))
        .where(Brand.id == brand_id)
    )
    return result.scalars().first()

# Get a single brand by slug
async def get_brand_by_slug(db: AsyncSession, slug: str) -> Optional[Brand]:
    result = await db.execute(
        select(Brand)
        .options(selectinload(Brand.reviews).selectinload(BrandReview.user))
        .where(Brand.slug == slug)
    )
    return result.scalars().first()

# List multiple brands with limit and offset
async def list_brands(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Brand]:
    result = await db.execute(select(Brand).offset(skip).limit(limit))
    return list(result.scalars().all())

# Update a brand
async def update_brand(db: AsyncSession, brand_id: int, brand_update: BrandUpdate) -> Optional[Brand]:
    db_brand = await get_brand_by_id(db, brand_id)
    if not db_brand:
        return None

    update_data = brand_update.model_dump(exclude_unset=True)
    links_data = update_data.pop('links', None)
    tags_data = update_data.pop('tags', None)
    media_data = update_data.pop('media', None)

    for key, value in update_data.items():
        setattr(db_brand, key, value)

    if links_data is not None:
        from models.brands import BrandLink
        await db.execute(delete(BrandLink).where(BrandLink.brand_id == brand_id))
        if links_data:
            db_links = [
                BrandLink(
                    brand_id=brand_id,
                    link_type=link['link_type'],
                    title=link['title'],
                    url=link['url'],
                    is_primary=link.get('is_primary', False)
                ) for link in links_data
            ]
            db.add_all(db_links)

    if tags_data is not None:
        db_brand.tags = await get_or_create_tags(db, tags_data)

    if media_data is not None:
        from models.brands import BrandMedia
        await db.execute(delete(BrandMedia).where(BrandMedia.brand_id == brand_id))
        if media_data:
            db_media = [
                BrandMedia(
                    brand_id=brand_id,
                    media_type=item['media_type'],
                    media_url=item['media_url'],
                    sort_order=item.get('sort_order', None)
                ) for item in media_data
            ]
            db.add_all(db_media)

    await db.commit()
    await db.refresh(db_brand)
    return db_brand


# Delete a brand
async def delete_brand(db: AsyncSession, brand_id: int) -> bool:
    query = delete(Brand).where(Brand.id == brand_id)
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0


# Create a new brand review
async def create_brand_review(
    db: AsyncSession, 
    brand_id: int, 
    review_data: BrandReviewCreate, 
    user_id: UUID
) -> BrandReview:
    db_review = BrandReview(
        brand_id=brand_id,
        user_id=user_id,
        rating=review_data.rating,
        review=review_data.review
    )
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    
    # Eagerly load user relationship to serialize user_email
    result = await db.execute(
        select(BrandReview)
        .options(selectinload(BrandReview.user))
        .where(BrandReview.id == db_review.id)
    )
    refreshed_review = result.scalars().first()
    return refreshed_review if refreshed_review else db_review

# List reviews for a specific brand
async def list_brand_reviews(
    db: AsyncSession, 
    brand_id: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[BrandReview]:
    query = select(BrandReview).options(selectinload(BrandReview.user)).where(BrandReview.brand_id == brand_id).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())
