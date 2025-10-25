import base64  # Giải mã ảnh trả về khi nhận dạng base64
import os  # Đọc biến môi trường tránh hard-code API key
import time  # Tạo độ trễ giữa các lần retry
from pathlib import Path  # Quản lý đường dẫn thư mục đầu ra

import requests  # Gửi request HTTP trực tiếp đến gateway
from dotenv import load_dotenv  # Cho phép đọc API key từ file .env

load_dotenv()  # Nạp biến môi trường từ file .env trước khi sử dụng

API_KEY = os.getenv("THUCCHIEN_API_KEY")  # API key có thể được nạp từ file .env
if not API_KEY:
    raise RuntimeError("Thiếu biến THUCCHIEN_API_KEY trong môi trường hoặc file .env")
API_URL = "https://api.thucchien.ai/images/generations"  # Endpoint chuẩn theo tài liệu gateway
def generate_image(prompt: str, *, retries: int = 3, delay_seconds: int = 5) -> bytes:
    """Sinh ảnh bằng HTTP thuần, tự retry khi gặp lỗi mạng hoặc 5xx."""
    payload = {
        "model": "imagen-4",  # Model được tài liệu đề xuất cho sinh ảnh chuẩn
        "prompt": prompt,  # Đưa prompt trực tiếp theo yêu cầu của người dùng
        "n": 1,  # Giảm tải bằng cách yêu cầu một ảnh duy nhất
        "aspect_ratio": "1:1",  # Tùy chọn cố định để tránh thất bại do size không hợp lệ
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",  # Chuẩn xác thực giống OpenAI API
        "Content-Type": "application/json",  # Nội dung gửi đi là JSON
    }
    for attempt in range(1, retries + 1):  # Vòng lặp retry đơn giản nếu gặp lỗi
        response = requests.post(API_URL, json=payload, headers=headers, timeout=60)
        if response.ok:  # Thành công thì trả dữ liệu ngay
            data = response.json()
            return base64.b64decode(data["data"][0]["b64_json"])  # Giải mã ảnh sang bytes
        print(
            f"Lần thử {attempt} thất bại với mã {response.status_code}, sẽ thử lại sau {delay_seconds}s"
        )  # Thông báo lỗi giúp debug nhanh
        time.sleep(delay_seconds)  # Chờ trước khi thử lại
    response.raise_for_status()  # Nếu hết retry vẫn lỗi thì ném exception chi tiết

if __name__ == "__main__":
    prompt_text = (
        "Poster sự kiện hackathon phong cách neon, nhân vật chính đeo khăn quàng đỏ"
    )  # Prompt mẫu tránh trùng với demo chính
    output_file = Path("alternative_outputs/image_from_prompt_requests.png")  # Đường dẫn file đầu ra
    output_file.parent.mkdir(parents=True, exist_ok=True)  # Tạo thư mục nếu chưa có

    image_bytes = generate_image(prompt_text)  # Thực thi sinh ảnh
    output_file.write_bytes(image_bytes)  # Lưu ảnh ra ổ đĩa
    print(f"Đã lưu ảnh fallback tại: {output_file}")  # Xác nhận hoàn tất quy trình
