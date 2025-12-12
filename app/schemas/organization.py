from pydantic import BaseModel, EmailStr

class OrganizationCreate(BaseModel):
    organization_name: str
    email: EmailStr
    password: str

class OrganizationUpdate(BaseModel):
    organization_name: str
    email: EmailStr
    password: str

class OrganizationResponse(BaseModel):
    organization_name: str
    collection_name: str
    admin_email: str
    created_at: str

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
