from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.auth import (
    AcceptInviteRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    GoogleAuthRequest,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserBrief,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=LoginResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    result = await svc.register(body.email, body.full_name, body.password, body.tenant_slug)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered or tenant not found",
        )
    return result


@router.post("/google", response_model=LoginResponse)
async def google_auth(body: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    result = await svc.google_auth(body.id_token)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authentication failed",
        )
    return result


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    result = await svc.login(body.email, body.password)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return result


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    new_access = await svc.refresh_access_token(body.refresh_token)
    if new_access is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    return TokenResponse(access_token=new_access)


@router.post("/logout")
async def logout(user: User = Depends(get_current_user)):
    import asyncio
    from app.core.config import settings

    try:
        import redis as redis_lib

        def _blacklist_token():
            r = redis_lib.from_url(settings.REDIS_URL)
            r.setex(f"bl:{str(user.id)}", settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60, "1")
            r.close()

        await asyncio.get_running_loop().run_in_executor(None, _blacklist_token)
    except Exception:
        pass

    return {"success": True, "message": "Logged out"}


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    token = await svc.forgot_password(body.email)
    if token:
        from app.services.notification_service import NotificationService
        notif_svc = NotificationService(db)
        await notif_svc.send_password_reset(body.email, token)
    return {"success": True, "message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    success = await svc.reset_password(body.token, body.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    return {"success": True, "message": "Password has been reset"}


@router.post("/accept-invite", response_model=LoginResponse)
async def accept_invite(body: AcceptInviteRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    result = await svc.accept_invite(body.token, body.full_name, body.password)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation",
        )
    return result


@router.get("/me", response_model=UserBrief)
async def get_me(user: User = Depends(get_current_user)):
    return UserBrief(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
    )


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.security import verify_password, hash_password

    if not user.password_hash or not verify_password(body.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    user.password_hash = hash_password(body.new_password)
    await db.flush()
    return {"success": True, "message": "Password changed successfully"}
