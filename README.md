Organization Management Service (Backend Intern Assignment)
A backend service for managing organizations in a multi-tenant architecture using FastAPI and MongoDB. Each organization gets its own isolated database, while a master database stores global metadata and admin credentials.

Setup Instructions
Prerequisites
Python 3.11+

MongoDB Community Server or MongoDB Atlas account

pip (Python package manager)

Git (optional but recommended)

1. Clone the Repository
bash
git clone <your-repo-url>.git
cd <your-repo-folder>
2. Create and Activate Virtual Environment (recommended)
bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
3. Install Dependencies
bash
pip install -r requirements.txt
4. Configure Environment Variables
Create a .env file in the project root:

text
MONGODB_URL=mongodb://localhost:27017/
MASTER_DB_NAME=master_database
SECRET_KEY=replace-with-a-long-random-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
If you use MongoDB Atlas, replace MONGODB_URL with your Atlas connection string.

5. Run the Application
bash
uvicorn app.main:app --reload
The API will be available at:

Base URL: http://127.0.0.1:8000/

Interactive docs (Swagger UI): http://127.0.0.1:8000/docs

Alternative docs (ReDoc): http://127.0.0.1:8000/redoc

Tech Stack Used
Language: Python

Framework: FastAPI

Database: MongoDB (PyMongo)

Auth: JWT (JSON Web Tokens)

Password Hashing: Argon2 (via Passlib)

Config Management: pydantic-settings

Environment: Uvicorn ASGI server

Testing: pytest, FastAPI TestClient

API Endpoints
1. Create Organization
Method: POST

URL: /org/create

Request body:

json
{
  "organization_name": "Shiney",
  "email": "shiney@gunnu.com",
  "password": "strongpassword123"
}
Behavior:

Validates that organization_name does not already exist.

Creates a new database and collection for the organization (e.g. org_Shiney).

Inserts an initial document into the organization collection (so DB appears in MongoDB).

Stores metadata in the master database (master_database.organizations):

organization_name

collection_name

admin_email

admin_password (hashed)

created_at

Returns basic organization metadata.

2. Get Organization by Name
Method: GET

URL: /org/get

Query parameter: organization_name

Behavior:

Looks up the organization in the master database by organization_name.

Returns organization metadata (excluding the hashed password).

Returns 404 if the organization does not exist.

3. Update Organization
Method: PUT

URL: /org/update

Request body:

json
{
  "organization_name": "ShineyRenamed",
  "email": "shiney@gunnu.com",
  "password": "newpassword123"
}
Behavior:

Identifies the organization by admin_email (the email field).

Validates that the new organization_name does not conflict with any other existing organization.

Creates a new database/collection for the new name.

Copies all documents from the old organization collection into the new one.

Updates in the master database:

organization_name

collection_name

admin_email (if changed)

admin_password (re-hashed)

Drops the old organization database if the name changed.

Returns a success message.

4. Delete Organization
Method: DELETE

URL: /org/delete

Query parameter: organization_name

Auth: Requires Bearer JWT token

Behavior:

Uses HTTP Bearer auth (JWT) to protect the route.

Verifies the JWT, extracts organization_id from the payload.

Ensures that the authenticated admin belongs to the same organization being deleted.

Drops the organization database.

Removes the organization entry from the master database.

Returns a success message.

5. Admin Login
Method: POST

URL: /admin/login

Request body:

json
{
  "email": "shiney@gunnu.com",
  "password": "strongpassword123"
}
Behavior:

Looks up admin by admin_email in master database.

Verifies the password using Argon2 hashing.

On success, returns a JWT containing:

admin_id

organization_id (organization name)

email

On failure, returns 401 Unauthorized.

Using the Authorization Button in Swagger UI
The project uses HTTP Bearer authentication integrated into the interactive docs:

Open http://127.0.0.1:8000/docs.

Call POST /admin/login with valid credentials to receive an access_token.

Click the “Authorize” button (padlock icon at the top-right of the docs).

In the popup, in the field for the Bearer scheme, paste only the raw JWT token (no need to type Bearer manually).

Click “Authorize”, then “Close”.

After this, all protected endpoints (like DELETE /org/delete) will automatically send the Authorization header with your token. You do not need to manually type the header for each request.

Multi-Tenant Architecture Design
Master Database
A dedicated database (MASTER_DB_NAME, e.g. master_database) stores global metadata:

organizations collection:

_id

organization_name

collection_name

admin_email

admin_password (hashed)

created_at

This allows quickly finding any organization and its corresponding dynamic database/collection.

Dynamic Organization Databases
For each organization:

A separate database is created: org_<organization_name>.

Within that database, a main collection (e.g. data) holds tenant-specific data.

An _initialized document is inserted to ensure the database appears in MongoDB tools.

This design provides:

Logical data isolation per organization.

Easier backup/restore per tenant.

Flexibility to extend each tenant schema independently.

Authentication & Security
JWT Authentication

Admin login returns a signed JWT.

Protected routes use HTTP Bearer auth and verify the token.

Token payload includes admin and organization identifiers.

Password Hashing

Uses Argon2 via Passlib.

Only hashed passwords are stored; plain-text passwords are never persisted.

Authorization

Delete operation checks that the token’s organization_id matches the requested organization.

Prevents one tenant’s admin from modifying another tenant’s data.

Tests
Automated tests are implemented using pytest and FastAPI’s TestClient.

To run tests:

bash
pytest -v
The test suite covers:

Organization creation (success + duplicate name)

Get organization (success + not found)

Admin login (success, wrong password, non-existent user)

Update organization (success + not found)

Delete organization (with and without authorization)

Validation errors (invalid email, missing fields)

All tests currently pass.

Key Design Choices & Trade-Offs
FastAPI + MongoDB

Fast development, async-friendly, and JSON-native.

MongoDB is a good fit for flexible, tenant-specific data.

Trade-off: Not focused on complex relational joins.

Per-Organization Database

Strong logical isolation and clean separation for each tenant.

Trade-off: At very large scale, many databases may increase resource usage and connection overhead.

Master Metadata Database

Central point for managing organizations and admin credentials.

Trade-off: Needs careful backup and monitoring because it’s critical for tenant discovery and authentication.

Assumptions
All organizations share the same MongoDB cluster/instance; each tenant has its own database within that cluster.

Connection details per organization are not separated because a single cluster is sufficient for this assignment.

Admin users are defined per organization; cross-tenant admin roles were not required.