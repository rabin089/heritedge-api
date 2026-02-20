"""
Seed data script for initial admin users
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_initial_users(db: Session):
    """Create initial superadmin and admin users"""
    
    # Default credentials (should be changed in production)
    initial_users = [
        {
            "email": "heritedgenepal@gmail.com",
            "password": "SuperAdmin123!",
            "role": "superadmin",
            "is_admin": True
        },
        {
            "email": "admin@heritedgenepal.com", 
            "password": "Admin123!",
            "role": "admin",
            "is_admin": True
        }
    ]
    
    created_users = []
    
    for user_data in initial_users:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if existing_user:
            print(f"⚠️  User {user_data['email']} already exists, skipping...")
            continue
            
        # Create new user
        user = User(
            email=user_data["email"],
            hashed_password=hash_password(user_data["password"]),
            is_active=True,
            is_admin=user_data["is_admin"],
            role=user_data["role"]
        )
        
        db.add(user)
        created_users.append(user_data["email"])
        print(f"✅ Created {user_data['role']} user: {user_data['email']}")
    
    if created_users:
        db.commit()
        print(f"\n🎉 Successfully created {len(created_users)} initial users:")
        for email in created_users:
            print(f"   - {email}")
        print("\n📝 Default credentials:")
        print("   Superadmin: superadmin@heritedgenepal.com / SuperAdmin123!")
        print("   Admin: admin@heritedgenepal.com / Admin123!")
        print("\n⚠️  Remember to change these passwords in production!")
    else:
        print("ℹ️  All initial users already exist")


def seed_database():
    """Main seeding function"""
    db = SessionLocal()
    try:
        print("🌱 Starting database seeding...")
        create_initial_users(db)
        print("✅ Database seeding completed!")
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
