from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID

class BrandLinkBase(BaseModel):
    link_type: str = Field(..., max_length=50)
    title: str = Field(..., max_length=255)
    url: str
    is_primary: bool = False

class BrandLinkCreate(BrandLinkBase):
    pass

class BrandLinkResponse(BrandLinkBase):
    id: int
    brand_id: int

    class Config:
        from_attributes = True

class BrandTagResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class BrandMediaBase(BaseModel):
    media_type: str = Field(..., max_length=30)
    media_url: str
    sort_order: Optional[int] = None

class BrandMediaCreate(BrandMediaBase):
    pass

class BrandMediaResponse(BrandMediaBase):
    id: int
    brand_id: int

    class Config:
        from_attributes = True

class BrandReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    review: Optional[str] = None

class BrandReviewResponse(BaseModel):
    id: int
    brand_id: int
    user_id: UUID
    rating: int
    review: Optional[str] = None
    created_at: datetime
    user_email: Optional[str] = None
    user_name: Optional[str] = None

    class Config:
        from_attributes = True

class BrandWhitePassReviewBase(BaseModel):
    sdk_installed: bool = False
    callback_verified: bool = False
    domain_verified: bool = False

class BrandWhitePassReviewCreate(BrandWhitePassReviewBase):
    pass

class BrandWhitePassReviewResponse(BrandWhitePassReviewBase):
    id: int
    brand_id: int
    integration_status: str
    review_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class BrandWhitePassReviewLogResponse(BaseModel):
    id: int
    brand_id: int
    integration_status: str
    sdk_installed: bool
    callback_verified: bool
    domain_verified: bool
    reviewed_by: Optional[UUID] = None
    review_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class BrandWhitePassReviewAction(BaseModel):
    integration_status: str = Field(..., max_length=30)  # approved or rejected
    review_notes: Optional[str] = None


class BrandWytPaymentReviewBase(BaseModel):
    api_keys_configured: bool = False
    webhook_verified: bool = False
    test_payment_completed: bool = False

class BrandWytPaymentReviewCreate(BrandWytPaymentReviewBase):
    pass

class BrandWytPaymentReviewResponse(BrandWytPaymentReviewBase):
    id: int
    brand_id: int
    integration_status: str
    review_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class BrandWytPaymentReviewAction(BaseModel):
    integration_status: str = Field(..., max_length=30)  # approved or rejected
    review_notes: Optional[str] = None


class BrandBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=255)
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    brand_type: Optional[List[str]] = Field(None)
    company_name: Optional[str] = Field(None, max_length=255)
    is_wytpass_integration_accepted: bool = False
    is_payment_integration_accepted: bool = False
    is_featured: bool = False
    status: str = Field("Pending", max_length=30)
    current_stage: str = Field("Brand Submitted", max_length=100)

class BrandCreate(BrandBase):
    links: Optional[List[BrandLinkCreate]] = []
    tags: Optional[List[str]] = []
    media: Optional[List[BrandMediaCreate]] = []

class BrandUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    slug: Optional[str] = Field(None, min_length=2, max_length=255)
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    brand_type: Optional[List[str]] = Field(None)
    company_name: Optional[str] = Field(None, max_length=255)
    is_wytpass_integration_accepted: Optional[bool] = None
    is_payment_integration_accepted: Optional[bool] = None
    is_featured: Optional[bool] = None
    status: Optional[str] = Field(None, max_length=30)
    current_stage: Optional[str] = Field(None, max_length=100)
    links: Optional[List[BrandLinkCreate]] = None
    tags: Optional[List[str]] = None
    media: Optional[List[BrandMediaCreate]] = None

class BrandResponse(BrandBase):
    id: int
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    links: List[BrandLinkResponse] = []
    tags: List[BrandTagResponse] = []
    media: List[BrandMediaResponse] = []
    whitepass_review: Optional[BrandWhitePassReviewResponse] = None
    wytpayment_review: Optional[BrandWytPaymentReviewResponse] = None

    class Config:
        from_attributes = True


class BrandDetailResponse(BrandResponse):
    reviews: List[BrandReviewResponse] = []


class BrandWatchlistResponse(BaseModel):
    id: int
    user_id: UUID
    brand_id: int
    created_at: datetime
    brand: Optional[BrandResponse] = None

    class Config:
        from_attributes = True


# ======================== Marketplace Banner Schemas ========================
class MarketplaceBannerBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    subtitle: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    badge: Optional[str] = Field(None, max_length=100)
    bg_image: Optional[str] = Field("from-blue-600 to-indigo-900")
    icon: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0

class MarketplaceBannerCreate(MarketplaceBannerBase):
    pass

class MarketplaceBannerUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    subtitle: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    badge: Optional[str] = Field(None, max_length=100)
    bg_image: Optional[str] = Field(None)
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class MarketplaceBannerResponse(MarketplaceBannerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True




