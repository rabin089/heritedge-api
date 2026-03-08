from fastapi import FastAPI
from dotenv import load_dotenv
import os
from app.api.v1.routes import router as api_router
from app.seed_data import seed_database

# Load environment variables
load_dotenv()

app = FastAPI(title="HeritEdge API")

# Add your route groups
app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    """Seed initial data on startup"""
    seed_on_startup = os.getenv("SEED_ON_STARTUP", "false").lower() in {"1", "true", "yes", "y"}
    if not seed_on_startup:
        return

    try:
        seed_database()
    except Exception as e:
        print(f"Error during startup seeding: {e}")

@app.get("/")
def read_root():
    return {"message": "Welcome to HeritEdge API v2"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
