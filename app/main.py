from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from dotenv import load_dotenv
import os
from app.api.v1.routes import router as api_router
from app.seed_data import seed_database

# Load environment variables
load_dotenv()

app = FastAPI(title="HeritEdge API")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for validation errors to prevent UnicodeDecodeError 
    when the input contains non-UTF8 bytes (like image files).
    """
    errors = exc.errors()
    for error in errors:
        # Pydantic v2 uses 'input', v1 uses 'value' (sometimes)
        # We check for bytes in any of the error fields that might contain them
        if "input" in error and isinstance(error["input"], bytes):
            try:
                error["input"].decode("utf-8")
            except UnicodeDecodeError:
                error["input"] = f"<binary data: {len(error['input'])} bytes>"
        elif "ctx" in error and isinstance(error["ctx"], dict):
            # Sometimes the values are in context
            for k, v in error["ctx"].items():
                if isinstance(v, bytes):
                    try:
                        v.decode("utf-8")
                    except UnicodeDecodeError:
                        error["ctx"][k] = f"<binary data: {len(v)} bytes>"
    
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": errors}),
    )

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
