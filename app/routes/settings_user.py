from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models import Settings, User
from ..schemas import SettingsCreate, SettingsRead
from ..db import get_db
from ..services.session_manager import get_current_user

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/", response_model=SettingsRead)
async def get_settings(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(select(Settings).where(Settings.user_id == user_id))
    settings = result.scalars().first()

    if not settings:
        # Create default settings if none exist
        settings = Settings(user_id=user_id, notifications_enabled=True, theme="light")
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings


@router.post("/", response_model=SettingsRead)
async def upsert_settings(data: SettingsCreate, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(select(Settings).where(Settings.user_id == user_id))
    settings = result.scalars().first()

    if settings:
        # Update existing settings
        for key, value in data.dict(exclude_unset=True).items():
            setattr(settings, key, value)
        await db.commit()
        await db.refresh(settings)
    else:
        # Create new settings
        settings = Settings(user_id=user_id, **data.dict())
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings