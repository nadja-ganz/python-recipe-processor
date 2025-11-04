import base64
import sys
from io import BytesIO
try:
    import pdfplumber
    from PIL import Image
except ImportError:
    print("Please install required packages:")
    sys.exit(1)


def image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 string."""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    return base64.b64encode(img_bytes).decode('utf-8')