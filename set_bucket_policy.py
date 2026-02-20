import os
from dotenv import load_dotenv
from minio import Minio
import json

load_dotenv()

# MinIO configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "false").lower() == "true"

# Public read-only policy for the bucket
public_policy = {
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

def set_public_policy():
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
            return
        
        # Set public read policy
        policy_json = json.dumps(public_policy)
        client.set_bucket_policy(MINIO_BUCKET, policy_json)
        
        print(f"✅ Successfully set public policy for bucket '{MINIO_BUCKET}'")
        print(f"📝 Policy: {policy_json}")
        
        # Test public access by listing objects
        objects = client.list_objects(MINIO_BUCKET)
        print(f"📁 Objects in bucket: {[obj.object_name for obj in objects]}")
        
    except Exception as e:
        print(f"❌ Error setting bucket policy: {e}")

if __name__ == "__main__":
    set_public_policy()
