from fastapi import FastAPI
from .routes import organization, admin

app = FastAPI(title="Organization Management Service")

app.include_router(organization.router)
app.include_router(admin.router)

@app.get("/")
async def root():
    return {"message": "Organization Management API"}
