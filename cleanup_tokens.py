#!/usr/bin/env python3
"""
Clean up invalid/old FCM tokens from the database.
"""
from app.core.database import SessionLocal
from app.models.user_device import UserDevice

db = SessionLocal()

# Get all tokens before deletion
old_tokens = db.query(UserDevice).all()
print(f"Found {len(old_tokens)} token(s) in database:")
for token in old_tokens:
    print(f"  - User: {token.user_email}, Token: {token.fcm_token[:40]}...")

# Delete all tokens
deleted_count = db.query(UserDevice).delete()
db.commit()

print(f"\n✅ Deleted {deleted_count} token(s) from database")
print("\nNext steps:")
print("1. Restart your Flutter app (close and reopen)")
print("2. Call POST /me/device-token with your new FCM token")
print("3. Test POST /api/v1/notifications/test-push again")
