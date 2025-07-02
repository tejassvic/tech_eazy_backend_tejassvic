from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, UploadFile
from database import AsyncSessionLocal
from models import (
    Parcel, ParcelCreate, ParcelORM, Vendor, VendorCreate, VendorORM,
    DeliveryOrder, DeliveryOrderCreate, DeliveryOrderORM, DeliveryOrderDTO,
    User, UserCreate, UserORM, SubscriptionType, UserRole
)
from auth import get_password_hash, create_access_token
from datetime import datetime, timedelta
import csv
import io
import os

class ParcelRepo:
    async def add_parcel(self, parcel_data: ParcelCreate) -> Parcel:
        async with AsyncSessionLocal() as session:
            try:
                db_parcel = ParcelORM(**parcel_data.dict())
                session.add(db_parcel)
                await session.commit()
                await session.refresh(db_parcel)
                return Parcel(**db_parcel.__dict__)
            except IntegrityError:
                await session.rollback()
                raise HTTPException(
                    status_code=409, 
                    detail="A parcel with this tracking ID already exists"
                )

    async def get_parcel(self, tracking_id: str) -> Optional[Parcel]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ParcelORM).where(ParcelORM.tracking_id == tracking_id))
            db_parcel = result.scalar_one_or_none()
            if db_parcel:
                return Parcel(**db_parcel.__dict__)
            return None

    async def list_parcels(self, skip: int = 0, limit: int = 10) -> List[Parcel]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ParcelORM).offset(skip).limit(limit))
            parcels = result.scalars().all()
            return [Parcel(**p.__dict__) for p in parcels]

    async def group_parcels_by_area_and_size(self) -> List[Tuple[str, str, int]]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ParcelORM.delivery_address, ParcelORM.parcel_size, func.count(ParcelORM.tracking_id))
                .group_by(ParcelORM.delivery_address, ParcelORM.parcel_size)
            )
            rows = result.all()
            return [(str(row[0]), str(row[1]), int(row[2])) for row in rows]

    async def group_parcels_by_status(self) -> Dict[str, int]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ParcelORM.status, func.count(ParcelORM.tracking_id))
                .group_by(ParcelORM.status)
            )
            rows = result.all()
            return {str(row[0]): int(row[1]) for row in rows}

    async def group_parcels_by_size(self) -> Dict[str, int]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ParcelORM.parcel_size, func.count(ParcelORM.tracking_id))
                .group_by(ParcelORM.parcel_size)
            )
            rows = result.all()
            return {str(row[0]): int(row[1]) for row in rows}

    async def get_parcels_by_delivery_order(self, order_id: str, skip: int = 0, limit: int = 10) -> List[Parcel]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ParcelORM)
                .where(ParcelORM.delivery_order_id == order_id)
                .offset(skip).limit(limit)
            )
            parcels = result.scalars().all()
            return [Parcel(**p.__dict__) for p in parcels]

    async def get_parcels_by_vendor(self, vendor_id: str, skip: int = 0, limit: int = 10) -> List[Parcel]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ParcelORM)
                .join(DeliveryOrderORM, ParcelORM.delivery_order_id == DeliveryOrderORM.id)
                .where(DeliveryOrderORM.vendor_id == vendor_id)
                .offset(skip).limit(limit)
            )
            parcels = result.scalars().all()
            return [Parcel(**p.__dict__) for p in parcels]

    async def get_count(self) -> int:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(func.count(ParcelORM.tracking_id)))
            return result.scalar() or 0

class VendorRepo:
    async def create_vendor(self, vendor_data: VendorCreate) -> Vendor:
        async with AsyncSessionLocal() as session:
            try:
                db_vendor = VendorORM(**vendor_data.dict())
                session.add(db_vendor)
                await session.commit()
                await session.refresh(db_vendor)
                return Vendor(**db_vendor.__dict__)
            except IntegrityError:
                await session.rollback()
                raise HTTPException(status_code=409, detail="Vendor name already exists")

    async def get_vendor(self, vendor_id: str) -> Optional[Vendor]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(VendorORM).where(VendorORM.id == vendor_id))
            db_vendor = result.scalar_one_or_none()
            if db_vendor:
                return Vendor(**db_vendor.__dict__)
            return None

    async def list_vendors(self, skip: int = 0, limit: int = 10) -> List[Vendor]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(VendorORM).offset(skip).limit(limit))
            vendors = result.scalars().all()
            return [Vendor(**v.__dict__) for v in vendors]

    async def get_vendor_by_name(self, name: str) -> Optional[Vendor]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(VendorORM).where(VendorORM.name == name))
            db_vendor = result.scalar_one_or_none()
            if db_vendor:
                return Vendor(**db_vendor.__dict__)
            return None

    async def get_count(self) -> int:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(func.count(VendorORM.id)))
            return result.scalar() or 0

class DeliveryOrderRepo:
    async def create_delivery_order(self, order_data: DeliveryOrderCreate, file_path: str) -> DeliveryOrder:
        async with AsyncSessionLocal() as session:
            try:
                db_order = DeliveryOrderORM(**order_data.dict(), file_path=file_path)
                session.add(db_order)
                await session.commit()
                await session.refresh(db_order)
                return DeliveryOrder(**db_order.__dict__)
            except IntegrityError:
                await session.rollback()
                raise HTTPException(status_code=409, detail="Error creating delivery order")

    async def get_delivery_order(self, order_id: str) -> Optional[DeliveryOrder]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(DeliveryOrderORM).where(DeliveryOrderORM.id == order_id))
            db_order = result.scalar_one_or_none()
            if db_order:
                return DeliveryOrder(**db_order.__dict__)
            return None

    async def list_delivery_orders_today(self, skip: int = 0, limit: int = 10) -> List[DeliveryOrderDTO]:
        async with AsyncSessionLocal() as session:
            today = datetime.now().date()
            result = await session.execute(
                select(DeliveryOrderORM, VendorORM.name)
                .join(VendorORM, DeliveryOrderORM.vendor_id == VendorORM.id)
                .where(func.date(DeliveryOrderORM.delivery_date) == today)
                .offset(skip).limit(limit)
            )
            orders = result.all()
            return [
                DeliveryOrderDTO(
                    date=order[0].delivery_date,
                    vendor_name=order[1],
                    total_orders=order[0].total_orders,
                    file_link=f"/files/{order[0].file_path}"
                ) for order in orders
            ]

    async def list_delivery_orders_by_vendor_and_date(
        self, vendor_id: str, date: datetime, skip: int = 0, limit: int = 10
    ) -> List[DeliveryOrderDTO]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(DeliveryOrderORM, VendorORM.name)
                .join(VendorORM, DeliveryOrderORM.vendor_id == VendorORM.id)
                .where(
                    DeliveryOrderORM.vendor_id == vendor_id,
                    func.date(DeliveryOrderORM.delivery_date) == date.date()
                )
                .offset(skip).limit(limit)
            )
            orders = result.all()
            return [
                DeliveryOrderDTO(
                    date=order[0].delivery_date,
                    vendor_name=order[1],
                    total_orders=order[0].total_orders,
                    file_link=f"/files/{order[0].file_path}"
                ) for order in orders
            ]

    async def process_parcel_file(self, file: UploadFile, delivery_order_id: str) -> int:
        async with AsyncSessionLocal() as session:
            content = await file.read()
            text = content.decode('utf-8')
            
            parcels_created = 0
            for line in text.strip().split('\n'):
                if line.strip():
                    try:
                        parts = line.split(',')
                        if len(parts) >= 5:
                            parcel_data = ParcelCreate(
                                customer_name=parts[0].strip(),
                                delivery_address=parts[1].strip(),
                                contact_number=parts[2].strip(),
                                parcel_size=parts[3].strip(),
                                parcel_weight=float(parts[4].strip())
                            )
                            db_parcel = ParcelORM(**parcel_data.dict(), delivery_order_id=delivery_order_id)
                            session.add(db_parcel)
                            parcels_created += 1
                    except Exception as e:
                        continue
            
            await session.commit()
            return parcels_created

    async def get_count(self) -> int:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(func.count(DeliveryOrderORM.id)))
            return result.scalar() or 0

class UserRepo:
    async def create_user(self, user_data: UserCreate) -> User:
        async with AsyncSessionLocal() as session:
            try:
                hashed_password = get_password_hash(user_data.password)
                db_user = UserORM(
                    username=user_data.username,
                    email=user_data.email,
                    hashed_password=hashed_password,
                    role=user_data.role.value
                )
                session.add(db_user)
                await session.commit()
                await session.refresh(db_user)
                return User(**db_user.__dict__)
            except IntegrityError:
                await session.rollback()
                raise HTTPException(status_code=409, detail="Username or email already exists")

    async def get_user_by_username(self, username: str) -> Optional[UserORM]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(UserORM).where(UserORM.username == username))
            return result.scalar_one_or_none()

    async def list_users(self, skip: int = 0, limit: int = 10) -> List[User]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(UserORM).offset(skip).limit(limit))
            users = result.scalars().all()
            return [User(**u.__dict__) for u in users]

parcel_repo = ParcelRepo()
vendor_repo = VendorRepo()
delivery_order_repo = DeliveryOrderRepo()
user_repo = UserRepo()

async def create_parcel(parcel_data: ParcelCreate) -> Parcel:
    return await parcel_repo.add_parcel(parcel_data)

async def get_parcel(tracking_id: str) -> Optional[Parcel]:
    return await parcel_repo.get_parcel(tracking_id)

async def list_parcels(skip: int = 0, limit: int = 10) -> List[Parcel]:
    return await parcel_repo.list_parcels(skip, limit)

async def group_parcels_by_status() -> Dict[str, int]:
    return await parcel_repo.group_parcels_by_status()

async def group_parcels_by_size() -> Dict[str, int]:
    return await parcel_repo.group_parcels_by_size()

async def create_vendor(vendor_data: VendorCreate) -> Vendor:
    return await vendor_repo.create_vendor(vendor_data)

async def get_vendor(vendor_id: str) -> Optional[Vendor]:
    return await vendor_repo.get_vendor(vendor_id)

async def list_vendors(skip: int = 0, limit: int = 10) -> List[Vendor]:
    return await vendor_repo.list_vendors(skip, limit)

async def create_delivery_order(order_data: DeliveryOrderCreate, file: UploadFile) -> DeliveryOrder:
    file_path = f"uploads/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    os.makedirs("uploads", exist_ok=True)
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    order = await delivery_order_repo.create_delivery_order(order_data, file_path)
    await delivery_order_repo.process_parcel_file(file, order.id)
    return order

async def get_delivery_orders_today(skip: int = 0, limit: int = 10) -> List[DeliveryOrderDTO]:
    return await delivery_order_repo.list_delivery_orders_today(skip, limit)

async def get_delivery_orders_by_vendor_and_date(
    vendor_id: str, date: datetime, skip: int = 0, limit: int = 10
) -> List[DeliveryOrderDTO]:
    return await delivery_order_repo.list_delivery_orders_by_vendor_and_date(vendor_id, date, skip, limit)

async def create_user(user_data: UserCreate) -> User:
    return await user_repo.create_user(user_data)

async def authenticate_and_create_token(username: str, password: str):
    from auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
    from datetime import timedelta
    
    user = await authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

async def get_parcels_by_delivery_order(order_id: str, skip: int = 0, limit: int = 10) -> List[Parcel]:
    return await parcel_repo.get_parcels_by_delivery_order(order_id, skip, limit)

async def get_parcels_by_vendor(vendor_id: str, skip: int = 0, limit: int = 10) -> List[Parcel]:
    return await parcel_repo.get_parcels_by_vendor(vendor_id, skip, limit)

async def list_users(skip: int = 0, limit: int = 10) -> List[User]:
    return await user_repo.list_users(skip, limit)

async def get_vendor_count() -> int:
    return await vendor_repo.get_count()

async def get_parcel_count() -> int:
    return await parcel_repo.get_count()

async def get_delivery_order_count() -> int:
    return await delivery_order_repo.get_count() 