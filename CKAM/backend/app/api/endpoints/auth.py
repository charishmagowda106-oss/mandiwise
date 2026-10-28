from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database.session import get_db
from app.models.models import User
from app.schemas import schemas
from app.core.security import get_password_hash, verify_password, create_access_token
from app.api.dependencies import get_current_user
from app.services.otp import OtpError, issue_otp, verify_otp

router = APIRouter()

@router.post("/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    email = user_in.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    if user_in.phone and db.query(User).filter(User.phone == user_in.phone).first():
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        email=email,
        password_hash=hashed_password,
        name=user_in.name,
        phone=user_in.phone,
        location_lat=user_in.location_lat,
        location_lng=user_in.location_lng
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email or phone already registered")
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email = form_data.username.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# ---- Phone OTP login (alternative to email/password) ----

@router.post("/request-otp", response_model=schemas.OtpSent)
def request_otp(req: schemas.OtpRequest, db: Session = Depends(get_db)):
    """Send a 6-digit login code to the farmer's phone.

    The number must already be linked to an account (added at sign-up).
    """
    normalized = req.phone
    if db.query(User).filter(User.phone == normalized).first() is None:
        # Not linked: tell the farmer clearly instead of silently sending nothing.
        raise HTTPException(status_code=404, detail="No account is linked to this number — please sign up first")
    try:
        return issue_otp(db, normalized)
    except OtpError as exc:
        raise HTTPException(status_code=429, detail=str(exc))

@router.post("/verify-otp", response_model=schemas.Token)
def verify_otp_endpoint(req: schemas.OtpVerify, db: Session = Depends(get_db)):
    try:
        user = verify_otp(db, req.phone, req.code)
    except OtpError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=schemas.UserOut)
def update_users_me(
    update: schemas.UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    return current_user
