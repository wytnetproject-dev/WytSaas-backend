from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class EnquiryBase(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: str = Field(..., max_length=255)
    phone: Optional[str] = Field(None, max_length=30)
    message: str
    terms_accepted: bool = Field(False)

class EnquiryCreate(EnquiryBase):
    pass

class EnquiryResponse(EnquiryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
