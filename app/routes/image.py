from typing import List

from fastapi import FastAPI, File, UploadFile, Depends, APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import os
import uuid

from ..config import settings
from ..models import Image
from ..db import get_db
from ..schemas import ImageRead

router = APIRouter(prefix="/image", tags=["image"])

@router.post("/load", response_model=ImageRead)
async def upload_image(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.content_type.startswith("image/"):
        return JSONResponse(content={"error": "File is not an image"}, status_code=400)

    # Уникальное имя файла
    file_ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(settings.upload_dir, unique_name)

    # Сохраняем файл
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Сохраняем запись в БД
    image_record = Image(
        filename=unique_name,
        filepath=file_path,
        content_type=file.content_type,
    )
    db.add(image_record)
    await db.commit()
    await db.refresh(image_record)

    return ImageRead(
        id = image_record.id,
        filename = image_record.filename,
        filepath = image_record.filepath,
    )
