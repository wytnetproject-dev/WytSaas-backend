from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class BrandSubscriptionPlanBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    features: Optional[List[str]] = None
    billing_cycle: str = Field(..., max_length=30)
    external_plan_id: Optional[str] = Field(None, max_length=255)
    status: str = Field("active", max_length=30)

class BrandSubscriptionPlanCreate(BrandSubscriptionPlanBase):
    pass

class BrandSubscriptionPlanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    features: Optional[List[str]] = None
    billing_cycle: Optional[str] = Field(None, max_length=30)
    external_plan_id: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=30)

class BrandSubscriptionPlanResponse(BrandSubscriptionPlanBase):
    id: int
    brand_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserSubscriptionCreate(BaseModel):
    plan_id: int


class UserSubscriptionResponse(BaseModel):
    id: int
    user_id: str
    brand_id: int
    plan_id: int
    status: str
    subscribed_at: datetime
    external_user_id: Optional[str] = None
    sync_status: Optional[str] = "pending"
    last_synced_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentOrderCreate(BaseModel):
    plan_id: int


class PaymentOrderResponse(BaseModel):
    order_id: str
    amount: int
    currency: str
    key_id: str
    plan_id: int
    is_mock: bool


class PaymentVerificationInput(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan_id: int

