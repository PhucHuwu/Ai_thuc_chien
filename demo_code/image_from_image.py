import base64  # Cần module base64 để mã hóa/giải mã dữ liệu ảnh
import os  # Dùng để truy cập biến môi trường chứa API key
from pathlib import Path  # Hỗ trợ thao tác đường dẫn file rõ ràng

from dotenv import load_dotenv  # Nạp biến môi trường từ file .env
import requests  # Thực hiện cuộc gọi HTTP trực tiếp tới endpoint Gemini

load_dotenv()  # Đảm bảo API key có thể đọc từ file .env

API_KEY = os.getenv("THUCCHIEN_API_KEY")  # Lấy API key từ môi trường sau khi load .env
if not API_KEY:
    raise RuntimeError("Thiếu biến THUCCHIEN_API_KEY trong môi trường hoặc file .env")
MODEL = "gemini-2.5-flash-image-preview"  # Chọn model hỗ trợ chế độ image-to-image
API_URL = (
    f"https://api.thucchien.ai/gemini/v1beta/models/{MODEL}:generateContent"
)  # Xây dựng endpoint gọi tới proxy Gemini

INPUT_PATH = Path(
    "demo_assets/reference_photo.jpg"
)  # Đường dẫn ảnh gốc cần chỉnh sửa (tùy chỉnh lại theo ảnh thực tế của bạn)
if not INPUT_PATH.exists():
    raise FileNotFoundError(
        f"Không tìm thấy file ảnh tại {INPUT_PATH}, hãy chuẩn bị sẵn ảnh mẫu"
    )  # Dừng chương trình sớm nếu ảnh đầu vào chưa được cấp

PROMPT = (
    "Giữ bố cục tổng thể nhưng thêm hiệu ứng đèn neon xanh quanh nhân vật"
)  # Mô tả cách model cần biến đổi ảnh gốc
OUTPUT_PATH = Path("demo_outputs/image_from_image.png")  # File đầu ra để lưu kết quả
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)  # Đảm bảo thư mục lưu tồn tại

image_b64 = base64.b64encode(INPUT_PATH.read_bytes()).decode("utf-8")  # Đọc ảnh gốc và mã hóa sang base64

payload = {
    "contents": [
        {
            "parts": [
                {"text": PROMPT},  # Phần văn bản mô tả yêu cầu chỉnh sửa
                {
                    "inlineData": {
                        "mimeType": "image/jpeg",  # Khai báo đúng định dạng ảnh gốc
                        "data": image_b64,  # Truyền dữ liệu ảnh đã mã hóa base64
                    }
                },
            ]
        }
    ],
    "generationConfig": {"temperature": 0.4},  # Tùy chỉnh độ sáng tạo để kết quả ổn định
}  # Hoàn thiện payload JSON gửi tới API

headers = {
    "x-goog-api-key": API_KEY,  # Gemini yêu cầu header x-goog-api-key thay vì Bearer token
    "Content-Type": "application/json",  # Định dạng nội dung là JSON
}  # Bộ header cần thiết cho request

response = requests.post(API_URL, headers=headers, json=payload, timeout=90)  # Gửi request POST và chờ phản hồi
response.raise_for_status()  # Tự động báo lỗi nếu API trả về mã trạng thái không thành công

candidates = response.json()["candidates"]  # Truy xuất danh sách phương án phản hồi
if not candidates:
    raise RuntimeError("API không trả về ứng viên nào, hãy kiểm tra prompt và ảnh đầu vào")  # Kiểm tra đề phòng kết quả rỗng

image_data = candidates[0]["content"]["parts"][0]["inlineData"]["data"]  # Lấy dữ liệu ảnh base64 từ ứng viên đầu tiên
OUTPUT_PATH.write_bytes(base64.b64decode(image_data))  # Giải mã base64 và lưu ra file ảnh mới

print(f"Đã lưu ảnh chỉnh sửa tại: {OUTPUT_PATH}")  # Thông báo vị trí file đầu ra
