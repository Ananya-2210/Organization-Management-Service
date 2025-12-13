# Organization Management Service (Backend Intern Assignment)

A backend service for managing organizations in a **multi-tenant architecture** using **FastAPI** and **MongoDB**.  
Each organization gets its own isolated database, while a **master database** stores global metadata and admin credentials.

---
## Architecture Diagram

[![Architecture Diagram](images/Architecture-Diagram.png)](images/Architecture-Diagram.png)



### Key Components:

- **Client Layer**: Users interact via Swagger UI or any HTTP client
- **API Layer**: FastAPI handles all REST endpoints with JWT authentication
- **Data Layer**: 
  - **master_database**: Stores organization metadata and admin credentials
  - **Tenant Databases**: Each organization has isolated data storage

### Request Flow:

1. Client sends HTTP requests to FastAPI endpoints
2. POST /org/create stores metadata in master DB and creates new tenant database
3. POST /admin/login validates credentials and issues JWT token
4. Protected operations (update/delete) require JWT authentication
5. All passwords are hashed with Argon2 before storage


## Setup Instructions

### Prerequisites

- Python 3.11+
- MongoDB (local Community Server or MongoDB Atlas)
- `pip` (Python package manager)
- Git (optional but recommended)

### 1. Clone the Repository

git clone <your-repo-url>.git
cd <your-repo-folder>


### 2. Create and Activate Virtual Environment (recommended)

python -m venv venv

Windows
venv\Scripts\activate

macOS / Linux
source venv/bin/activate


### 3. Install Dependencies

pip install -r requirements.txt

### 4. Configure Environment Variables

Create a `.env` file in the project root:
MONGODB_URL=mongodb://localhost:27017/
MASTER_DB_NAME=master_database
SECRET_KEY=replace-with-a-long-random-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30


If you use MongoDB Atlas, replace `MONGODB_URL` with your Atlas connection string.

### 5. Run the Application
uvicorn app.main:app --reload


The API will be available at:

- Base URL: `http://127.0.0.1:8000/`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## Tech Stack Used

- **Language:** Python
- **Framework:** FastAPI
- **Database:** MongoDB (PyMongo)
- **Auth:** JWT (JSON Web Tokens)
- **Password Hashing:** Argon2 (Passlib)
- **Config Management:** pydantic-settings
- **Server:** Uvicorn
- **Testing:** pytest, FastAPI TestClient

---

## API Endpoints

### 1. Create Organization

- **Method:** `POST`
- **URL:** `/org/create`

**Request body example:**
{
"organization_name": "Shiney",
"email": "shiney@gunnu.com",
"password": "strongpassword123"
}

**Behavior:**

- Validates that `organization_name` does not already exist.
- Creates a new database and collection for the organization (e.g. `org_Shiney`).
- Inserts an initial document so the DB appears in MongoDB tools.
- Stores metadata in the master database (`master_database.organizations`):
  - `organization_name`
  - `collection_name`
  - `admin_email`
  - `admin_password` (hashed using Argon2)
  - `created_at`
- Returns basic organization metadata.

---

### 2. Get Organization by Name

- **Method:** `GET`
- **URL:** `/org/get`
- **Query parameter:** `organization_name`

**Behavior:**

- Looks up the organization in the master database by `organization_name`.
- Returns organization metadata (excluding the hashed password).
- Returns **404** if the organization does not exist.

---

### 3. Update Organization

- **Method:** `PUT`
- **URL:** `/org/update`

**Request body example:**
{
"organization_name": "ShineyRenamed",
"email": "shiney@gunnu.com",
"password": "newpassword123"
}

**Behavior:**

- Identifies the organization by `admin_email` (the `email` field).
- Validates that the new `organization_name` does not conflict with any other existing organization.
- Creates a new database/collection for the new name.
- Migrates all data from the old organization collection to the new one.
- Updates in the master database:
  - `organization_name`
  - `collection_name`
  - `admin_email` (if changed)
  - `admin_password` (re-hashed)
- Drops the old organization database if the name changed.
- Returns a success message.

---

### 4. Delete Organization

- **Method:** `DELETE`
- **URL:** `/org/delete`
- **Query parameter:** `organization_name`
- **Auth:** Requires Bearer JWT token

**Behavior:**

- Protected using HTTP Bearer authentication (JWT).
- Verifies the JWT and extracts `organization_id` from the token payload.
- Ensures the authenticated admin belongs to the organization being deleted.
- Drops the organization database.
- Deletes the organization document from the master database.
- Returns a success message.

---

### 5. Admin Login

- **Method:** `POST`
- **URL:** `/admin/login`

**Request body example:**
{
"email": "shiney@gunnu.com",
"password": "strongpassword123"
}


**Behavior:**

- Looks up the admin by `admin_email` in the master database.
- Verifies the password using Argon2 hashing.
- On success, returns a JWT containing:
  - `admin_id`
  - `organization_id` (organization name)
  - `email`
- On failure, returns **401 Unauthorized**.

---

## Using the Authorization Button in Swagger UI

The project integrates HTTP Bearer authentication with Swagger UI to make testing protected endpoints easy.

1. Open `http://127.0.0.1:8000/docs`.
2. Call **`POST /admin/login`** with a valid email and password to get an `access_token`.
3. Click the **“Authorize”** button (padlock icon in the top-right of Swagger UI).
4. In the popup for the Bearer auth scheme, paste **only** the raw JWT token (no need to type `Bearer`).
5. Click **“Authorize”**, then **“Close”**.

After this, Swagger will automatically include the `Authorization: Bearer <token>` header for all protected endpoints such as **`DELETE /org/delete`**. You no longer need to manually add the header to each request.

---

## Multi-Tenant Architecture Design

### Master Database

A dedicated database (`MASTER_DB_NAME`, e.g. `master_database`) stores global metadata:

- `organizations` collection:
  - `_id`
  - `organization_name`
  - `collection_name`
  - `admin_email`
  - `admin_password` (hashed)
  - `created_at`

This supports quick lookup of tenants and their corresponding databases/collections.

### Dynamic Organization Databases

For each organization:

- A separate database is created: `org_<organization_name>`.
- Inside that database, a main collection (e.g. `data`) holds tenant-specific data.
- An `_initialized` document is inserted to ensure the database is materialized and visible in MongoDB Compass.

**Benefits:**

- Logical isolation of each tenant’s data.
- Easier backup/restore per organization.
- Flexibility to evolve tenant schemas independently.

---

## Authentication & Security

- **JWT Authentication**
  - Admin login issues a signed JWT.
  - Protected routes use HTTP Bearer auth and verify the token.
  - Token payload includes both admin identification and organization identifier.

- **Password Hashing**
  - Uses Argon2 via Passlib.
  - Plain-text passwords are never stored; only secure hashes are persisted.

- **Authorization Rules**
  - Delete operation checks that the token’s `organization_id` matches the organization being deleted.
  - Prevents one tenant from deleting or modifying another tenant’s organization.

---

## Tests

Automated tests are implemented with **pytest** and FastAPI’s `TestClient`.

Run tests with:
pytest -v


### Covered Scenarios

- Create organization (success + duplicate name validation)
- Get organization (success + 404 not found)
- Admin login:
  - Success
  - Wrong password
  - Non-existent email
- Update organization (success + not found)
- Delete organization:
  - Without auth token (edge case)
  - With valid auth token (success)
- Validation:
  - Invalid email format
  - Missing required fields

All tests currently pass.

---

## Key Design Choices & Trade-Offs

- **FastAPI + MongoDB**
  - Very productive for JSON APIs, async-friendly.
  - MongoDB matches well with flexible tenant-specific data.
  - Trade-off: Complex relational joins across tenants are not the focus.

- **Per-Organization Database**
  - Strong logical isolation and clear data separation.
  - Trade-off: At large scale, many databases can add management and resource overhead.

- **Master Metadata Database**
  - Central point for organization and admin metadata.
  - Trade-off: Critical component that must be backed up and monitored carefully.

---

## Assumptions

- All organizations share the same MongoDB cluster/instance; each has its own database name.
- Per-organization connection details are not stored separately because a single cluster is sufficient for this assignment.
- Admins are scoped per organization; cross-tenant admin roles are out of scope.

---

## How to Use This Project for the Assignment

1. Implement backend as described (already done in this repo).
2. Run all tests with `pytest -v` and verify they pass.
3. Start the app and test endpoints using Swagger UI with the Authorize button.
4. Export or screenshot your architecture diagram and reference it from this README or submit it separately.
5. Share your GitHub repo link and (optionally) a short design explanation as requested in the assignment.






