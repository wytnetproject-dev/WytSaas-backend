from typing import Optional
from sqlalchemy import Column, String, Text, Boolean, DateTime, BigInteger, Uuid, Integer, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from db.db import Base
from model import User


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
    brand_type = Column(ARRAY(String(50)), nullable=True, comment="Array of brand types (app / website / saas / ai-tool)")
    company_name = Column(String(255), nullable=True)
    is_wytpass_integration_accepted = Column(Boolean, default=False)
    is_payment_integration_accepted = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    status = Column(String(30), nullable=False, default="Pending", 
                   comment="Pending / Approved / Rejected / suspended")
    current_stage = Column(String(100), nullable=False, default="Brand Submitted",
                          comment="Brand Submitted / Waiting for WytPass Review / WhitePass Integration Completed / Waiting for WytPayment Review / WytPayment Integration Completed / Onboarding Completed")
    submitted_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_by = Column(Uuid, nullable=True, comment="Created user id")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    links = relationship("BrandLink", back_populates="brand", cascade="all, delete-orphan", lazy="selectin")
    tags = relationship("BrandTag", secondary="brand_tag_mapping", back_populates="brands", lazy="selectin")
    media = relationship("BrandMedia", back_populates="brand", cascade="all, delete-orphan", lazy="selectin")
    whitepass_review = relationship("BrandWhitePassReview", back_populates="brand", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    wytpayment_review = relationship("BrandWytPaymentReview", back_populates="brand", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    subscription_plans = relationship("BrandSubscriptionPlan", back_populates="brand", cascade="all, delete-orphan", lazy="selectin")
    reviews = relationship("BrandReview", back_populates="brand", cascade="all, delete-orphan", lazy="selectin")


  


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

    brand = relationship("Brand", back_populates="links")

    


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

    brand = relationship("Brand", back_populates="media")

  


# ======================== Brand Tags ========================
class BrandTag(Base):
    """Stores tags for search and filtering."""
    __tablename__ = "brand_tags"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)

    brands = relationship("Brand", secondary="brand_tag_mapping", back_populates="tags")


    


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
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False, comment="Review user")
    rating = Column(Integer, nullable=False, comment="Rating (1-5)")
    review = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    brand = relationship("Brand", back_populates="reviews")
    user = relationship("User")

    @property
    def user_email(self) -> Optional[str]:
        if "user" in self.__dict__ and self.user is not None:
            return self.user.email
        return None

    @property
    def user_name(self) -> Optional[str]:
        if "user" in self.__dict__ and self.user is not None:
            return self.user.full_name or self.user.username
        return None

    


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


# ======================== Brand WhitePass Reviews ========================
class BrandWhitePassReview(Base):
    """Tracks WhitePass verification status and details for a brand."""
    __tablename__ = "brand_whitepass_reviews"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    brand_id = Column(BigInteger, ForeignKey("brands.id"), nullable=False)
    integration_status = Column(String(30), nullable=False, default="pending", 
                                comment="pending / approved / rejected")
    sdk_installed = Column(Boolean, default=False, nullable=False)
    callback_verified = Column(Boolean, default=False, nullable=False)
    domain_verified = Column(Boolean, default=False, nullable=False)
    reviewed_by = Column(Uuid, ForeignKey("users.id"), nullable=True, comment="Admin reviewer")
    review_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    brand = relationship("Brand", back_populates="whitepass_review")


# ======================== Brand WytPayment Reviews ========================
class BrandWytPaymentReview(Base):
    """Tracks WytPayment verification status and details for a brand."""
    __tablename__ = "brand_wytpayment_reviews"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    brand_id = Column(BigInteger, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    integration_status = Column(String(30), nullable=False, default="pending", 
                                comment="pending / approved / rejected")
    
    # Checklist items for payment integration
    api_keys_configured = Column(Boolean, default=False, nullable=False)
    webhook_verified = Column(Boolean, default=False, nullable=False)
    test_payment_completed = Column(Boolean, default=False, nullable=False)
    
    # Review tracking
    reviewed_by = Column(Uuid, ForeignKey("users.id"), nullable=True, comment="Admin reviewer")
    review_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    brand = relationship("Brand", back_populates="wytpayment_review")


# ======================== Brand Subscription Plans ========================
class BrandSubscriptionPlan(Base):
    """Stores subscription plans created by the brand."""
    __tablename__ = "brand_subscription_plans"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    brand_id = Column(BigInteger, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    features = Column(ARRAY(Text), nullable=True)
    billing_cycle = Column(String(30), nullable=False)
    external_plan_id = Column(String(255), nullable=True)
    status = Column(String(30), nullable=False, default="active")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    brand = relationship("Brand", back_populates="subscription_plans")


# ======================== Brand Watchlist ========================
class BrandWatchlist(Base):
    """Watchlist model mapping user id and brand/app id."""
    __tablename__ = "brand_watchlist"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False)
    brand_id = Column(BigInteger, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    brand = relationship("Brand", lazy="selectin")
    user = relationship("User")


# ======================== User Subscription ========================
class UserSubscription(Base):
    """UserSubscription model mapping user id, brand id and plan id."""
    __tablename__ = "user_subscriptions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    brand_id = Column(BigInteger, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(BigInteger, ForeignKey("brand_subscription_plans.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(30), nullable=False, default="active") # active / cancelled
    subscribed_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # New sync integration columns
    external_user_id = Column(String(255), nullable=True)
    sync_status = Column(String(30), default="pending", nullable=False)
    last_synced_at = Column(DateTime, nullable=True)

    brand = relationship("Brand", lazy="selectin")
    user = relationship("User", lazy="selectin")
    plan = relationship("BrandSubscriptionPlan", lazy="selectin")


# ======================== Brand Integration Settings ========================
class BrandIntegration(Base):
    __tablename__ = "brand_integrations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    brand_id = Column(
        BigInteger,
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False
    )
    create_user_endpoint = Column(Text, nullable=True)
    update_user_endpoint = Column(Text, nullable=True)
    cancel_user_endpoint = Column(Text, nullable=True)
    webhook_url = Column(Text, nullable=True)
    api_key = Column(Text, nullable=True)
    webhook_secret = Column(Text, nullable=True)
    status = Column(String(30), default="active", nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    brand = relationship("Brand", lazy="selectin")


# ======================== Subscription Sync Logs ========================
class SubscriptionSyncLog(Base):
    __tablename__ = "subscription_sync_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    subscription_id = Column(
        BigInteger,
        ForeignKey("user_subscriptions.id", ondelete="CASCADE"),
        nullable=True
    )
    brand_id = Column(
        BigInteger,
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=True
    )
    action = Column(String(50), nullable=False)
    request_payload = Column(Text, nullable=True)
    response_payload = Column(Text, nullable=True)
    response_code = Column(Integer, nullable=True)
    status = Column(String(30), nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    subscription = relationship("UserSubscription", lazy="selectin")
    brand = relationship("Brand", lazy="selectin")


# ======================== Subscription Payments ========================
class SubscriptionPayment(Base):
    __tablename__ = "subscription_payments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    subscription_id = Column(
        BigInteger,
        ForeignKey("user_subscriptions.id", ondelete="CASCADE"),
        nullable=True
    )
    user_id = Column(Uuid, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_gateway = Column(String(50), nullable=False)
    gateway_payment_id = Column(String(255), nullable=False)
    payment_status = Column(String(30), nullable=False)
    paid_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    subscription = relationship("UserSubscription", lazy="selectin")


# ======================== Developer Bank Account Details ========================
class DeveloperBankAccount(Base):
    """Stores bank account details for a developer account (linked to a User)."""
    __tablename__ = "developer_bank_accounts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, comment="Developer user id")
    bank_name = Column(String(255), nullable=False)
    account_holder_name = Column(String(255), nullable=False)
    account_number = Column(String(100), nullable=False)
    routing_number = Column(String(100), nullable=True, comment="Routing number or SWIFT/IFSC code")
    swift_code = Column(String(50), nullable=True)
    ifsc_code = Column(String(50), nullable=True)
    account_type = Column(String(50), nullable=True, default="Checking", comment="Checking / Savings")
    bank_address = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", lazy="selectin")


