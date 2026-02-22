import os
from dotenv import load_dotenv
from minio import Minio

# Load environment variables
load_dotenv()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "false").lower() == "true"

print("=== Setting Bucket to Public ===")
print(f"Endpoint: {MINIO_ENDPOINT}")
print(f"Bucket: {MINIO_BUCKET}")
print(f"SSL: {MINIO_USE_SSL}")

try:
    client = Minio(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_USE_SSL,
    )
    
    # Check if bucket exists
    if not client.bucket_exists(MINIO_BUCKET):
        print(f"❌ Bucket '{MINIO_BUCKET}' does not exist")
        print("Available buckets:")
        buckets = client.list_buckets()
        for bucket in buckets:
            print(f"  - {bucket.name}")
        exit(1)
    
    # Set public read policy
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{MINIO_BUCKET}/*"]
            }
        ]
    }
    
    import json
    client.set_bucket_policy(MINIO_BUCKET, json.dumps(policy))
    print(f"✅ Bucket '{MINIO_BUCKET}' is now public!")
    
    # Verify policy
    current_policy = client.get_bucket_policy(MINIO_BUCKET)
    print("📋 Current policy applied successfully")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")
