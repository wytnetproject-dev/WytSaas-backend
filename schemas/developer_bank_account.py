from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID

class DeveloperBankAccountBase(BaseModel):
    bank_name: str = Field(..., max_length=255)
    account_holder_name: str = Field(..., max_length=255)
    account_number: str = Field(..., max_length=100)
    routing_number: Optional[str] = Field(None, max_length=100)
    swift_code: Optional[str] = Field(None, max_length=50)
    ifsc_code: Optional[str] = Field(None, max_length=50)
    account_type: Optional[str] = Field("Checking", max_length=50)
    bank_address: Optional[str] = None

class DeveloperBankAccountCreate(DeveloperBankAccountBase):
    pass

class DeveloperBankAccountUpdate(BaseModel):
    bank_name: Optional[str] = Field(None, max_length=255)
    account_holder_name: Optional[str] = Field(None, max_length=255)
    account_number: Optional[str] = Field(None, max_length=100)
    routing_number: Optional[str] = Field(None, max_length=100)
    swift_code: Optional[str] = Field(None, max_length=50)
    ifsc_code: Optional[str] = Field(None, max_length=50)
    account_type: Optional[str] = Field(None, max_length=50)
    bank_address: Optional[str] = None

class DeveloperBankAccountResponse(DeveloperBankAccountBase):
    id: int
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
