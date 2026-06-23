from sqlalchemy import Column, String, Text, Boolean, DateTime, BigInteger
from sqlalchemy.sql import func
from db.db import Base

class Enquiry(Base):
    """Enquiry model for user messages, contact forms, and inquiries."""
    __tablename__ = "enquiries"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(30), nullable=True)
    message = Column(Text, nullable=False)
    terms_accepted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
