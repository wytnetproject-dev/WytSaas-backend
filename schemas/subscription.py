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
