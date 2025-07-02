from enum import Enum
from typing import List, Set
from fastapi import HTTPException, status
from models import UserRole

class Permission(str, Enum):
    # Vendor permissions
    CREATE_VENDOR = "CREATE_VENDOR"
    READ_VENDOR = "READ_VENDOR"
    UPDATE_VENDOR = "UPDATE_VENDOR"
    DELETE_VENDOR = "DELETE_VENDOR"
    LIST_VENDORS = "LIST_VENDORS"
    
    # Delivery Order permissions
    CREATE_DELIVERY_ORDER = "CREATE_DELIVERY_ORDER"
    READ_DELIVERY_ORDER = "READ_DELIVERY_ORDER"
    UPDATE_DELIVERY_ORDER = "UPDATE_DELIVERY_ORDER"
    DELETE_DELIVERY_ORDER = "DELETE_DELIVERY_ORDER"
    LIST_DELIVERY_ORDERS = "LIST_DELIVERY_ORDERS"
    
    # Parcel permissions
    CREATE_PARCEL = "CREATE_PARCEL"
    READ_PARCEL = "READ_PARCEL"
    UPDATE_PARCEL = "UPDATE_PARCEL"
    DELETE_PARCEL = "DELETE_PARCEL"
    LIST_PARCELS = "LIST_PARCELS"
    UPDATE_PARCEL_STATUS = "UPDATE_PARCEL_STATUS"
    
    # User permissions
    CREATE_USER = "CREATE_USER"
    READ_USER = "READ_USER"
    UPDATE_USER = "UPDATE_USER"
    DELETE_USER = "DELETE_USER"
    LIST_USERS = "LIST_USERS"
    
    # File permissions
    UPLOAD_FILE = "UPLOAD_FILE"
    DOWNLOAD_FILE = "DOWNLOAD_FILE"

# Role-based permissions mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        Permission.CREATE_VENDOR,
        Permission.READ_VENDOR,
        Permission.UPDATE_VENDOR,
        Permission.DELETE_VENDOR,
        Permission.LIST_VENDORS,
        Permission.CREATE_DELIVERY_ORDER,
        Permission.READ_DELIVERY_ORDER,
        Permission.UPDATE_DELIVERY_ORDER,
        Permission.DELETE_DELIVERY_ORDER,
        Permission.LIST_DELIVERY_ORDERS,
        Permission.CREATE_PARCEL,
        Permission.READ_PARCEL,
        Permission.UPDATE_PARCEL,
        Permission.DELETE_PARCEL,
        Permission.LIST_PARCELS,
        Permission.UPDATE_PARCEL_STATUS,
        Permission.CREATE_USER,
        Permission.READ_USER,
        Permission.UPDATE_USER,
        Permission.DELETE_USER,
        Permission.LIST_USERS,
        Permission.UPLOAD_FILE,
        Permission.DOWNLOAD_FILE,
    },
    UserRole.VENDOR: {
        Permission.READ_VENDOR,  # Only their own vendor info
        Permission.CREATE_DELIVERY_ORDER,
        Permission.READ_DELIVERY_ORDER,  # Only their own orders
        Permission.LIST_DELIVERY_ORDERS,  # Only their own orders
        Permission.CREATE_PARCEL,
        Permission.READ_PARCEL,  # Only their own parcels
        Permission.LIST_PARCELS,  # Only their own parcels
        Permission.UPLOAD_FILE,
        Permission.DOWNLOAD_FILE,  # Only their own files
    },
    UserRole.DELIVERY_AGENT: {
        Permission.READ_PARCEL,  # Only assigned parcels
        Permission.UPDATE_PARCEL_STATUS,  # Update delivery status
        Permission.LIST_PARCELS,  # Only assigned parcels
        Permission.READ_DELIVERY_ORDER,  # Only assigned orders
        Permission.LIST_DELIVERY_ORDERS,  # Only assigned orders
    },
    UserRole.CUSTOMER: {
        Permission.READ_PARCEL,  # Only their own parcels
        Permission.LIST_PARCELS,  # Only their own parcels
    }
}

def get_user_permissions(role: UserRole) -> Set[Permission]:
    """Get permissions for a specific user role"""
    return ROLE_PERMISSIONS.get(role, set())

def has_permission(user_role: UserRole, required_permission: Permission) -> bool:
    """Check if a user role has a specific permission"""
    user_permissions = get_user_permissions(user_role)
    return required_permission in user_permissions

def require_permission(required_permission: Permission):
    """Decorator to require a specific permission"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This will be used with dependency injection
            # The actual user will be passed from the endpoint
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def check_vendor_access(user_role: UserRole, user_vendor_id: str, target_vendor_id: str) -> bool:
    """Check if user has access to vendor data"""
    if user_role == UserRole.ADMIN:
        return True
    elif user_role == UserRole.VENDOR:
        return user_vendor_id == target_vendor_id
    return False

def check_delivery_order_access(user_role: UserRole, user_vendor_id: str, order_vendor_id: str) -> bool:
    """Check if user has access to delivery order data"""
    if user_role == UserRole.ADMIN:
        return True
    elif user_role == UserRole.VENDOR:
        return user_vendor_id == order_vendor_id
    elif user_role == UserRole.DELIVERY_AGENT:
        return True  # Delivery agents can see assigned orders
    return False

def check_parcel_access(user_role: UserRole, user_vendor_id: str, parcel_vendor_id: str) -> bool:
    """Check if user has access to parcel data"""
    if user_role == UserRole.ADMIN:
        return True
    elif user_role == UserRole.VENDOR:
        return user_vendor_id == parcel_vendor_id
    elif user_role == UserRole.DELIVERY_AGENT:
        return True  # Delivery agents can see assigned parcels
    elif user_role == UserRole.CUSTOMER:
        return True  # Customers can see their own parcels (would need customer_id in parcel model)
    return False 