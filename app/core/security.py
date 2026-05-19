from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
import os
import json
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException

from dotenv import load_dotenv

load_dotenv()

# ----------------------------
# CONFIG
# ----------------------------

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)
REFRESH_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "10080")  # 7 days default
)

# ----------------------------
# FIREBASE INIT (CLEAN + SAFE)
# ----------------------------

firebase_cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
firebase_cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

if not firebase_cred_json and not firebase_cred_path:
    raise RuntimeError("Neither FIREBASE_CREDENTIALS_JSON nor FIREBASE_CREDENTIALS_PATH is set")

try:
    if firebase_cred_json:
        cred_dict = json.loads(firebase_cred_json)
        cred = credentials.Certificate(cred_dict)
    else:
        # Load from path
        if not os.path.exists(firebase_cred_path):
            raise RuntimeError(f"Firebase credentials file not found at: {firebase_cred_path}")
        cred = credentials.Certificate(firebase_cred_path)

    # Prevent duplicate initialization in FastAPI reload / multiple imports
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

except json.JSONDecodeError:
    raise RuntimeError("FIREBASE_CREDENTIALS_JSON is not valid JSON")
except Exception as e:
    raise RuntimeError(f"Failed to initialize Firebase: {str(e)}")

# ----------------------------
# PASSWORD HASHING
# ----------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ----------------------------
# JWT TOKENS
# ----------------------------

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({
        "exp": expire,
        "type": "access"
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ----------------------------
# FIREBASE TOKEN VERIFY
# ----------------------------

def verify_firebase_token(id_token: str):
    try:
        return auth.verify_id_token(id_token)

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid Firebase token"
        )