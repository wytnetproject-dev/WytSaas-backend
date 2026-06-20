from typing import List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from models.brands import Brand, BrandReview, MarketplaceBanner
from schemas.brand import (
    BrandCreate, BrandUpdate, BrandReviewCreate,
    MarketplaceBannerCreate, MarketplaceBannerUpdate
)
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
    from models.brands import (
        BrandLink, BrandCategoryMapping, BrandMedia, BrandTagMapping,
        BrandReview, BrandPromotion, BrandAnalytics, BrandWhitePassReview,
        BrandWytPaymentReview, BrandSubscriptionPlan, BrandWatchlist,
        UserSubscription, BrandIntegration, SubscriptionSyncLog, SubscriptionPayment
    )

    # 1. SubscriptionPayment references user_subscriptions.id
    sub_ids_query = select(UserSubscription.id).where(UserSubscription.brand_id == brand_id)
    sub_ids_result = await db.execute(sub_ids_query)
    sub_ids = list(sub_ids_result.scalars().all())
    if sub_ids:
        await db.execute(delete(SubscriptionPayment).where(SubscriptionPayment.subscription_id.in_(sub_ids)))

    # 2. SubscriptionSyncLog (references brands.id and user_subscriptions.id)
    await db.execute(delete(SubscriptionSyncLog).where(SubscriptionSyncLog.brand_id == brand_id))

    # 3. UserSubscription (references brands.id)
    await db.execute(delete(UserSubscription).where(UserSubscription.brand_id == brand_id))

    # 4. BrandIntegration (references brands.id)
    await db.execute(delete(BrandIntegration).where(BrandIntegration.brand_id == brand_id))

    # 5. BrandWatchlist (references brands.id)
    await db.execute(delete(BrandWatchlist).where(BrandWatchlist.brand_id == brand_id))

    # 6. BrandSubscriptionPlan (references brands.id)
    await db.execute(delete(BrandSubscriptionPlan).where(BrandSubscriptionPlan.brand_id == brand_id))

    # 7. BrandWytPaymentReview (references brands.id)
    await db.execute(delete(BrandWytPaymentReview).where(BrandWytPaymentReview.brand_id == brand_id))

    # 8. BrandWhitePassReview (references brands.id)
    await db.execute(delete(BrandWhitePassReview).where(BrandWhitePassReview.brand_id == brand_id))

    # 9. BrandAnalytics (references brands.id)
    await db.execute(delete(BrandAnalytics).where(BrandAnalytics.brand_id == brand_id))

    # 10. BrandPromotion (references brands.id)
    await db.execute(delete(BrandPromotion).where(BrandPromotion.brand_id == brand_id))

    # 11. BrandReview (references brands.id)
    await db.execute(delete(BrandReview).where(BrandReview.brand_id == brand_id))

    # 12. BrandTagMapping (references brands.id)
    await db.execute(delete(BrandTagMapping).where(BrandTagMapping.brand_id == brand_id))

    # 13. BrandMedia (references brands.id)
    await db.execute(delete(BrandMedia).where(BrandMedia.brand_id == brand_id))

    # 14. BrandCategoryMapping (references brands.id)
    await db.execute(delete(BrandCategoryMapping).where(BrandCategoryMapping.brand_id == brand_id))

    # 15. BrandLink (references brands.id)
    await db.execute(delete(BrandLink).where(BrandLink.brand_id == brand_id))

    # 16. Finally delete the Brand itself
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


# ======================== Marketplace Banner CRUD ========================
async def create_marketplace_banner(db: AsyncSession, banner: MarketplaceBannerCreate) -> MarketplaceBanner:
    db_banner = MarketplaceBanner(
        title=banner.title,
        subtitle=banner.subtitle,
        description=banner.description,
        badge=banner.badge,
        bg_image=banner.bg_image,
        icon=banner.icon,
        is_active=banner.is_active,
        sort_order=banner.sort_order
    )
    db.add(db_banner)
    await db.commit()
    await db.refresh(db_banner)
    return db_banner

async def list_marketplace_banners(db: AsyncSession, only_active: bool = True) -> List[MarketplaceBanner]:
    query = select(MarketplaceBanner)
    if only_active:
        query = query.where(MarketplaceBanner.is_active == True)
    query = query.order_by(MarketplaceBanner.sort_order.asc(), MarketplaceBanner.id.asc())
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_marketplace_banner_by_id(db: AsyncSession, banner_id: int) -> Optional[MarketplaceBanner]:
    result = await db.execute(select(MarketplaceBanner).where(MarketplaceBanner.id == banner_id))
    return result.scalars().first()

async def update_marketplace_banner(db: AsyncSession, banner_id: int, banner_update: MarketplaceBannerUpdate) -> Optional[MarketplaceBanner]:
    db_banner = await get_marketplace_banner_by_id(db, banner_id)
    if not db_banner:
        return None
    update_data = banner_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_banner, key, value)
    await db.commit()
    await db.refresh(db_banner)
    return db_banner

async def delete_marketplace_banner(db: AsyncSession, banner_id: int) -> bool:
    result = await db.execute(delete(MarketplaceBanner).where(MarketplaceBanner.id == banner_id))
    await db.commit()
    return result.rowcount > 0

