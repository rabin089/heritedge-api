import os
from dotenv import load_dotenv
from minio import Minio

# Load .env file
load_dotenv()

# Load from .env
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "false").lower() == "true"

print(f"Connecting to MinIO at {MINIO_ENDPOINT} (SSL: {MINIO_USE_SSL})")
print(f"Bucket: {MINIO_BUCKET}")
print(f"Access Key: {MINIO_ACCESS_KEY}")

try:
    client = Minio(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_USE_SSL,
    )
    
    # Test connection
    buckets = client.list_buckets()
    print(f"✅ Connected! Buckets: {[b.name for b in buckets]}")
    
    # Check if our bucket exists
    if client.bucket_exists(MINIO_BUCKET):
        print(f"✅ Bucket '{MINIO_BUCKET}' exists")
    else:
        print(f"❌ Bucket '{MINIO_BUCKET}' does not exist")
        
except Exception as e:
    print(f"❌ MinIO connection error: {e}")
    print(f"Error type: {type(e).__name__}")
