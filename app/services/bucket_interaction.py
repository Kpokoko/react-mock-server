import uuid
from fastapi import UploadFile
import aioboto3
from ..config import settings

session = aioboto3.Session()

def get_s3_client():
    return session.client(
        service_name="s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
    )


async def upload_image_to_s3(file: UploadFile) -> str:
    """
    Загружает файл в Yandex Cloud Object Storage и возвращает уникальный ключ (s3_key)
    """
    key = f"images/{uuid.uuid4().hex}_{file.filename}"

    async with get_s3_client() as s3:
        await s3.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=await file.read(),
            ContentType=file.content_type
        )

    return key


async def generate_presigned_url(key: str, expires: int = 300) -> str:
    """
    Генерирует временный presigned URL для приватного объекта
    """
    async with get_s3_client() as s3:
        return await s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET_NAME, "Key": key},
            ExpiresIn=expires
        )
