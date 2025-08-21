from fastapi import FastAPI
from app.api.v1.routes import router as api_router

app = FastAPI(title="HeritEdge API")

# Add your route groups
app.include_router(api_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to HeritEdge API v2"}
