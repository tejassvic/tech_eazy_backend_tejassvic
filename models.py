from pydantic import BaseModel, Field, validator
from typing import Optional, List
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.declarative import declarative_base
from database import Base
from datetime import datetime
from enum import Enum

class SubscriptionType(str, Enum):
    NORMAL = "NORMAL"
    PRIME = "PRIME"
    VIP = "VIP"

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    VENDOR = "VENDOR"
    DELIVERY_AGENT = "DELIVERY_AGENT"
    CUSTOMER = "CUSTOMER"

class VendorORM(Base):
    __tablename__ = "vendors"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    subscription_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    delivery_orders = relationship("DeliveryOrderORM", back_populates="vendor")

class DeliveryOrderORM(Base):
    __tablename__ = "delivery_orders"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=False)
    delivery_date = Column(DateTime, nullable=False)
    file_path = Column(String, nullable=False)
    total_orders = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    vendor = relationship("VendorORM", back_populates="delivery_orders")
    parcels = relationship("ParcelORM", back_populates="delivery_order")

class UserORM(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="CUSTOMER")
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=True)
    is_active = Column(String, default="True")
    created_at = Column(DateTime, default=datetime.utcnow)

class ParcelORM(Base):
    __tablename__ = "parcels"
    tracking_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_name = Column(String, nullable=False)
    delivery_address = Column(String, nullable=False)
    contact_number = Column(String, nullable=False)
    parcel_size = Column(String, nullable=False)
    parcel_weight = Column(Float, nullable=False)
    status = Column(String, default="Pending")
    delivery_order_id = Column(String, ForeignKey("delivery_orders.id"), nullable=True)
    delivery_order = relationship("DeliveryOrderORM", back_populates="parcels")

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

class VendorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    subscription_type: SubscriptionType

class VendorCreate(VendorBase):
    pass

class Vendor(VendorBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DeliveryOrderBase(BaseModel):
    vendor_id: str
    delivery_date: datetime
    total_orders: int = Field(..., ge=0)

class DeliveryOrderCreate(DeliveryOrderBase):
    pass

class DeliveryOrder(DeliveryOrderBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DeliveryOrderDTO(BaseModel):
    date: datetime
    vendor_name: str
    total_orders: int
    file_link: str

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.CUSTOMER

class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: UserRole = UserRole.CUSTOMER
    vendor_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None 