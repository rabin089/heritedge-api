from fastapi import APIRouter, Depends, HTTPException, Form, Body
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.schemas.users import UserCreate, UserOut, Token, FirebaseLoginRequest, AccountLinkingRequest
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM, \
    create_refresh_token, verify_firebase_token

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

    # Hash the password if provided (OAuth users may not have passwords)
    hashed_pw = None
    if user.password:
        hashed_pw = hash_password(user.password)

    # Create a new user
    new_user = User(
        email=user.email, 
        hashed_password=hashed_pw,
        name=user.name,  # From Google/other providers
        profile_photo_url=user.profile_photo_url,
        auth_provider=user.auth_provider
    )
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
    if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
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


@router.post("/firebase-login", response_model=Token)
def firebase_login(id_token: str = Body(...), db: Session = Depends(get_db)):
    decoded_token = verify_firebase_token(id_token)
    firebase_uid = decoded_token['uid']
    email = decoded_token.get('email')
    name = decoded_token.get('name', '')  # Extract name from Firebase token
    picture = decoded_token.get('picture', '')  # Extract profile photo from Firebase token
    
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided in Firebase token")

    # Check if user exists by firebase_uid
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if user:
        # Update user's name and profile photo if they're empty
        if not user.name and name:
            user.name = name
        if not user.profile_photo_url and picture:
            user.profile_photo_url = picture
        user.last_login_at = datetime.now(timezone.utc)
        db.commit()
        
        # User already linked with Firebase, login directly
        access_token = create_access_token(data={"sub": user.email})
        refresh_token = create_refresh_token(data={"sub": user.email})
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    # Check if email already exists (password-based user)
    email_user = db.query(User).filter(User.email == email).first()
    if email_user:
        # Email exists but not linked to Firebase
        # Return a special response indicating account linking is required
        raise HTTPException(
            status_code=409,
            detail={
                "error_code": "ACCOUNT_EXISTS",
                "message": "An account with this email already exists.",
                "options": [
                    {
                        "option": "link_account",
                        "description": "Link your Google account to your existing password-based account",
                        "endpoint": "/api/v1/auth/link-account",
                        "requires": ["id_token", "email", "password"]
                    },
                    {
                        "option": "use_password",
                        "description": "Continue using your password to login (don't use Google Sign-In)",
                        "endpoint": "/api/v1/auth/login",
                        "requires": ["username", "password"]
                    },
                    {
                        "option": "different_email",
                        "description": "Create a new Firebase account with a different email address"
                    }
                ]
            }
        )
    
    # Create new user with Firebase
    user = User(
        email=email, 
        firebase_uid=firebase_uid, 
        hashed_password=None,
        name=name,  # Extract from Firebase token
        profile_photo_url=picture,  # Extract from Firebase token
        auth_provider="google"  # Set auth provider to google
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/link-account", response_model=Token)
def link_account(request: AccountLinkingRequest, db: Session = Depends(get_db)):
    """
    Link an existing password-based account with a Firebase account.
    Requires both the Firebase ID token and the existing account password.
    """
    # Verify Firebase token
    decoded_token = verify_firebase_token(request.id_token)
    firebase_uid = decoded_token['uid']
    firebase_email = decoded_token.get('email')
    firebase_name = decoded_token.get('name', '')  # Extract name from Firebase token
    firebase_picture = decoded_token.get('picture', '')  # Extract profile photo from Firebase token
    
    if not firebase_email:
        raise HTTPException(status_code=400, detail="Email not provided in Firebase token")
    
    # Check if the Firebase UID is already linked
    existing_firebase_user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if existing_firebase_user:
        raise HTTPException(status_code=400, detail="This Firebase account is already linked to another user")
    
    # Find the user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify the password matches
    if not user.hashed_password or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify that the email matches
    if user.email != firebase_email:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "EMAIL_MISMATCH",
                "message": f"The Firebase email ({firebase_email}) does not match your account email ({user.email})"
            }
        )
    
    # Link the Firebase account
    user.firebase_uid = firebase_uid
    # Update name and profile photo if they're empty
    if not user.name and firebase_name:
        user.name = firebase_name
    if not user.profile_photo_url and firebase_picture:
        user.profile_photo_url = firebase_picture
    db.commit()
    db.refresh(user)
    
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }



