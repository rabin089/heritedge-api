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
MINIO_MEDIA_BUCKET = os.getenv("MINIO_MEDIA_BUCKET")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "false").lower() == "true"
MINIO_PUBLIC_BASE_URL = os.getenv("MINIO_PUBLIC_BASE_URL")
MINIO_MEDIA_PUBLIC_BASE_URL = os.getenv("MINIO_MEDIA_PUBLIC_BASE_URL")

client = Minio(
    endpoint=MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_USE_SSL,
)

import json

def ensure_bucket_public(bucket_name: str):
    """Ensure the specified bucket exists and has public read policy"""
    try:
        # Check if bucket exists, create if not
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
        
        # Set public read policy
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                }
            ]
        }
        client.set_bucket_policy(bucket_name, json.dumps(policy))
        print(f"✅ Bucket '{bucket_name}' set to public read")
    except Exception as e:
        print(f"Warning: Could not set bucket policy for {bucket_name}: {e}")

def upload_file(file_obj: bytes, object_name: str, content_type: str = "application/octet-stream", bucket_name: str = None):
    # Use default bucket if none provided
    target_bucket = bucket_name or MINIO_BUCKET
    ensure_bucket_public(target_bucket)

    file_data = BytesIO(file_obj)
    client.put_object(
        bucket_name=target_bucket,
        object_name=object_name,
        data=file_data,
        length=len(file_obj),
        content_type=content_type,
    )

    # Choose correct base URL based on bucket
    if target_bucket == MINIO_MEDIA_BUCKET:
        base_url = (MINIO_MEDIA_PUBLIC_BASE_URL or "").rstrip("/")
    else:
        base_url = (MINIO_PUBLIC_BASE_URL or "").rstrip("/")
        
    return f"{base_url}/{object_name}"

