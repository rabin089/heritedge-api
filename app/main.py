from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
import os
import logging
from app.api.v1.routes import router as api_router
from app.seed_data import seed_database
from app.services.scheduler_jobs import send_reminder_notifications, ping_contributors_for_dates

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle."""
    # --- STARTUP ---
    seed_on_startup = os.getenv("SEED_ON_STARTUP", "false").lower() in {"1", "true", "yes", "y"}
    if seed_on_startup:
        try:
            seed_database()
        except Exception as e:
            logger.error(f"Error during startup seeding: {e}")

    # Start background scheduler
    scheduler = BackgroundScheduler(timezone="UTC")

    # Daily reminder job — runs at 02:15 UTC (08:00 NPT)
    scheduler.add_job(
        send_reminder_notifications,
        CronTrigger(hour=2, minute=15),
        id="reminder_notifications",
        replace_existing=True
    )

    # Monthly contributor ping — runs on 1st of every month at 03:30 UTC (09:15 NPT)
    scheduler.add_job(
        ping_contributors_for_dates,
        CronTrigger(day=1, hour=3, minute=30),
        id="contributor_ping",
        replace_existing=True
    )

    scheduler.start()
    logger.info("✅ APScheduler started with reminder and contributor ping jobs.")

    yield  # App is running

    # --- SHUTDOWN ---
    scheduler.shutdown(wait=False)
    logger.info("APScheduler shut down.")


app = FastAPI(title="HeritEdge API", lifespan=lifespan)

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
# 1. Standard API versioning (Preferred)
app.include_router(api_router, prefix="/api/v1")

# 2. Legacy support (Root level routes for existing Flutter code)
app.include_router(api_router)



@app.get("/")
def read_root():
    return {"message": "Welcome to HeritEdge API v2"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
