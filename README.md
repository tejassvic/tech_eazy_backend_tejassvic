# Zero Mile Delivery System

A minimal FastAPI backend for managing parcel deliveries with async SQLite database.

## Project Structure

```
TechEazy/
├── main.py              # FastAPI app and routes
├── models.py            # SQLAlchemy models and Pydantic schemas
├── database.py          # Database configuration and session management
├── service.py           # Business logic and repository operations
├── requirements.txt     # Python dependencies
├── proj.db             # SQLite database file (auto-created)
├── .gitignore          # Git ignore rules
├── README.md           # This file
└── postman_collection.json  # Postman collection for API testing
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd TechEazy
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Start the server**
   ```bash
   uvicorn main:app --reload
   ```

2. **Access the API**
   - API Base URL: `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`

## API Endpoints

### Parcel Management

#### Create a Parcel
```http
POST /parcels
Content-Type: application/json

{
  "customer_name": "John Doe",
  "delivery_address": "123 Main St, City, State 12345",
  "contact_number": "+1234567890",
  "parcel_size": "Medium",
  "parcel_weight": 2.5
}
```

#### Get All Parcels
```http
GET /parcels
```

#### Get Parcel by Tracking ID
```http
GET /parcels/{tracking_id}
```

## Data Models

### Parcel Model
```python
{
  "tracking_id": "string (auto-generated UUID)",
  "customer_name": "string (1-100 chars)",
  "delivery_address": "string (1-200 chars)",
  "contact_number": "string (1-20 chars)",
  "parcel_size": "string (Small/Medium/Large)",
  "parcel_weight": "float (0.1-1000 kg)",
  "status": "string (Pending/In Transit/Delivered/Failed)"
}
```

## Validation Rules

- **Parcel Size**: Must be one of: `Small`, `Medium`, `Large`
- **Parcel Weight**: Must be between 0.1 and 1000 kg
- **Status**: Must be one of: `Pending`, `In Transit`, `Delivered`, `Failed`
- **Customer Name**: 1-100 characters
- **Delivery Address**: 1-200 characters
- **Contact Number**: 1-20 characters


## Error Handling

- **404**: Parcel not found
- **409**: Duplicate tracking ID
- **422**: Validation error (invalid input data)
- **500**: Internal server error