import base64  # Mã hóa ảnh mẫu sang base64 để gửi kèm yêu cầu
import os  # Lấy API key từ biến môi trường
import time  # Chờ giữa các lần kiểm tra trạng thái
from pathlib import Path  # Làm việc với đường dẫn file rõ ràng
import requests  # Thực hiện các request HTTP tới gateway

from dotenv import load_dotenv  # Đọc biến môi trường từ file .env để linh hoạt cấu hình

load_dotenv()  # Nạp biến môi trường từ file .env

API_KEY = os.getenv("THUCCHIEN_API_KEY")  # Đọc API key do người dùng cấu hình từ environment hoặc .env
if not API_KEY:
    raise RuntimeError("Thiếu biến THUCCHIEN_API_KEY trong môi trường hoặc file .env")
API_ROOT = "https://api.thucchien.ai/gemini/v1beta"  # Gốc endpoint cho dòng Gemini
DOWNLOAD_ROOT = "https://api.thucchien.ai/gemini/download"  # Endpoint tải dữ liệu media
MODEL = "veo-3.0-generate-001"  # Sử dụng model Veo 3 cho tác vụ image-to-video

INPUT_PATH = Path(
    "demo_assets/video_reference.jpg"
)  # Ảnh mẫu để model dựa vào khi tạo chuyển động
if not INPUT_PATH.exists():
    raise FileNotFoundError(
        f"Không tìm thấy ảnh mẫu tại {INPUT_PATH}, hãy cung cấp file phù hợp"
    )  # Dừng sớm nếu ảnh đầu vào chưa được đặt đúng vị trí

PROMPT = (
    "Biến tấm ảnh thành cảnh chuyển động chậm, làm nổi bật dòng nước chảy và ánh sáng lấp lánh"
)  # Mô tả cách muốn video phát triển từ ảnh gốc
OUTPUT_PATH = Path("demo_outputs/video_from_image.mp4")  # File đích để lưu video kết quả
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)  # Đảm bảo thư mục demo_outputs tồn tại

image_b64 = base64.b64encode(INPUT_PATH.read_bytes()).decode("utf-8")  # Chuyển dữ liệu ảnh sang chuỗi base64

start_url = f"{API_ROOT}/models/{MODEL}:predictLongRunning"  # Endpoint khởi tạo tác vụ video
start_payload = {
    "instances": [
        {
            "prompt": PROMPT,  # Văn bản hướng dẫn chuyển động
            "image": {
                "bytesBase64Encoded": image_b64,  # Ảnh tĩnh làm nguồn tham chiếu
                "mimeType": "image/jpeg",  # Khai báo đúng định dạng ảnh nhập
            },
            "parameters": {
                "aspectRatio": "16:9",  # Thiết lập tỷ lệ khung hình 16:9 phổ biến
                "resolution": "720p",  # Chọn độ phân giải để tối ưu thời gian xử lý
                "personGeneration": "allow_adult",  # Bật quyền tạo nhân vật người trong chế độ image-to-video
            },
        }
    ]
}  # Payload hoàn chỉnh gửi tới API

headers = {
    "x-goog-api-key": API_KEY,  # Truyền API key theo yêu cầu của gateway Gemini
    "Content-Type": "application/json",  # Khai báo kiểu dữ liệu JSON
}  # Bộ header dùng cho toàn bộ quy trình

start_response = requests.post(start_url, headers=headers, json=start_payload, timeout=120)  # Gửi yêu cầu khởi tạo tác vụ image-to-video
start_response.raise_for_status()  # Báo lỗi nếu request không thành công
operation_name = start_response.json()["name"]  # Trích xuất tên tác vụ để theo dõi
print(f"Đã khởi tạo tác vụ video từ ảnh: {operation_name}")  # Thông báo operation đã tạo

status_url = f"{API_ROOT}/{operation_name}"  # Endpoint kiểm tra trạng thái tác vụ
video_id = None  # Biến lưu ID video sau khi hoàn tất
while video_id is None:  # Tiếp tục kiểm tra cho đến khi có kết quả
    status_response = requests.get(status_url, headers={"x-goog-api-key": API_KEY}, timeout=60)  # Gọi API kiểm tra trạng thái
    status_response.raise_for_status()  # Dừng nếu gặp lỗi HTTP
    payload = status_response.json()  # Đọc dữ liệu JSON trả về
    if payload.get("done"):  # Khi tác vụ hoàn thành
        samples = payload["response"]["generateVideoResponse"]["generatedSamples"]  # Lấy danh sách video tạo ra
        uri = samples[0]["video"]["uri"]  # URI chứa đường dẫn tải video
        path_fragment = uri.split("/")[-1]  # Phần cuối URI chứa video_id và tham số
        video_id = path_fragment.split(":")[0]  # Tách video_id khỏi phần :download
        print(f"Video từ ảnh đã sẵn sàng với video_id: {video_id}")  # Báo cho người dùng biết kết quả
    else:
        print("Tác vụ vẫn đang xử lý, đợi 20 giây rồi kiểm tra lại...")  # Thông báo trạng thái chờ
        time.sleep(20)  # Nghỉ 20 giây trước khi kiểm tra tiếp

download_url = f"{DOWNLOAD_ROOT}/v1beta/files/{video_id}:download?alt=media"  # Endpoint để tải video hoàn chỉnh
with requests.get(download_url, headers={"x-goog-api-key": API_KEY}, timeout=300, stream=True) as download_response:
    download_response.raise_for_status()  # Đảm bảo request tải xuống hợp lệ
    with OUTPUT_PATH.open("wb") as file_handle:  # Mở file đích ở chế độ ghi nhị phân
        for chunk in download_response.iter_content(chunk_size=1_048_576):  # Ghi dữ liệu theo từng khối 1MB
            if chunk:  # Bỏ qua chunk rỗng
                file_handle.write(chunk)  # Lưu dữ liệu chunk vào file mp4

print(f"Đã lưu video sinh từ ảnh tại: {OUTPUT_PATH}")  # Xác nhận vị trí file kết quả
