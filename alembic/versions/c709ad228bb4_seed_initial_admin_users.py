"""seed_initial_admin_users

Revision ID: c709ad228bb4
Revises: de45fa67bc89
Create Date: 2026-01-01 06:34:39.435155

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.core.security import hash_password


# revision identifiers, used by Alembic.
revision: str = 'c709ad228bb4'
down_revision: Union[str, Sequence[str], None] = 'de45fa67bc89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed initial admin users."""
    bind = op.get_bind()
    Session = sessionmaker(bind=bind)
    session = Session()
    
    try:
        # Check if users already exist
        existing_superadmin = session.query(User).filter(User.email == "heritedgenepal@gmail.com").first()
        existing_admin = session.query(User).filter(User.email == "admin@heritedgenepal.com").first()
        
        if not existing_superadmin:
            superadmin = User(
                email="heritedgenepal@gmail.com",
                hashed_password=hash_password("SuperAdmin123!"),
                is_active=True,
                is_admin=True,
                role="superadmin"
            )
            session.add(superadmin)
            print("✅ Created superadmin user: heritedgenepal@gmail.com")
        
        if not existing_admin:
            admin = User(
                email="admin@heritedgenepal.com",
                hashed_password=hash_password("Admin123!"),
                is_active=True,
                is_admin=True,
                role="admin"
            )
            session.add(admin)
            print("✅ Created admin user: admin@heritedgenepal.com")
        
        session.commit()
        print("\n🎉 Initial admin users seeded successfully!")
        print("📝 Default credentials:")
        print("   Superadmin: heritedgenepal@gmail.com / SuperAdmin123!")
        print("   Admin: admin@heritedgenepal.com / Admin123!")
        print("⚠️  Remember to change these passwords in production!")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error seeding initial users: {e}")
        raise
    finally:
        session.close()


def downgrade() -> None:
    """Remove seeded admin users."""
    bind = op.get_bind()
    Session = sessionmaker(bind=bind)
    session = Session()
    
    try:
        # Delete seeded users
        session.query(User).filter(User.email.in_(["heritedgenepal@gmail.com", "admin@heritedgenepal.com"])).delete(synchronize_session=False)
        session.commit()
        print("✅ Removed seeded admin users")
    except Exception as e:
        session.rollback()
        print(f"❌ Error removing seeded users: {e}")
        raise
    finally:
        session.close()
