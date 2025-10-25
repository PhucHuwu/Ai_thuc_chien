import os  # Lấy API key từ biến môi trường
from pathlib import Path  # Xử lý đường dẫn file đầu ra
import requests  # Gửi yêu cầu HTTP tới gateway

from dotenv import load_dotenv  # Cho phép đọc biến môi trường từ file .env

load_dotenv()  # Nạp biến môi trường từ file .env nếu tồn tại

API_KEY = os.getenv("THUCCHIEN_API_KEY")  # Đọc API key từ môi trường hoặc file .env
if not API_KEY:
    raise RuntimeError("Thiếu biến THUCCHIEN_API_KEY trong môi trường hoặc file .env")
API_URL = "https://api.thucchien.ai/audio/speech"  # Endpoint Text-to-Speech của gateway
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",  # TTS sử dụng chuẩn Bearer token của OpenAI API
    "Content-Type": "application/json",  # Định dạng nội dung là JSON
}  # Bộ header cố định cho mọi request TTS

SCRIPT_TEXT = (
    "Xin chào mọi người! Đây là bản demo chuyển văn bản thành giọng nói qua AI Thực Chiến gateway."
)  # Nội dung kịch bản muốn đọc thành tiếng
OUTPUT_PATH = Path("demo_outputs/text_to_speech.mp3")  # Đường dẫn file âm thanh xuất ra
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)  # Đảm bảo thư mục đích tồn tại

payload = {
    "model": "gemini-2.5-flash-preview-tts",  # Chọn model TTS được gateway hỗ trợ
    "input": SCRIPT_TEXT,  # Truyền kịch bản văn bản cần đọc
    "voice": "Zephyr",  # Đặt tên giọng đọc phù hợp (tham khảo thêm trong tài liệu)
    "format": "mp3",  # Yêu cầu định dạng file âm thanh MP3 phổ biến
}  # Payload JSON gửi tới API

response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)  # Gửi yêu cầu tạo giọng nói
response.raise_for_status()  # Kiểm tra và thông báo nếu API trả mã lỗi
OUTPUT_PATH.write_bytes(response.content)  # Ghi trực tiếp dữ liệu âm thanh nhị phân ra file mp3

print(f"Đã lưu file âm thanh tại: {OUTPUT_PATH}")  # Thông báo vị trí lưu kết quả
