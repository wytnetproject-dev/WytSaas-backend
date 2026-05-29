from sqlalchemy import Column, String, Text, Boolean, DateTime, BigInteger, Uuid, Integer, ForeignKey
from sqlalchemy.sql import func
from db.db import Base


# ======================== Main Brands Table ========================
class Brand(Base):
    """Brand/Product model for storing brand or product information."""
    __tablename__ = "brands"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    short_description = Column(Text, nullable=True)
    full_description = Column(Text, nullable=True)
    logo_url = Column(Text, nullable=True)
    banner_url = Column(Text, nullable=True)
    brand_type = Column(String(50), nullable=True, comment="app / website / saas / ai-tool")
    company_name = Column(String(255), nullable=True)
    is_wytpass_integration_accepted = Column(Boolean, default=False)
    is_payment_integration_accepted = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    status = Column(String(30), nullable=False, default="draft", 
                   comment="draft / pending / under_review / approved / rejected / suspended")
    current_stage = Column(String(30), nullable=False, default="brand_submission",
                          comment="brand_submission / whitepass_review / payment_integration / final_review / completed")
    submitted_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_by = Column(Uuid, nullable=True, comment="Created user id")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

  


# ======================== Brand Links ========================
class BrandLink(Base):
    """Stores all external links related to the brand."""
    __tablename__ = "brand_links"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    brand_id = Column(BigInteger, ForeignKey("brands.id"), nullable=False)
    link_type = Column(String(50), nullable=False, comment="play_store / website / github")
    title = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    


# ======================== Brand Categories ========================
class BrandCategory(Base):
    """Stores available categories."""
    __tablename__ = "brand_categories"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    icon = Column(Text, nullable=True)

   

# ======================== Brand Category Mapping ========================
class BrandCategoryMapping(Base):
    """Mapping between brands and categories."""
    __tablename__ = "brand_category_mapping"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    brand_id = Column(BigInteger, ForeignKey("brands.id"), nullable=False)
    category_id = Column(BigInteger, ForeignKey("brand_categories.id"), nullable=False)

    def __repr__(self):
        return f"<BrandCategoryMapping(id={self.id}, brand_id={self.brand_id}, category_id={self.category_id})>"


# ======================== Brand Media ========================
class BrandMedia(Base):
    """Stores screenshots, banners, and videos."""
    __tablename__ = "brand_media"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    brand_id = Column(BigInteger, ForeignKey("brands.id"), nullable=False)
    media_type = Column(String(30), nullable=False, comment="image / video")
    media_url = Column(Text, nullable=False)
    sort_order = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

  


# ======================== Brand Tags ========================
class BrandTag(Base):
    """Stores tags for search and filtering."""
    __tablename__ = "brand_tags"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)

    


# ======================== Brand Tag Mapping ========================
class BrandTagMapping(Base):
    """Mapping between brands and tags."""
    __tablename__ = "brand_tag_mapping"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    brand_id = Column(BigInteger, ForeignKey("brands.id"), nullable=False)
    tag_id = Column(BigInteger, ForeignKey("brand_tags.id"), nullable=False)

    


# ======================== Brand Reviews ========================
class BrandReview(Base):
    """Stores ratings and reviews."""
    __tablename__ = "brand_reviews"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    brand_id = Column(BigInteger, ForeignKey("brands.id"), nullable=False)
    user_id = Column(Uuid, nullable=False, comment="Review user")
    rating = Column(Integer, nullable=False, comment="Rating (1-5)")
    review = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    


# ======================== Brand Promotions ========================
class BrandPromotion(Base):
    """Stores promotion and featured data."""
    __tablename__ = "brand_promotions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    brand_id = Column(BigInteger, ForeignKey("brands.id"), nullable=False)
    promotion_type = Column(String(50), nullable=False, comment="featured / sponsored")
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(String(30), nullable=False, default="active", comment="active / expired")

   


# ======================== Brand Analytics ========================
class BrandAnalytics(Base):
    """Stores analytics and tracking data."""
    __tablename__ = "brand_analytics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    brand_id = Column(BigInteger, ForeignKey("brands.id"), nullable=False, unique=True)
    total_views = Column(BigInteger, default=0)
    total_clicks = Column(BigInteger, default=0)
    total_installs = Column(BigInteger, default=0)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

   
