import os
from dotenv import load_dotenv
from minio import Minio
from io import BytesIO

load_dotenv()

# MinIO configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "false").lower() == "true"
MINIO_PUBLIC_BASE_URL = os.getenv("MINIO_PUBLIC_BASE_URL")

print(f"MinIO Endpoint: {MINIO_ENDPOINT}")
print(f"MinIO Bucket: {MINIO_BUCKET}")
print(f"Public Base URL: {MINIO_PUBLIC_BASE_URL}")

try:
    client = Minio(
            endpoint=MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_USE_SSL,
        )
    
    # Test upload
    test_data = b"test image data"
    test_filename = "test-image.jpg"
    
    client.put_object(
        bucket_name=MINIO_BUCKET,
        object_name=test_filename,
        data=BytesIO(test_data),
        length=len(test_data),
        content_type="image/jpeg",
    )
    
    public_url = f"{MINIO_PUBLIC_BASE_URL}/{test_filename}"
    print(f"✅ Upload successful!")
    print(f"📁 Object name: {test_filename}")
    print(f"🔗 Public URL: {public_url}")
    
    # Test if object exists
    if client.stat_object(MINIO_BUCKET, test_filename):
        print("✅ Object exists in bucket")
    else:
        print("❌ Object not found in bucket")
        
except Exception as e:
    print(f"❌ Error: {e}")
