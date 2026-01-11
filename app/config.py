from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    session_expire_minutes: int = 60
    upload_dir: str = "uploads"

    S3_ENDPOINT_URL: str = "https://storage.yandexcloud.net"
    S3_REGION: str = "ru-central1"
    S3_BUCKET_NAME: str = "dangeon-bucket-image"

    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
