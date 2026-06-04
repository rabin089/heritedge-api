from sqlalchemy.orm import Session
from app.models.user_settings import UserSettings
from app.schemas.user_settings import UserSettingsUpdate

def get_user_settings(db: Session, user_email: str) -> UserSettings:
    settings = db.query(UserSettings).filter(UserSettings.user_email == user_email).first()
    if not settings:
        settings = UserSettings(user_email=user_email, push_notifications_enabled=True)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

def update_user_settings(db: Session, user_email: str, settings_in: UserSettingsUpdate) -> UserSettings:
    settings = get_user_settings(db, user_email)
    
    update_data = settings_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
        
    db.commit()
    db.refresh(settings)
    return settings
