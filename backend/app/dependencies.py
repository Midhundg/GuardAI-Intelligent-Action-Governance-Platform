import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

try:
    import structlog
    logger = structlog.get_logger()
except ImportError:
    logger = logging.getLogger("dependencies")

from app.auth.jwt_handler import verify_access_token
from app.database import SessionLocal
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_access_token(token)
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception as e:
        try:
            logger.warning("JWT verification failed", error=str(e))
        except Exception:
            pass
        raise credentials_exception

    user = (
        db.query(User)
        .filter(
            User.username == username,
            User.is_active == True,
            User.is_deleted == False,
        )
        .first()
    )

    if user is None:
        raise credentials_exception

    return user


def require_roles(*roles):
    """Enforce Role-Based Access Control (RBAC). Case-insensitive matching."""
    allowed_roles = {r.upper() for r in roles}
    if "USER" in allowed_roles:
        allowed_roles.add("EMPLOYEE")

    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_role = current_user.role.upper()
        if user_role != "ADMIN" and user_role not in allowed_roles:
            try:
                logger.warning(
                    "Access denied for user",
                    user=current_user.username,
                    role=current_user.role,
                    required_roles=list(roles),
                )
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to perform this action.",
            )

        return current_user

    return role_checker