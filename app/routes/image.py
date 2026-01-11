from typing import List

from app.services.bucket_interaction import upload_image_to_s3
from fastapi import FastAPI, File, UploadFile, Depends, APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import os
import uuid

from ..config import settings
from ..models import Image, ImageUser
from ..db import get_db
from ..schemas import ImageRead
from ..services.session_manager import get_current_user

router = APIRouter(prefix="/image", tags=["image"])

@router.post("/load/public", response_model=ImageRead)
async def upload_image(request: Request, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not file.content_type.startswith("image/"):
        return JSONResponse(content={"error": "File is not an image"}, status_code=400)
    
    key = await upload_image_to_s3(file)
    
    file_ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4().hex}{file_ext}"

    # Сохраняем запись в БД
    image_record = Image(
        filename=unique_name,
        filepath=key,
        content_type=file.content_type,
    )

    db.add(image_record)
    await db.commit()
    await db.refresh(image_record)

    user_image_record = ImageUser(
        user_id=user_id,
        image_id=image_record.id,
        private=False,
    )

    db.add(user_image_record)
    await db.commit()

    return ImageRead(
        id = image_record.id,
        filename = image_record.filename,
        filepath = image_record.filepath,
    )


@router.post("/load/private", response_model=ImageRead)
async def upload_image(request: Request, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not file.content_type.startswith("image/"):
        return JSONResponse(content={"error": "File is not an image"}, status_code=400)

    key = await upload_image_to_s3(file)

    file_ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4().hex}{file_ext}"

    # Сохраняем запись в БД
    image_record = Image(
        filename=unique_name,
        filepath=key,
        content_type=file.content_type,
    )



    db.add(image_record)
    await db.commit()
    await db.refresh(image_record)

    user_image_record = ImageUser(
        user_id=user_id,
        image_id=image_record.id,
        private=True,
    )

    db.add(user_image_record)
    await db.commit()

    return ImageRead(
        id = image_record.id,
        filename = image_record.filename,
        filepath = image_record.filepath,
    )
