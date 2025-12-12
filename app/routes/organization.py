from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..schemas.organization import OrganizationCreate, OrganizationUpdate, OrganizationResponse
from ..database import db
from ..auth.password import hash_password
from ..auth.jwt_handler import verify_token
from datetime import datetime

router = APIRouter(prefix="/org", tags=["Organization"])
security = HTTPBearer()

@router.post("/create", response_model=OrganizationResponse)
async def create_organization(org: OrganizationCreate):
    master_db = db.get_master_db()
    
    # Check if organization exists
    existing_org = master_db.organizations.find_one({"organization_name": org.organization_name})
    if existing_org:
        raise HTTPException(status_code=400, detail="Organization already exists")
    
    # Hash password
    hashed_password = hash_password(org.password)
    
    # Create organization collection with initial document
    collection_name = f"org_{org.organization_name}"
    org_collection = db.create_org_collection(org.organization_name)
    
    # INSERT INITIAL DOCUMENT to make database visible
    org_collection.insert_one({"_initialized": True, "created_at": datetime.utcnow()})
    
    # Store in master database
    org_data = {
        "organization_name": org.organization_name,
        "collection_name": collection_name,
        "admin_email": org.email,
        "admin_password": hashed_password,
        "created_at": datetime.utcnow().isoformat()
    }
    
    master_db.organizations.insert_one(org_data)
    
    return OrganizationResponse(
        organization_name=org.organization_name,
        collection_name=collection_name,
        admin_email=org.email,
        created_at=org_data["created_at"]
    )

@router.get("/get")
async def get_organization(organization_name: str):
    master_db = db.get_master_db()
    org = master_db.organizations.find_one({"organization_name": organization_name}, {"admin_password": 0})
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    org["_id"] = str(org["_id"])
    return org

@router.put("/update")
async def update_organization(org: OrganizationUpdate):
    """
    Update an existing organization.
    
    Identifies organization by admin email, then updates name and password.
    Migrates data to new collection if name changes.
    """
    master_db = db.get_master_db()
    
    # Find existing organization by email
    existing_org = master_db.organizations.find_one({"admin_email": org.email})
    if not existing_org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # CHECK IF NEW NAME CONFLICTS WITH ANOTHER ORGANIZATION
    if org.organization_name != existing_org["organization_name"]:
        name_conflict = master_db.organizations.find_one({
            "organization_name": org.organization_name,
            "_id": {"$ne": existing_org["_id"]}  # Exclude current org
        })
        if name_conflict:
            raise HTTPException(
                status_code=400, 
                detail=f"Organization name '{org.organization_name}' already exists"
            )
    
    # Create new collection
    new_collection_name = f"org_{org.organization_name}"
    old_collection = db.get_org_collection(existing_org["organization_name"])
    new_collection = db.create_org_collection(org.organization_name)
    
    # Migrate data
    data = list(old_collection.find({}))
    if data:
        new_collection.insert_many(data)
    else:
        # Insert initial document if no data to migrate
        new_collection.insert_one({"_initialized": True, "created_at": datetime.utcnow()})
    
    # Update master database
    hashed_password = hash_password(org.password)
    master_db.organizations.update_one(
        {"_id": existing_org["_id"]},
        {"$set": {
            "organization_name": org.organization_name,
            "collection_name": new_collection_name,
            "admin_password": hashed_password,
            "admin_email": org.email
        }}
    )
    
    # Drop old database only if name changed
    if org.organization_name != existing_org["organization_name"]:
        db.drop_org_database(existing_org['organization_name'])
    
    return {"message": "Organization updated successfully"}


@router.delete("/delete")
async def delete_organization(
    organization_name: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Extract token from credentials
    token = credentials.credentials
    
    # Verify token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    master_db = db.get_master_db()
    org = master_db.organizations.find_one({"organization_name": organization_name})
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check if the authenticated user is the admin of this organization
    if payload.get("organization_id") != organization_name:
        raise HTTPException(status_code=403, detail="Not authorized to delete this organization")
    
    # Delete organization database
    db.drop_org_database(organization_name)
    
    # Delete from master database
    master_db.organizations.delete_one({"organization_name": organization_name})
    
    return {"message": "Organization deleted successfully"}
