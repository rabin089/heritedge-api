import os
from dotenv import load_dotenv
from minio import Minio
from urllib.parse import urljoin
from io import BytesIO

# Load environment variables
load_dotenv()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "false").lower() == "true"
MINIO_PUBLIC_BASE_URL = os.getenv("MINIO_PUBLIC_BASE_URL")

print("=== Upload Debug Test ===")
print(f"ENDPOINT: {MINIO_ENDPOINT}")
print(f"ACCESS_KEY: {MINIO_ACCESS_KEY}")
print(f"BUCKET: {MINIO_BUCKET}")
print(f"USE_SSL: {MINIO_USE_SSL}")
print(f"PUBLIC_BASE_URL: {MINIO_PUBLIC_BASE_URL}")

try:
    # Create MinIO client
    client = Minio(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_USE_SSL,
    )
    
    print("\n✅ MinIO client created successfully")
    
    # Test bucket existence
    if client.bucket_exists(MINIO_BUCKET):
        print(f"✅ Bucket '{MINIO_BUCKET}' exists")
        
        # Test upload with dummy data
        test_data = b"Hello, this is a test file!"
        object_name = "test-upload.txt"
        
        file_data = BytesIO(test_data)
        client.put_object(
            bucket_name=MINIO_BUCKET,
            object_name=object_name,
            data=file_data,
            length=len(test_data),
            content_type="text/plain",
        )
        
        public_url = urljoin(MINIO_PUBLIC_BASE_URL, object_name)
        print(f"✅ Upload successful!")
        print(f"📁 Object name: {object_name}")
        print(f"🔗 Public URL: {public_url}")
        
        # Clean up test file
        client.remove_object(MINIO_BUCKET, object_name)
        print("🧹 Test file cleaned up")
        
    else:
        print(f"❌ Bucket '{MINIO_BUCKET}' does not exist")
        print("Available buckets:")
        buckets = client.list_buckets()
        for bucket in buckets:
            print(f"  - {bucket.name}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
