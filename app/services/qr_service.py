import qrcode
import io
import base64
import secrets
import json

def generate_qr_code(data: dict) -> str:
    """
    Generate QR code from data dict and return as base64 PNG.
    """
    payload = json.dumps(data)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"

def generate_qr_token() -> str:
    """Generate a secure QR token."""
    return secrets.token_urlsafe(12)