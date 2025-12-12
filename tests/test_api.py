from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

# Test data
test_org_name = "TestOrganization"
test_email = "admin@testorg.com"
test_password = "securepassword123"

class TestOrganizationEndpoints:
    
    def test_create_organization_success(self):
        """Test creating a new organization"""
        response = client.post(
            "/org/create",
            json={
                "organization_name": test_org_name,
                "email": test_email,
                "password": test_password
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["organization_name"] == test_org_name
        assert data["admin_email"] == test_email
        assert "collection_name" in data
        assert "created_at" in data
    
    def test_create_organization_duplicate(self):
        """Test creating organization with duplicate name"""
        response = client.post(
            "/org/create",
            json={
                "organization_name": test_org_name,
                "email": "another@email.com",
                "password": "password123"
            }
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
    
    def test_get_organization_success(self):
        """Test retrieving an existing organization"""
        response = client.get(
            f"/org/get?organization_name={test_org_name}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["organization_name"] == test_org_name
        assert "admin_password" not in data  # Password should be excluded
    
    def test_get_organization_not_found(self):
        """Test retrieving non-existent organization"""
        response = client.get(
            "/org/get?organization_name=NonExistentOrg"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestAdminAuthentication:
    
    def test_admin_login_success(self):
        """Test successful admin login"""
        response = client.post(
            "/admin/login",
            json={
                "email": test_email,
                "password": test_password
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_admin_login_wrong_password(self):
        """Test login with incorrect password"""
        response = client.post(
            "/admin/login",
            json={
                "email": test_email,
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_admin_login_nonexistent_user(self):
        """Test login with non-existent email"""
        response = client.post(
            "/admin/login",
            json={
                "email": "nonexistent@email.com",
                "password": "somepassword"
            }
        )
        assert response.status_code == 401


class TestOrganizationUpdate:
    
    def test_update_organization_success(self):
        """Test updating organization name and password"""
        response = client.put(
            "/org/update",
            json={
                "organization_name": "UpdatedTestOrg",
                "email": test_email,
                "password": "newpassword456"
            }
        )
        assert response.status_code == 200
        assert "success" in response.json()["message"].lower()
        
        # Verify the update
        get_response = client.get("/org/get?organization_name=UpdatedTestOrg")
        assert get_response.status_code == 200
    
    def test_update_organization_not_found(self):
        """Test updating with non-existent email"""
        response = client.put(
            "/org/update",
            json={
                "organization_name": "SomeOrg",
                "email": "notfound@email.com",
                "password": "password123"
            }
        )
        assert response.status_code == 404


class TestOrganizationDelete:
    
    def test_delete_without_auth(self):
        """Test delete without authentication token"""
        response = client.delete(
            "/org/delete?organization_name=UpdatedTestOrg"
        )
        assert response.status_code == 403  # Forbidden without auth
    
    def test_delete_with_auth_success(self):
        """Test successful organization deletion"""
        # First login to get token
        login_response = client.post(
            "/admin/login",
            json={
                "email": test_email,
                "password": "newpassword456"
            }
        )
        token = login_response.json()["access_token"]
        
        # Delete with auth
        response = client.delete(
            "/org/delete?organization_name=UpdatedTestOrg",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "success" in response.json()["message"].lower()
        
        # Verify deletion
        get_response = client.get("/org/get?organization_name=UpdatedTestOrg")
        assert get_response.status_code == 404


class TestValidation:
    
    def test_create_org_invalid_email(self):
        """Test creating org with invalid email format"""
        response = client.post(
            "/org/create",
            json={
                "organization_name": "TestOrg2",
                "email": "invalid-email",
                "password": "password123"
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_org_missing_fields(self):
        """Test creating org with missing required fields"""
        response = client.post(
            "/org/create",
            json={
                "organization_name": "TestOrg3"
                # Missing email and password
            }
        )
        assert response.status_code == 422
