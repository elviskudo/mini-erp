from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from utils.media import upload_media
from dependencies import get_current_tenant_id

router = APIRouter(
    prefix="/upload",
    tags=["Uploads"]
)

@router.post("/media")
async def upload_media_file(
    file: UploadFile = File(...),
    # tenant_id: str = Depends(get_current_tenant_id) # Optional: Use for folder naming if needed
):
    """
    Upload an image or video to Cloudinary.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    # Read file content
    contents = await file.read()
    
    # Upload to Cloudinary
    # We pass contents directly. Cloudinary accepts bytes.
    result = upload_media(contents, folder="mini_erp_products")
    
    if not result:
        raise HTTPException(status_code=500, detail="Upload to Cloudinary failed")
        
    return result
