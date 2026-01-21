from minio import Minio
from urllib.parse import urljoin
import os
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "false").lower() == "true"
MINIO_PUBLIC_BASE_URL = os.getenv("MINIO_PUBLIC_BASE_URL")

client = Minio(
    endpoint=MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_USE_SSL,
)

def upload_file(file_obj: bytes, object_name: str, content_type: str = "application/octet-stream"):
    # Convert bytes to file-like object
    file_data = BytesIO(file_obj)
    client.put_object(
        bucket_name=MINIO_BUCKET,
        object_name=object_name,
        data=file_data,
        length=len(file_obj),
        content_type=content_type,
    )
    public_url = urljoin(MINIO_PUBLIC_BASE_URL, object_name)
    return public_url
