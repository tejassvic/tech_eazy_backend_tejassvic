from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Optional
from datetime import datetime
import os
from models import (
    Parcel, ParcelCreate, Vendor, VendorCreate, DeliveryOrder, DeliveryOrderCreate,
    DeliveryOrderDTO, User, UserCreate, Token
)
from services import (
    create_parcel, get_parcel, list_parcels, create_vendor, get_vendor, list_vendors,
    create_delivery_order, get_delivery_orders_today, get_delivery_orders_by_vendor_and_date,
    create_user, authenticate_and_create_token, get_parcels_by_delivery_order, get_parcels_by_vendor,
    list_users, get_vendor_count, get_parcel_count, get_delivery_order_count
)
from auth import get_current_user, require_role, require_permission
from permissions import Permission
from models import UserRole
from database import engine, Base

app = FastAPI(title="Zero Mile Delivery System", version="1.0.0")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if not os.path.exists("uploads"):
    os.makedirs("uploads")
app.mount("/files", StaticFiles(directory="uploads"), name="files")

@app.post("/parcels/", response_model=Parcel)
async def create_parcel_endpoint(parcel: ParcelCreate):
    return await create_parcel(parcel)

@app.get("/parcels/", response_model=List[Parcel])
async def list_parcels_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    return await list_parcels(skip, limit)

@app.get("/parcels/{tracking_id}", response_model=Parcel)
async def get_parcel_endpoint(tracking_id: str):
    parcel = await get_parcel(tracking_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    return parcel

@app.post("/vendors/", response_model=Vendor)
async def create_vendor_endpoint(vendor: VendorCreate):
    return await create_vendor(vendor)

@app.get("/vendors/", response_model=List[Vendor])
async def list_vendors_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    return await list_vendors(skip, limit)

@app.get("/vendors/{vendor_id}", response_model=Vendor)
async def get_vendor_endpoint(vendor_id: str):
    vendor = await get_vendor(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor

@app.post("/delivery-orders/", response_model=DeliveryOrder)
async def create_delivery_order_endpoint(
    vendor_id: str,
    delivery_date: datetime,
    total_orders: int,
    file: UploadFile = File(...)
):
    if not file.filename or not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="File must be a .txt file")
    
    order_data = DeliveryOrderCreate(
        vendor_id=vendor_id,
        delivery_date=delivery_date,
        total_orders=total_orders
    )
    
    return await create_delivery_order(order_data, file)

@app.get("/delivery-orders/today", response_model=List[DeliveryOrderDTO])
async def get_delivery_orders_today_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    return await get_delivery_orders_today(skip, limit)

@app.get("/delivery-orders/filter", response_model=List[DeliveryOrderDTO])
async def get_delivery_orders_by_vendor_and_date_endpoint(
    vendor_id: str,
    date: datetime,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    return await get_delivery_orders_by_vendor_and_date(vendor_id, date, skip, limit)

@app.post("/register", response_model=User)
async def register_user(user: UserCreate):
    return await create_user(user)

@app.post("/token", response_model=Token)
async def login_for_access_token(username: str, password: str):
    return await authenticate_and_create_token(username, password)

@app.get("/files/{file_path:path}")
async def download_file(file_path: str):
    full_path = os.path.join("uploads", file_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(full_path)

@app.get("/protected")
async def protected_route(current_user = Depends(get_current_user)):
    return {"message": "This is a protected route", "user": current_user.username}

@app.get("/vendors/{vendor_id}/delivery-orders", response_model=List[DeliveryOrderDTO])
async def get_vendor_delivery_orders_endpoint(
    vendor_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    return await get_delivery_orders_by_vendor_and_date(vendor_id, datetime.now(), skip, limit)

@app.get("/delivery-orders/{order_id}/parcels", response_model=List[Parcel])
async def get_delivery_order_parcels_endpoint(
    order_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    return await get_parcels_by_delivery_order(order_id, skip, limit)

@app.get("/vendors/{vendor_id}/parcels", response_model=List[Parcel])
async def get_vendor_parcels_endpoint(
    vendor_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    return await get_parcels_by_vendor(vendor_id, skip, limit)

@app.get("/users/me", response_model=User)
async def get_current_user_info(current_user = Depends(get_current_user)):
    return User(**current_user.__dict__)

@app.get("/users/", response_model=List[User])
async def list_users_endpoint(
    current_user = Depends(require_permission(Permission.LIST_USERS)),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    return await list_users(skip, limit)

@app.post("/users/", response_model=User)
async def create_user_endpoint(
    user: UserCreate,
    current_user = Depends(require_permission(Permission.CREATE_USER))
):
    return await create_user(user)

@app.get("/admin/dashboard")
async def admin_dashboard(current_user = Depends(require_role(UserRole.ADMIN))):
    return {
        "message": "Admin Dashboard",
        "user": current_user.username,
        "role": current_user.role,
        "stats": {
            "total_vendors": await get_vendor_count(),
            "total_parcels": await get_parcel_count(),
            "total_delivery_orders": await get_delivery_order_count()
        }
    }

@app.get("/vendor/dashboard")
async def vendor_dashboard(current_user = Depends(require_role(UserRole.VENDOR))):
    return {
        "message": "Vendor Dashboard",
        "user": current_user.username,
        "role": current_user.role,
        "vendor_id": current_user.vendor_id
    }

@app.get("/delivery-agent/dashboard")
async def delivery_agent_dashboard(current_user = Depends(require_role(UserRole.DELIVERY_AGENT))):
    return {
        "message": "Delivery Agent Dashboard",
        "user": current_user.username,
        "role": current_user.role
    }

@app.get("/customer/dashboard")
async def customer_dashboard(current_user = Depends(require_role(UserRole.CUSTOMER))):
    return {
        "message": "Customer Dashboard",
        "user": current_user.username,
        "role": current_user.role
    } 