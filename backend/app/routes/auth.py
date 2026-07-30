import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

try:
    import structlog
    logger = structlog.get_logger()
except ImportError:
    logger = logging.getLogger("auth_router")

from app.auth.jwt_handler import create_access_token
from app.auth.passwords import hash_password, verify_password
from app.dependencies import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserResponse

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(User)
        .filter(
            (User.username == user.username)
            | (User.email == user.email)
        )
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists.",
        )

    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password),
        role=user.role.upper() if user.role else "USER",
        department=user.department,
    )

    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists.",
        )

    try:
        logger.info("User registered successfully", username=new_user.username, role=new_user.role)
    except Exception:
        pass

    return new_user


@router.post(
    "/login",
    response_model=Token,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(
            User.username == form_data.username,
            User.is_active == True,
            User.is_deleted == False,
        )
        .first()
    )

    if not user or not verify_password(form_data.password, user.password_hash):
        try:
            logger.warning("Failed login attempt", username=form_data.username)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    access_token = create_access_token(
        {
            "sub": user.username,
            "role": user.role,
            "user_id": user.id,
        }
    )

    try:
        logger.info("User logged in", username=user.username, role=user.role)
    except Exception:
        pass

    return Token(
        access_token=access_token,
        token_type="bearer",
    )