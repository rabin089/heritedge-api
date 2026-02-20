from fastapi import FastAPI
from dotenv import load_dotenv
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
    try:
        seed_database()
    except Exception as e:
        print(f"Error during startup seeding: {e}")

@app.get("/")
def read_root():
    return {"message": "Welcome to HeritEdge API v2"}
