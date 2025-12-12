from fastapi import APIRouter, HTTPException
from ..schemas.organization import AdminLogin, TokenResponse
from ..database import db
from ..auth.password import verify_password
from ..auth.jwt_handler import create_access_token

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/login", response_model=TokenResponse)
async def admin_login(credentials: AdminLogin):
    master_db = db.get_master_db()
    
    # Find admin user
    admin = master_db.organizations.find_one({"admin_email": credentials.email})
    
    if not admin or not verify_password(credentials.password, admin["admin_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    token_data = {
        "admin_id": str(admin["_id"]),
        "organization_id": admin["organization_name"],
        "email": credentials.email
    }
    
    access_token = create_access_token(token_data)
    
    return TokenResponse(access_token=access_token, token_type="bearer")
