import os
import sys
# Add app to path
sys.path.append(os.getcwd())

from app.utils.minio_client import upload_file

def test():
    try:
        data = b"hello minio"
        url = upload_file(data, "test_file_new.txt", "text/plain")
        print(f"Uploaded successfully! URL: {url}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
