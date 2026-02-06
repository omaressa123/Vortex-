from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import uuid
import secrets
import hashlib
import psycopg2
from psycopg2.extras import RealDictCursor

# JWT Configuration
SECRET_KEY = "your-secret-key-change-in-production"  # Move to environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()

# Pydantic models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserCreate(BaseModel):
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class User(BaseModel):
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    is_premium: bool
    api_quota_daily: int
    api_quota_used: int

class APIKeyCreate(BaseModel):
    key_name: str
    permissions: List[str] = []
    expires_days: Optional[int] = None

class APIKey(BaseModel):
    id: str
    key_name: str
    permissions: List[str]
    is_active: bool
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    created_at: datetime

# Security functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        token_data = TokenData(email=email)
        return token_data
    except JWTError:
        return None

def generate_api_key():
    """Generate a secure API key"""
    return f"ak-{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

# Database functions
def get_user_by_email(db_conn, email: str) -> Optional[dict]:
    cursor = db_conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    return dict(user) if user else None

def get_user_by_id(db_conn, user_id: str) -> Optional[dict]:
    cursor = db_conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    return dict(user) if user else None

def create_user(db_conn, user_data: dict) -> dict:
    cursor = db_conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        INSERT INTO users (email, password_hash, first_name, last_name)
        VALUES (%s, %s, %s, %s)
        RETURNING *
        """,
        (user_data['email'], user_data['password_hash'], 
         user_data.get('first_name'), user_data.get('last_name'))
    )
    user = cursor.fetchone()
    db_conn.commit()
    cursor.close()
    return dict(user)

def create_api_key_for_user(db_conn, user_id: str, key_data: dict) -> dict:
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    
    expires_at = None
    if key_data.get('expires_days'):
        expires_at = datetime.utcnow() + timedelta(days=key_data['expires_days'])
    
    cursor = db_conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        INSERT INTO api_keys (user_id, key_name, key_hash, permissions, expires_at)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
        """,
        (user_id, key_data['key_name'], key_hash, 
         key_data.get('permissions', []), expires_at)
    )
    api_key_record = cursor.fetchone()
    db_conn.commit()
    cursor.close()
    
    return {
        **dict(api_key_record),
        'api_key': api_key  # Return the actual key only once
    }

def get_api_key_by_hash(db_conn, key_hash: str) -> Optional[dict]:
    cursor = db_conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT ak.*, u.email, u.is_active as user_active
        FROM api_keys ak
        JOIN users u ON ak.user_id = u.id
        WHERE ak.key_hash = %s AND ak.is_active = TRUE AND u.is_active = TRUE
        """,
        (key_hash,)
    )
    api_key = cursor.fetchone()
    cursor.close()
    return dict(api_key) if api_key else None

def update_api_key_last_used(db_conn, key_id: str):
    cursor = db_conn.cursor()
    cursor.execute(
        "UPDATE api_keys SET last_used = NOW() WHERE id = %s",
        (key_id,)
    )
    db_conn.commit()
    cursor.close()

def check_user_quota(db_conn, user_id: str) -> bool:
    cursor = db_conn.cursor()
    cursor.execute(
        """
        SELECT api_quota_daily, api_quota_used 
        FROM users 
        WHERE id = %s AND is_active = TRUE
        """,
        (user_id,)
    )
    result = cursor.fetchone()
    cursor.close()
    
    if not result:
        return False
    
    quota_daily, quota_used = result
    return quota_used < quota_daily

def increment_user_quota(db_conn, user_id: str):
    cursor = db_conn.cursor()
    cursor.execute(
        "UPDATE users SET api_quota_used = api_quota_used + 1 WHERE id = %s",
        (user_id,)
    )
    db_conn.commit()
    cursor.close()

# Dependency functions
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_conn = None
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception
    
    user = get_user_by_email(db_conn, email=token_data.email)
    if user is None:
        raise credentials_exception
    
    if not user['is_active']:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user

def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    if not current_user.get("is_active"):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def authenticate_api_key(
    api_key: str,
    db_conn = None
) -> Optional[dict]:
    key_hash = hash_api_key(api_key)
    api_key_record = get_api_key_by_hash(db_conn, key_hash)
    
    if not api_key_record:
        return None
    
    # Check if key is expired
    if api_key_record['expires_at'] and api_key_record['expires_at'] < datetime.utcnow():
        return None
    
    # Check user quota
    if not check_user_quota(db_conn, api_key_record['user_id']):
        raise HTTPException(
            status_code=429,
            detail="API quota exceeded"
        )
    
    # Update last used timestamp
    update_api_key_last_used(db_conn, api_key_record['id'])
    
    # Increment quota usage
    increment_user_quota(db_conn, api_key_record['user_id'])
    
    return api_key_record

def get_user_from_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_conn = None
) -> dict:
    api_key = credentials.credentials
    
    # Check if it's a JWT token (format: xxxxxx.yyyyyyy.zzzzzz)
    if api_key.count('.') == 2:
        # JWT token authentication
        token_data = verify_token(api_key)
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user = get_user_by_email(db_conn, email=token_data.email)
        if not user or not user['is_active']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return user
    
    else:
        # API key authentication
        api_key_record = authenticate_api_key(api_key, db_conn)
        if not api_key_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        user = get_user_by_id(db_conn, api_key_record['user_id'])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user

# Rate limiting
class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed based on rate limit"""
        current = self.redis.get(key)
        if current is None:
            self.redis.setex(key, window, 1)
            return True
        
        if int(current) >= limit:
            return False
        
        self.redis.incr(key)
        return True
