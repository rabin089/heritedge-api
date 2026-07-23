import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt
from unittest.mock import patch

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    hash_password,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_MINUTES,
    verify_firebase_token,
)
from fastapi import HTTPException

def test_hash_and_verify_password():
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_create_access_token():
    data = {"sub": "user@example.com"}
    token = create_access_token(data)
    
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    assert decoded["sub"] == "user@example.com"
    assert decoded["type"] == "access"
    assert "exp" in decoded

def test_create_access_token_custom_expiry():
    data = {"sub": "user@example.com"}
    delta = timedelta(minutes=15)
    
    token = create_access_token(data, expires_delta=delta)
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    exp = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
    expected_exp = datetime.now(timezone.utc) + delta
    
    # Allow 1 second variance for computation time
    assert abs((exp - expected_exp).total_seconds()) < 2

def test_create_refresh_token():
    data = {"sub": "user@example.com"}
    token = create_refresh_token(data)
    
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    assert decoded["sub"] == "user@example.com"
    assert decoded["type"] == "refresh"
    assert "exp" in decoded

@patch("app.core.security.auth.verify_id_token")
def test_verify_firebase_token_success(mock_verify):
    mock_verify.return_value = {"uid": "test_uid", "email": "test@firebase.com"}
    
    result = verify_firebase_token("valid_token")
    assert result["uid"] == "test_uid"
    assert result["email"] == "test@firebase.com"

@patch("app.core.security.auth.verify_id_token")
def test_verify_firebase_token_failure(mock_verify):
    mock_verify.side_effect = Exception("Firebase Error")
    
    with pytest.raises(HTTPException) as excinfo:
        verify_firebase_token("invalid_token")
        
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Invalid Firebase token"
