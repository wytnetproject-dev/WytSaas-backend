from typing import Optional, List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.enquiry import Enquiry
from schemas.enquiry import EnquiryCreate

async def get_enquiry_by_id(db: AsyncSession, enquiry_id: int) -> Optional[Enquiry]:
    """Retrieve an enquiry by its ID."""
    result = await db.execute(select(Enquiry).where(Enquiry.id == enquiry_id))
    return result.scalars().first()

async def get_enquiries(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Enquiry]:
    """Retrieve a paginated list of inquiries."""
    result = await db.execute(
        select(Enquiry).offset(skip).limit(limit).order_by(Enquiry.created_at.desc())
    )
    return list(result.scalars().all())

async def create_enquiry(db: AsyncSession, enquiry: EnquiryCreate) -> Enquiry:
    """Create a new enquiry record."""
    db_enquiry = Enquiry(
        first_name=enquiry.first_name,
        last_name=enquiry.last_name,
        email=enquiry.email,
        phone=enquiry.phone,
        message=enquiry.message,
        terms_accepted=enquiry.terms_accepted,
    )
    db.add(db_enquiry)
    await db.commit()
    await db.refresh(db_enquiry)
    return db_enquiry

async def delete_enquiry(db: AsyncSession, enquiry_id: int) -> bool:
    """Delete an enquiry by its ID."""
    query = delete(Enquiry).where(Enquiry.id == enquiry_id)
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0
