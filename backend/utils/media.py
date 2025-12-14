import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Cloudinary
cloudinary.config( 
  cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"), 
  api_key = os.getenv("CLOUDINARY_API_KEY"), 
  api_secret = os.getenv("CLOUDINARY_API_SECRET"),
  secure = True
)

def upload_media(file_file, folder: str = "mini_erp_products"):
    """
    Upload a file (image/video) to Cloudinary.
    Returns dictionary with 'url', 'public_id', 'format'.
    """
    try:
        # Use uploader.upload_stream regarding of file type (auto-detect)
        # For video, resource_type="auto" is best.
        result = cloudinary.uploader.upload(
            file_file, 
            folder=folder,
            resource_type="auto"
        )
        return {
            "url": result.get("secure_url"),
            "public_id": result.get("public_id"),
            "format": result.get("format"),
            "resource_type": result.get("resource_type")
        }
    except Exception as e:
        print(f"Cloudinary Upload Error: {e}")
        return None
