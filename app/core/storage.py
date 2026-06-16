import asyncio
import uuid
from pathlib import Path

import boto3
from fastapi import UploadFile

from app.core.config import settings

s3_client = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
)


async def upload_file(file: UploadFile, folder: str) -> str:
    ext = Path(file.filename).suffix if file.filename else ""
    filename = f"{folder}/{uuid.uuid4()}{ext}"

    contents = await file.read()

    def _upload():
        s3_client.put_object(
            Bucket=settings.S3_BUCKET,
            Key=filename,
            Body=contents,
            ContentType=file.content_type,
        )

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _upload)

    return f"{settings.S3_ENDPOINT}/{settings.S3_BUCKET}/{filename}"


async def upload_file_bytes(filename: str | None, content_type: str | None, data: bytes, folder: str) -> str:
    """Upload pre-read bytes directly — avoids double-reading an UploadFile stream."""
    from pathlib import Path as _Path
    ext = _Path(filename).suffix if filename else ""
    key = f"{folder}/{uuid.uuid4()}{ext}"

    def _upload():
        s3_client.put_object(
            Bucket=settings.S3_BUCKET,
            Key=key,
            Body=data,
            ContentType=content_type or "application/octet-stream",
        )

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _upload)
    return f"{settings.S3_ENDPOINT}/{settings.S3_BUCKET}/{key}"
