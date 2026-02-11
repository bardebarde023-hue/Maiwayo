from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import secrets
import sqlite3

from app.database import get_db
from app.models import *
from app.config import config

router = APIRouter()
security = HTTPBearer()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: sqlite3.Connection = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    cursor = db.cursor()
    if role == "admin":
        cursor.execute("SELECT * FROM admins WHERE username = ?", (user_id,))
    else:
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {"user_id": user_id, "role": role}

def get_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def generate_verification_code() -> str:
    return str(secrets.randbelow(900000) + 100000)

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    # Check if user exists
    if user_data.email:
        cursor.execute("SELECT * FROM users WHERE email = ?", (user_data.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
    
    if user_data.phone:
        cursor.execute("SELECT * FROM users WHERE phone = ?", (user_data.phone,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Phone already registered")
    
    # Generate user ID
    user_id = str(secrets.randbelow(9000000000) + 1000000000)
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Insert user
    cursor.execute("""
        INSERT INTO users (user_id, name, email, phone, password_hash, referrer_id, joined_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, user_data.name, user_data.email, user_data.phone, hashed_password, 
          user_data.referrer_id, datetime.now().isoformat()))
    
    # Create wallet
    cursor.execute("""
        INSERT INTO wallets (user_id) VALUES (?)
    """, (user_id,))
    
    # Handle referral
    if user_data.referrer_id:
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_data.referrer_id,))
        if cursor.fetchone():
            cursor.execute("""
                INSERT INTO referrals (referrer_id, referred_user_id, joined_at)
                VALUES (?, ?, ?)
            """, (user_data.referrer_id, user_id, datetime.now().isoformat()))
    
    db.commit()
    
    # Generate verification code
    code = generate_verification_code()
    expires_at = (datetime.now() + timedelta(minutes=15)).isoformat()
    
    cursor.execute("""
        INSERT INTO verification_codes (email, phone, code, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_data.email, user_data.phone, code, datetime.now().isoformat(), expires_at))
    
    db.commit()
    
    # In production, send email/SMS with code
    print(f"Verification code for {user_data.email or user_data.phone}: {code}")
    
    # Create token
    access_token = create_access_token({"sub": user_id, "role": "user"})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role="user",
        user_id=user_id
    )

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    # Try email first, then phone
    cursor.execute("SELECT * FROM users WHERE email = ? OR phone = ?", 
                   (login_data.identifier, login_data.identifier))
    user = cursor.fetchone()
    
    if not user or not verify_password(login_data.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if user['is_banned']:
        raise HTTPException(status_code=403, detail="Account banned")
    
    # Update last login
    cursor.execute("UPDATE users SET last_login = ? WHERE user_id = ?", 
                   (datetime.now().isoformat(), user['user_id']))
    db.commit()
    
    access_token = create_access_token({"sub": user['user_id'], "role": user['role']})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user['role'],
        user_id=user['user_id']
    )

@router.post("/admin/login", response_model=TokenResponse)
async def admin_login(login_data: AdminLogin, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM admins WHERE username = ?", (login_data.username,))
    admin = cursor.fetchone()
    
    if not admin or not verify_password(login_data.password, admin['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token({"sub": admin['username'], "role": "admin"})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role="admin"
    )

@router.post("/verify")
async def verify_account(verification: VerificationRequest, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT * FROM verification_codes 
        WHERE (email = ? OR phone = ?) AND code = ? AND verified = 0
        ORDER BY created_at DESC LIMIT 1
    """, (verification.identifier, verification.identifier, verification.code))
    
    code_record = cursor.fetchone()
    
    if not code_record:
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    if datetime.fromisoformat(code_record['expires_at']) < datetime.now():
        raise HTTPException(status_code=400, detail="Verification code expired")
    
    # Mark as verified
    cursor.execute("UPDATE verification_codes SET verified = 1 WHERE id = ?", (code_record['id'],))
    cursor.execute("UPDATE users SET is_verified = 1 WHERE email = ? OR phone = ?", 
                   (verification.identifier, verification.identifier))
    db.commit()
    
    return {"message": "Account verified successfully"}

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ? OR phone = ?", 
                   (request.identifier, request.identifier))
    user = cursor.fetchone()
    
    if not user:
        # Don't reveal if user exists
        return {"message": "If account exists, reset code has been sent"}
    
    code = generate_verification_code()
    expires_at = (datetime.now() + timedelta(minutes=15)).isoformat()
    
    cursor.execute("""
        INSERT INTO verification_codes (email, phone, code, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user['email'], user['phone'], code, datetime.now().isoformat(), expires_at))
    
    db.commit()
    
    print(f"Password reset code for {request.identifier}: {code}")
    
    return {"message": "If account exists, reset code has been sent"}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT * FROM verification_codes 
        WHERE (email = ? OR phone = ?) AND code = ? AND verified = 0
        ORDER BY created_at DESC LIMIT 1
    """, (request.identifier, request.identifier, request.code))
    
    code_record = cursor.fetchone()
    
    if not code_record:
        raise HTTPException(status_code=400, detail="Invalid reset code")
    
    if datetime.fromisoformat(code_record['expires_at']) < datetime.now():
        raise HTTPException(status_code=400, detail="Reset code expired")
    
    hashed_password = hash_password(request.new_password)
    
    cursor.execute("UPDATE users SET password_hash = ? WHERE email = ? OR phone = ?", 
                   (hashed_password, request.identifier, request.identifier))
    cursor.execute("UPDATE verification_codes SET verified = 1 WHERE id = ?", (code_record['id'],))
    db.commit()
    
    return {"message": "Password reset successfully"}