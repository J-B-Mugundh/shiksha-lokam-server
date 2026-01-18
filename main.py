"""
Shiksha Lokam - Main Backend Entry Point
Phase  1: Master Data Schema Creation + Core APIs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import os
from pathlib import Path
from database import set_database

# Load environment variables
load_dotenv()

# Set HuggingFace cache to project directory
PROJECT_DIR = Path(__file__).parent.absolute()
CACHE_DIR = os.path.join(PROJECT_DIR, ".cache", "huggingface")
os.makedirs(CACHE_DIR, exist_ok=True)
os.environ["HF_HOME"] = CACHE_DIR
os.environ["TRANSFORMERS_CACHE"] = CACHE_DIR

# Global MongoDB client
mongodb_client = None

@asynccontextmanager
async def lifespan(main: FastAPI):
    """Startup and shutdown events"""
    global mongodb_client
    
    # Startup: Connect to MongoDB
    try:        
        uri = os.getenv("MONGODB_URI")
        mongodb_client = MongoClient(uri, server_api=ServerApi('1'))
        mongodb_client.admin.command('ping')
        print("✓ Successfully connected to MongoDB!")
        
        # Select database
        db = mongodb_client["shiksha_lokam"]
        set_database(db)
        
        # Create indexes for better performance
        create_indexes(db)
        
        print("✓ Database indexes created!")
        
    except Exception as e:
        print(f"✗ Startup failed: {e}")
    
    yield
    
    # Shutdown: Close MongoDB connection
    if mongodb_client:
        mongodb_client.close()
        print("✓ MongoDB connection closed")

def create_indexes(db):
    """Create MongoDB indexes for all collections"""
    
    # Users
    db.users.create_index("email", unique=True)
    db.users.create_index("google_id", unique=True, sparse=True)
    db.users.create_index([("organizations.organization_id", 1)])
    
    # Organizations
    db.organizations.create_index("name")
    db.organizations.create_index("org_type")
    
    # Impacts
    db.impacts.create_index("theme_id")
    db.impacts.create_index("is_template")
    db.impacts.create_index("created_by")
    
    # Outcomes
    db.outcomes.create_index("stakeholder_type")
    db.outcomes.create_index("is_template")
    db.outcomes.create_index("created_by")
    
    # Themes
    db.themes.create_index("name", unique=True)
    db.themes.create_index("short_name")
    
    # LFAs
    db.lfas.create_index("organization_id")
    db.lfas.create_index("created_by")
    db.lfas.create_index("status")
    db.lfas.create_index("theme_id")
    db.lfas.create_index([("created_at", -1)])
    
    # LFA Reviews
    db.lfa_reviews.create_index("lfa_id")
    db.lfa_reviews.create_index("reviewer_id")
    db.lfa_reviews.create_index([("created_at", -1)])
    
    # School Progress
    db.school_progress.create_index("execution_id")
    db.school_progress.create_index("lfa_id")
    db.school_progress.create_index("organization_id")
    db.school_progress.create_index("status")
    db.school_progress.create_index("school_code")
    db.school_progress.create_index([("district", 1), ("state", 1)])

# Initialize FastAPI
main = FastAPI(
    lifespan=lifespan,
    title="Shiksha Lokam API",
    description="AI-powered gamified platform for NGO program design",
    version="1.0.0"
)

# CORS middleware
main.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes
from routes import (
    user_routes,
    organization_routes,
    impact_routes,
    outcome_routes,
    theme_routes,
    lfa_routes,
    school_routes,
    ai_generation_routes
)

# Register routers
main.include_router(user_routes.router, prefix="/api/users", tags=["Users"])
main.include_router(organization_routes.router, prefix="/api/organizations", tags=["Organizations"])
main.include_router(impact_routes.router, prefix="/api/impacts", tags=["Impacts"])
main.include_router(outcome_routes.router, prefix="/api/outcomes", tags=["Outcomes"])
main.include_router(theme_routes.router, prefix="/api/themes", tags=["Themes"])
main.include_router(lfa_routes.router, prefix="/api/lfas", tags=["LFAs"])
main.include_router(school_routes.router, prefix="/api/schools", tags=["Schools"])
main.include_router(ai_generation_routes.router, prefix="/api/ai", tags=["AI Generation"])

# Root endpoint
@main.get("/")
def read_root():
    return {
        "message": "Shiksha Lokam - Educational Program Design API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "users": "/api/users",
            "organizations": "/api/organizations",
            "impacts": "/api/impacts",
            "outcomes": "/api/outcomes",
            "themes": "/api/themes",
            "lfas": "/api/lfas",
            "schools": "/api/schools",
            "ai_generation": "/api/ai",
            "docs": "/docs"
        }
    }

# Health check endpoint
@main.get("/health")
def health_check():
    try:
        if mongodb_client:
            mongodb_client.admin.command('ping')
            return {
                "status": "healthy",
                "database": "connected",
                "db_name": "shiksha_lokam"
            }
        else:
            return {
                "status": "unhealthy",
                "database": "disconnected"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Export for use in routes
__all__ = ['main']