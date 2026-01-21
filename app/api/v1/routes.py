from fastapi import APIRouter
from app.api.v1 import auth, heritage, contribution, admin, favorites, notification, site_review, upload, geocoding

router = APIRouter()
router.include_router(auth.router)
router.include_router(site_review.router)
router.include_router(heritage.router)
router.include_router(contribution.router)
router.include_router(admin.router)
router.include_router(favorites.router)
router.include_router(notification.router)
router.include_router(upload.router, prefix="/api/v1")
router.include_router(geocoding.router, prefix="/api/v1")
router.include_router(geocoding.router)  # Also add without /api/v1 prefix for backward compatibility
