import base64  # Sử dụng module base64 để giải mã dữ liệu ảnh trả về từ API
import os  # Lấy biến môi trường chứa API key
from pathlib import Path  # Quản lý đường dẫn file đầu ra một cách an toàn

from dotenv import load_dotenv  # Đọc biến môi trường từ file .env nếu có
from openai import OpenAI  # Dùng client OpenAI tương thích với chuẩn gateway

load_dotenv()  # Nạp biến môi trường từ file .env ở thư mục dự án

API_BASE_URL = "https://api.thucchien.ai"  # Đặt URL gốc của gateway AI Thực Chiến
API_KEY = os.getenv("THUCCHIEN_API_KEY")  # Đọc API key từ biến môi trường hoặc file .env
if not API_KEY:
    raise RuntimeError("Thiếu biến THUCCHIEN_API_KEY trong môi trường hoặc file .env")
CLIENT = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)  # Khởi tạo client với key và base URL tùy chỉnh

PROMPT = (
    "Tạo một poster sự kiện công nghệ phong cách tương lai với tông màu xanh tím"
)  # Chuẩn bị prompt mô tả chi tiết nội dung hình ảnh mong muốn
OUTPUT_PATH = Path("demo_outputs/image_from_prompt.png")  # Khai báo đường dẫn file ảnh sẽ lưu
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)  # Tạo thư mục đích nếu chưa tồn tại

result = CLIENT.images.generate(
    model="imagen-4",  # Chỉ định model sinh ảnh đang được gateway hỗ trợ
    prompt=PROMPT,  # Truyền prompt mô tả cho model
    n=1,  # Yêu cầu tạo một hình ảnh duy nhất
    aspect_ratio="16:9",  # Lựa chọn tỷ lệ khung hình phù hợp với poster
)  # Gửi yêu cầu sinh ảnh và nhận về kết quả

image_b64 = result.data[0].b64_json  # Lấy dữ liệu ảnh đầu tiên ở dạng base64
OUTPUT_PATH.write_bytes(base64.b64decode(image_b64))  # Giải mã base64 và ghi thành file PNG

print(f"Đã lưu ảnh sinh từ prompt tại: {OUTPUT_PATH}")  # Thông báo vị trí file để tiện kiểm tra
