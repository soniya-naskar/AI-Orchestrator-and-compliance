import asyncio
import io
from PIL import Image
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except Exception:
    TESSERACT_AVAILABLE = False

async def ocr_image_bytes(image_bytes) -> list:
    await asyncio.sleep(0.01)
    if not image_bytes:
        return []
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if TESSERACT_AVAILABLE:
            txt = pytesseract.image_to_string(img)
        else:
            txt = 'OCR not available in demo; simulated output: MFA: Disabled'
        return [{'doc_id':'uploaded_screenshot.png','chunk_id':'ocr_1','snippet':txt}]
    except Exception as e:
        return [{'doc_id':'uploaded_screenshot.png','chunk_id':'ocr_error','snippet':f'OCR failed: {str(e)}'}]
