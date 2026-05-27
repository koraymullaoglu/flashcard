import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://flashcard:flashcard@localhost:5432/flashcard",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("SECRET_KEY", "dev-secret-key"))
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "flashcard-exports")
    S3_REGION = os.getenv("S3_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
    S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
    S3_EXPORT_PREFIX = os.getenv("S3_EXPORT_PREFIX", "exports")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
