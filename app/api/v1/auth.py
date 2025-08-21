from fastapi import APIRouter, Depends, HTTPException, Form, Body
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.users import UserCreate, UserOut, Token
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM, \
    create_refresh_token

router = APIRouter()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # ensure it's an access token
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail={"error_code": "INVALID_TOKEN_TYPE", "message":"Not an access token"})
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail={"error_code": "INVALID_TOKEN", "message": "Invalid token payload"})
    except ExpiredSignatureError:
        # Access token expired — frontend should attempt refresh
        raise HTTPException(status_code=403, detail={"error_code": "ACCESS_TOKEN_EXPIRED", "message": "Access token has expired"})
    except JWTError:
        # Invalid / tampered token
        raise HTTPException(status_code=401, detail={"error_code": "INVALID_TOKEN", "message": "Invalid token"})
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=404, detail={"error_code": "USER_NOT_FOUND", "message": "User not found"})
    return user


@router.get("/me", response_model=UserOut)
def read_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/signup", response_model=UserOut)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password
    hashed_pw = hash_password(user.password)

    # Create a new user
    new_user = User(email=user.email, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
@router.post("/refresh-token", response_model=Token)
def refresh_token(refresh_token: str = Body(...), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            # user passed an access token (or other) — reject
            raise HTTPException(status_code=401, detail={"error_code": "INVALID_TOKEN_TYPE", "message": "Not a refresh token"})
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail={"error_code": "INVALID_TOKEN", "message": "Invalid token payload"})
    except ExpiredSignatureError:
        # Refresh token expired — force re-login
        raise HTTPException(status_code=403, detail={"error_code": "REFRESH_TOKEN_EXPIRED", "message": "Refresh token has expired"})
    except JWTError:
        # Invalid / tampered token
        raise HTTPException(status_code=401, detail={"error_code": "INVALID_TOKEN", "message": "Invalid refresh token"})

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=404, detail={"error_code": "USER_NOT_FOUND", "message": "User not found"})

    new_access_token = create_access_token(data={"sub": user.email})
    # return same refresh token (stateless) and new access token
    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }



