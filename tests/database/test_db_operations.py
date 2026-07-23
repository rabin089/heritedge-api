import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User
from app.models.heritage_site import HeritageSite
from app.models.festival import Festival
from app.models.intangible_heritage import IntangibleHeritage
from app.models.user_activity import UserActivity, ActionType, ItemType
import uuid

from sqlalchemy.dialects.postgresql import JSONB, ARRAY, INET
from sqlalchemy.ext.compiler import compiles
import sqlite3
import json

sqlite3.register_adapter(list, json.dumps)
sqlite3.register_adapter(dict, json.dumps)

@compiles(JSONB, "sqlite")
def compile_jsonb(type_, compiler, **kw):
    return "JSON"

@compiles(ARRAY, "sqlite")
def compile_array(type_, compiler, **kw):
    return "JSON"

@compiles(INET, "sqlite")
def compile_inet(type_, compiler, **kw):
    return "VARCHAR"

# SQLite in-memory database for fast testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

from sqlalchemy import event

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Create the database and tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop the tables after each test to ensure isolation
        Base.metadata.drop_all(bind=engine)

def test_create_user(db_session):
    user = User(
        email="testdb@example.com",
        role="user",
        hashed_password="hashed_password",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    assert user.id is not None
    assert user.email == "testdb@example.com"

def test_unique_constraint_user_email(db_session):
    user1 = User(email="unique@example.com", role="user", hashed_password="pw1")
    user2 = User(email="unique@example.com", role="admin", hashed_password="pw2")
    
    db_session.add(user1)
    db_session.commit()
    
    db_session.add(user2)
    with pytest.raises(Exception):
        # Depending on sqlite/postgres dialect, it will raise an IntegrityError
        db_session.commit()
    db_session.rollback()

def test_create_user_activity(db_session):
    activity = UserActivity(
        user_id=uuid.uuid4(),
        item_id=uuid.uuid4(),
        item_type=ItemType.site,
        action_type=ActionType.view
    )
    db_session.add(activity)
    db_session.commit()
    
    assert db_session.query(UserActivity).count() == 1

def test_transaction_rollback(db_session):
    user = User(email="rollback@example.com", role="user", hashed_password="pw")
    db_session.add(user)
    db_session.flush() # Flush to db without committing
    
    assert db_session.query(User).filter(User.email == "rollback@example.com").first() is not None
    
    db_session.rollback()
    
    # User should be gone from the session
    assert db_session.query(User).filter(User.email == "rollback@example.com").first() is None
