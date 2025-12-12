from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from .config import settings

class Database:
    def __init__(self):
        try:
            self.client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.master_db = self.client[settings.MASTER_DB_NAME]
            print("✓ MongoDB connected successfully")
        except ConnectionFailure:
            print("✗ MongoDB connection failed. Please ensure MongoDB is running.")
            raise
    
    def get_master_db(self):
        return self.master_db
    
    def create_org_collection(self, org_name: str):
        """Create and return a collection for the organization"""
        db_name = f"org_{org_name}"
        org_db = self.client[db_name]
        # Return a collection, not a database
        return org_db["data"]  # or any collection name you want
    
    def get_org_collection(self, org_name: str):
        """Get an existing organization collection"""
        db_name = f"org_{org_name}"
        org_db = self.client[db_name]
        return org_db["data"]  # same collection name as above
    
    def drop_org_database(self, org_name: str):
        """Drop an organization database"""
        db_name = f"org_{org_name}"
        self.client.drop_database(db_name)

db = Database()
