from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.utils.minio_client import upload_file
from app.models.user import User
from app.api.v1.auth import get_current_user
import uuid

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/")
async def upload_file_endpoint(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        contents = await file.read()
        ext = file.filename.split(".")[-1] if "." in file.filename else ""
        object_name = f"{uuid.uuid4()}.{ext}"
        public_url = upload_file(contents, object_name, content_type=file.content_type)
        return {"filename": object_name, "url": public_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
