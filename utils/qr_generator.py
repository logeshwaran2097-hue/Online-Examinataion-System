import qrcode
from io import BytesIO
import base64

def generate_qr_code_base64(data_string):
    """
    Generate a QR code image from the provided data string,
    saves it as PNG in memory, and returns it as a Base64-encoded string.
    Returns: data:image/png;base64,... string
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data_string)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_data = buffer.getvalue()
    
    encoded = base64.b64encode(img_data).decode('utf-8')
    return f"data:image/png;base64,{encoded}"
