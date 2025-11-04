import qrcode
import os

# URL của website (thay bằng URL thật khi deploy, ví dụ: https://your-app.onrender.com)
url = "http://localhost:5000/"

# Tạo QR code
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)
qr.add_data(url)
qr.make(fit=True)

# Tạo ảnh QR với màu theme
img = qr.make_image(fill_color="#FABBCB", back_color="white")

# Lưu vào static/
output_path = os.path.join('static', 'qr_code.png')
img.save(output_path)
print(f"Đã tạo QR code tại: {output_path}")