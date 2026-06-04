from fastapi import APIRouter
from app.api.v1 import (
    auth, heritage, contribution, admin, favorites, 
    notification, site_review, upload, geocoding, 
    festival, festival_interaction, user_device, intangible_heritage
)

router = APIRouter()

# All routers included simply. Prefixing will be handled in main.py
router.include_router(auth.router)
router.include_router(site_review.router)
router.include_router(heritage.router)
router.include_router(contribution.router)
router.include_router(admin.router)
router.include_router(favorites.router)
router.include_router(notification.router)
router.include_router(festival.router)
router.include_router(festival_interaction.router)
router.include_router(user_device.router)
router.include_router(intangible_heritage.router)
router.include_router(upload.router)
router.include_router(geocoding.router)
