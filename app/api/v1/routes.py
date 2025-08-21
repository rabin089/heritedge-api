from fastapi import APIRouter
from app.api.v1 import auth, heritage, contribution

router = APIRouter()
router.include_router(auth.router)
router.include_router(heritage.router)
router.include_router(contribution.router)
