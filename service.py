from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from database import AsyncSessionLocal
from models import Parcel, ParcelCreate, ParcelORM

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

    async def list_parcels(self) -> List[Parcel]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ParcelORM))
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

parcel_repo = ParcelRepo()

async def create_parcel(parcel_data: ParcelCreate) -> Parcel:
    return await parcel_repo.add_parcel(parcel_data)

async def get_parcel(tracking_id: str) -> Optional[Parcel]:
    return await parcel_repo.get_parcel(tracking_id)

async def list_parcels() -> List[Parcel]:
    return await parcel_repo.list_parcels()

async def group_parcels_by_status() -> Dict[str, int]:
    return await parcel_repo.group_parcels_by_status()

async def group_parcels_by_size() -> Dict[str, int]:
    return await parcel_repo.group_parcels_by_size() 