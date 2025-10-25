import base64  # Chuyển dữ liệu ảnh qua lại giữa dạng bytes và base64
import os  # Sử dụng biến môi trường cho API key
import time  # Gắn delay giữa các lần thử lại
from pathlib import Path  # Quản lý đường dẫn file gọn gàng

import requests  # Gửi yêu cầu HTTP tới endpoint Gemini
from dotenv import load_dotenv  # Nạp biến môi trường từ file .env

load_dotenv()  # Đảm bảo API key được nạp từ file .env nếu tồn tại

API_KEY = os.getenv("THUCCHIEN_API_KEY")  # API key phải được thiết lập sẵn
if not API_KEY:
    raise RuntimeError("Thiếu biến THUCCHIEN_API_KEY trong môi trường hoặc file .env")
MODEL = "gemini-2.5-flash-image-preview"  # Model hỗ trợ chỉnh ảnh được tài liệu giới thiệu
API_URL = f"https://api.thucchien.ai/gemini/v1beta/models/{MODEL}:generateContent"  # Endpoint chỉnh ảnh


def edit_image(
    *,
    prompt: str,
    image_path: Path,
    output_path: Path,
    retries: int = 2,
    delay_seconds: int = 8,
) -> None:
    """Chỉnh ảnh với cơ chế retry + seed cố định để ổn định kết quả."""
    image_bytes = image_path.read_bytes()  # Đọc toàn bộ ảnh nguồn
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")  # Mã hóa ảnh sang base64
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},  # Phần mô tả chỉnh sửa
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",  # Chú ý đặt đúng MIME tương ứng ảnh nguồn
                            "data": image_b64,  # Ảnh gốc đã mã hóa
                        }
                    },
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.25,  # Nhiệt độ thấp giúp kết quả ít biến thiên khi retry
            "seed": 2211,  # Cố định seed để các lần chạy lại vẫn giữ phong cách tương đương
        },
    }
    headers = {
        "x-goog-api-key": API_KEY,
        "Content-Type": "application/json",
    }
    for attempt in range(1, retries + 2):  # Thử thêm một lần sau số retry cấu hình
        response = requests.post(API_URL, headers=headers, json=payload, timeout=150)
        if response.ok:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                inline_data = candidates[0]["content"]["parts"][0]["inlineData"]
                output_path.write_bytes(base64.b64decode(inline_data["data"]))
                return
            raise RuntimeError("API trả về phản hồi nhưng không chứa dữ liệu ảnh")
        print(
            f"Chỉnh ảnh thất bại lần {attempt} với mã {response.status_code}, nghỉ {delay_seconds}s trước khi thử lại"
        )
        time.sleep(delay_seconds)
    response.raise_for_status()


if __name__ == "__main__":
    source_image = Path("demo_assets/reference_photo.jpg")  # Ảnh mẫu dự phòng
    if not source_image.exists():
        raise SystemExit(
            "Không tìm thấy demo_assets/reference_photo.jpg, hãy thay bằng đường dẫn ảnh thực tế"
        )
    output_dir = Path("alternative_outputs")
    output_dir.mkdir(exist_ok=True)
    edit_image(
        prompt="Tăng ánh sáng ấm và thêm hiệu ứng bụi phát sáng quanh nhân vật",
        image_path=source_image,
        output_path=output_dir / "image_edit_retry.png",
    )
    print("Đã tạo ảnh chỉnh sửa fallback tại alternative_outputs/image_edit_retry.png")
