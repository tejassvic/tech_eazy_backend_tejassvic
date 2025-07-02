# Zero Mile Delivery System

A comprehensive FastAPI backend for managing delivery operations with vendor management, order processing, and JWT authentication.

## Features

- **Authentication**: JWT-based user authentication and authorization
- **Vendor Management**: Create and manage vendors with subscription types (NORMAL, PRIME, VIP)
- **Delivery Orders**: Upload and manage delivery orders with file processing
- **Parcel Management**: Create and track individual parcels
- **File Upload**: Support for uploading parcel lists as text files
- **Pagination**: Built-in pagination for all list endpoints
- **Async Database**: SQLite with async SQLAlchemy for optimal performance

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite with aiosqlite
- **ORM**: SQLAlchemy (async)
- **Authentication**: JWT with python-jose
- **Password Hashing**: bcrypt with passlib
- **File Upload**: FastAPI UploadFile

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Pagination
All list endpoints support pagination with query parameters:
- `skip`: Number of items to skip (default: 0)
- `limit`: Number of items per page (default: 10, max: 100)

Example: `GET /parcels/?skip=20&limit=5`

### Authentication & User Management
- `POST /register` - Register a new user
- `POST /token` - Login and get JWT token
- `GET /users/me` - Get current user info
- `GET /users/` - List users (Admin only)
- `POST /users/` - Create user (Admin only)
- `GET /protected` - Protected route example

### Role-Based Dashboards
- `GET /admin/dashboard` - Admin dashboard with system stats
- `GET /vendor/dashboard` - Vendor dashboard
- `GET /delivery-agent/dashboard` - Delivery agent dashboard
- `GET /customer/dashboard` - Customer dashboard

### Vendors
- `POST /vendors/` - Create a new vendor
- `GET /vendors/` - List vendors (with pagination)
- `GET /vendors/{vendor_id}` - Get vendor by ID
- `GET /vendors/{vendor_id}/delivery-orders` - Get vendor's delivery orders
- `GET /vendors/{vendor_id}/parcels` - Get vendor's parcels

### Delivery Orders
- `POST /delivery-orders/` - Create delivery order with file upload
- `GET /delivery-orders/today` - Get today's delivery orders
- `GET /delivery-orders/filter` - Filter orders by vendor and date
- `GET /delivery-orders/{order_id}/parcels` - Get delivery order's parcels

### Parcels
- `POST /parcels/` - Create a new parcel
- `GET /parcels/` - List all parcels (with pagination)
- `GET /parcels/{tracking_id}` - Get parcel by tracking ID

### Files
- `GET /files/{file_path}` - Download uploaded files

## Data Models

### Relationships
The system implements the following entity relationships:
- **Vendor → DeliveryOrder (1:Many)**: One vendor can have multiple delivery orders
- **DeliveryOrder → Parcel (1:Many)**: One delivery order can have multiple parcels
- **Vendor → Parcel (1:Many)**: One vendor can have multiple parcels (through delivery orders)

### Vendor
- `id`: Unique identifier
- `name`: Vendor name (unique)
- `subscription_type`: NORMAL, PRIME, or VIP
- `created_at`: Creation timestamp

### DeliveryOrder
- `id`: Unique identifier
- `vendor_id`: Associated vendor
- `delivery_date`: Scheduled delivery date
- `file_path`: Path to uploaded parcel file
- `total_orders`: Number of parcels in order
- `created_at`: Creation timestamp

### Parcel
- `tracking_id`: Unique tracking identifier
- `customer_name`: Customer's name
- `delivery_address`: Delivery address
- `contact_number`: Customer contact
- `parcel_size`: Small, Medium, or Large
- `parcel_weight`: Weight in kg
- `status`: Current delivery status
- `delivery_order_id`: Associated delivery order

### User
- `id`: Unique identifier
- `username`: Username (unique)
- `email`: Email address (unique)
- `hashed_password`: Encrypted password
- `role`: User role (ADMIN, VENDOR, DELIVERY_AGENT, CUSTOMER)
- `vendor_id`: Associated vendor (optional)
- `is_active`: Account status
- `created_at`: Creation timestamp

### User Roles and Permissions

#### **ADMIN**
- Full system access
- Can manage all vendors, users, delivery orders
- System configuration and monitoring
- Dashboard with system statistics

#### **VENDOR**
- Can manage their own delivery orders
- Upload parcel files
- View their delivery history
- Manage their vendor profile
- Access to vendor-specific data only

#### **DELIVERY_AGENT**
- View assigned parcels
- Update parcel status (In Transit, Delivered, Failed)
- Access to delivery routes and customer information
- View assigned delivery orders

#### **CUSTOMER**
- Track their parcels
- View delivery status
- Basic account management
- Access to their own parcel data only

## File Upload Format

Delivery orders accept `.txt` files with the following format:
```
CustomerName,DeliveryAddress,ContactNumber,ParcelSize,ParcelWeight
John Doe,123 Main St,City,State 12345,+1234567890,Medium,2.5
Jane Smith,456 Oak Ave,Town,State 67890,+0987654321,Small,1.0
```

## Authentication Flow

1. Register a user: `POST /register`
2. Login to get token: `POST /token`
3. Use token in Authorization header: `Bearer <token>`

## Database

The system uses SQLite with automatic table creation on startup. The database file is created as `proj.db` in the project root.

## Project Structure

```
TechEazy/
├── main.py              # FastAPI application and routes
├── models.py            # Pydantic models and SQLAlchemy ORM
├── services.py          # Business logic and repositories
├── database.py          # Database configuration
├── auth.py              # JWT authentication utilities
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── postman_collection.json # API testing collection
```

## Testing

Import the provided Postman collection to test all endpoints. The collection includes:
- Authentication flows
- Vendor management
- Delivery order creation and filtering
- Parcel operations
- File downloads

## Security Notes

- Change the `SECRET_KEY` in `auth.py` for production (afc would not hardcode in code in future version, was a bit confused with creating a .ini/.env file because of structure strictness)
- Use environment variables for sensitive configuration
- Implement proper CORS settings for production
- Consider using HTTPS in production

## Development

The system is designed for easy extension:
- Add new models in `models.py`
- Implement repositories in `services.py`
- Add endpoints in `main.py`
- Update authentication as needed