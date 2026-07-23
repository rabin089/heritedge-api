import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.core.database import Base

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
