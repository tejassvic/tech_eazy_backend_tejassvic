from fastapi import FastAPI, HTTPException
from typing import List
from models import Parcel, ParcelCreate
import service
from database import engine, Base

app = FastAPI(title="Zero Mile Delivery System")

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/parcels", response_model=List[Parcel], tags=["Parcels"])
async def get_all_parcels():
    return await service.list_parcels()

@app.get("/parcels/{tracking_id}", response_model=Parcel, tags=["Parcels"])
async def get_parcel(tracking_id: str):
    parcel = await service.get_parcel(tracking_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    return parcel

@app.post("/parcels", response_model=Parcel, status_code=201, tags=["Parcels"])
async def create_parcel(parcel_data: ParcelCreate):
    return await service.create_parcel(parcel_data) 