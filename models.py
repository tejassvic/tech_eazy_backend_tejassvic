from pydantic import BaseModel, Field, validator
from typing import Optional
import uuid
from sqlalchemy import Column, String, Float
from sqlalchemy.orm import declarative_base
from database import Base

class ParcelORM(Base):
    __tablename__ = "parcels"
    tracking_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_name = Column(String, nullable=False)
    delivery_address = Column(String, nullable=False)
    contact_number = Column(String, nullable=False)
    parcel_size = Column(String, nullable=False)
    parcel_weight = Column(Float, nullable=False)
    status = Column(String, default="Pending")

class ParcelBase(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=100)
    delivery_address: str = Field(..., min_length=1, max_length=200)
    contact_number: str = Field(..., min_length=1, max_length=20)
    parcel_size: str = Field(..., min_length=1, max_length=20)
    parcel_weight: float = Field(..., gt=0, le=1000)

    @validator('parcel_size')
    def validate_parcel_size(cls, v):
        valid_sizes = ['Small', 'Medium', 'Large']
        if v not in valid_sizes:
            raise ValueError(f'Parcel size must be one of: {", ".join(valid_sizes)}')
        return v

class ParcelCreate(ParcelBase):
    pass

class Parcel(ParcelBase):
    tracking_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "Pending"

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['Pending', 'In Transit', 'Delivered', 'Failed']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v 