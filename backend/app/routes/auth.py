from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, EmailStr
import bcrypt
import jwt
import os

from app.models.user import User, UserPreference
from app.database import get_db
from typing import Optional
from pydantic import BaseModel, EmailStr
import bcrypt
import jwt
import os

from app.models.user import User, UserPreference
from app.database import get_db

router = APIRouter()
security = HTTPBearer()

# Pydantic models for request/response
class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone_number: Optional[str] = None
    monthly_income: Optional[float] = 0.0
    savings_goal: Optional[float] = 0.0
    risk_tolerance: Optional[str] = "moderate"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    user_id: str
    email: str
    full_name: str
    phone_number: Optional[str]
    is_active: bool
    monthly_income: float
    savings_goal: float
    risk_tolerance: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), 
                    db: Session = Depends(get_db)) -> User:
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

@router.post("/register", response_model=TokenResponse)
async def register_user(user_data: UserRegistration, db: Session = Depends(get_db)):
    """Register a new user"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        phone_number=user_data.phone_number,
        monthly_income=user_data.monthly_income,
        savings_goal=user_data.savings_goal,
        risk_tolerance=user_data.risk_tolerance,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create user preferences
    user_preferences = UserPreference(
        user_id=new_user.id,
        enable_auto_categorization=True,
        enable_spending_alerts=True,
        enable_investment_suggestions=False,
        email_notifications=True,
        sms_notifications=False,
        budget_alert_threshold=0.8
    )
    
    db.add(user_preferences)
    db.commit()
    
    # Generate access token
    access_token = create_access_token(data={"sub": new_user.email})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(new_user)
    )

@router.post("/login", response_model=TokenResponse)
async def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return access token"""
    
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Generate access token
    access_token = create_access_token(data={"sub": user.email})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse.from_orm(current_user)

@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserRegistration, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    
    # Update user fields
    current_user.full_name = user_update.full_name
    current_user.phone_number = user_update.phone_number
    current_user.monthly_income = user_update.monthly_income
    current_user.savings_goal = user_update.savings_goal
    current_user.risk_tolerance = user_update.risk_tolerance
    current_user.updated_at = datetime.utcnow()
    
    # Update password if provided
    if user_update.password:
        current_user.hashed_password = hash_password(user_update.password)
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.from_orm(current_user)

@router.post("/logout")
async def logout_user(current_user: User = Depends(get_current_user)):
    """Logout user (client should discard token)"""
    return {"message": "Successfully logged out"}

@router.get("/preferences")
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user preferences"""
    preferences = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    
    if not preferences:
        # Create default preferences if not exist
        preferences = UserPreference(
            user_id=current_user.id,
            enable_auto_categorization=True,
            enable_spending_alerts=True,
            enable_investment_suggestions=False,
            email_notifications=True,
            sms_notifications=False,
            budget_alert_threshold=0.8
        )
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    
    return preferences

class UserPreferencesUpdate(BaseModel):
    enable_auto_categorization: Optional[bool] = None
    enable_spending_alerts: Optional[bool] = None
    enable_investment_suggestions: Optional[bool] = None
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    budget_alert_threshold: Optional[float] = None

@router.put("/preferences")
async def update_user_preferences(
    preferences_update: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user preferences"""
    preferences = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    
    if not preferences:
        raise HTTPException(status_code=404, detail="User preferences not found")
    
    # Update only provided fields
    update_data = preferences_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preferences, field, value)
    
    db.commit()
    db.refresh(preferences)
    
    return preferences