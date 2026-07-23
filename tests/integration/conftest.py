import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.core.database import Base

from sqlalchemy.dialects.postgresql import JSONB, ARRAY, INET, UUID
from sqlalchemy.ext.compiler import compiles
import sqlite3
import json

# Ensure all models are imported so Base.metadata knows about them
import app.models.user
import app.models.heritage_site
import app.models.user_activity
import app.models.user_interest_profile
import app.models.user_favorite
import app.models.recommendation_history
import app.models.site_review
import app.models.festival
import app.models.intangible_heritage
import app.models.contribution

import uuid as _uuid
sqlite3.register_adapter(list, json.dumps)
sqlite3.register_adapter(dict, json.dumps)
sqlite3.register_adapter(_uuid.UUID, lambda u: u.hex)

@compiles(JSONB, "sqlite")
def compile_jsonb(type_, compiler, **kw):
    return "JSON"

@compiles(ARRAY, "sqlite")
def compile_array(type_, compiler, **kw):
    return "JSON"

@compiles(UUID, "sqlite")
def compile_uuid(type_, compiler, **kw):
    return "VARCHAR(36)"

@compiles(INET, "sqlite")
def compile_inet(type_, compiler, **kw):
    return "VARCHAR"

from sqlalchemy.pool import StaticPool

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
    
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
