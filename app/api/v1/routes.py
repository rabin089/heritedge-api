from fastapi import APIRouter
from app.api.v1 import auth, heritage, contribution, admin, favorites, notification, geocoding

router = APIRouter()
router.include_router(auth.router)
router.include_router(heritage.router)
router.include_router(contribution.router)
router.include_router(admin.router)
router.include_router(favorites.router)
router.include_router(notification.router)
router.include_router(geocoding.router)
