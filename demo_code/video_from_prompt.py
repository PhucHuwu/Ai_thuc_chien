import os  # Dùng để lấy API key từ biến môi trường
import time  # Hỗ trợ tạm dừng giữa các lần kiểm tra trạng thái
from pathlib import Path  # Quản lý đường dẫn file đầu ra
import requests  # Thực hiện các cuộc gọi HTTP đến gateway

from dotenv import load_dotenv  # Cho phép đọc API key từ file .env

load_dotenv()  # Nạp biến môi trường từ file .env nếu tồn tại

API_KEY = os.getenv("THUCCHIEN_API_KEY")  # Đọc API key gateway do người dùng cung cấp
if not API_KEY:
    raise RuntimeError("Thiếu biến THUCCHIEN_API_KEY trong môi trường hoặc file .env")
API_ROOT = "https://api.thucchien.ai/gemini/v1beta"  # Gốc endpoint cho các thao tác Veo
DOWNLOAD_ROOT = "https://api.thucchien.ai/gemini/download"  # Gốc endpoint tải video
MODEL = "veo-3.0-generate-001"  # Chọn model Veo 3 phiên bản chuẩn
HEADERS = {
    "x-goog-api-key": API_KEY,  # Veo yêu cầu gửi key qua header x-goog-api-key
    "Content-Type": "application/json",  # Định nghĩa kiểu nội dung JSON
}  # Bộ header dùng chung cho mọi request

PROMPT = (
    "Một cảnh quay flycam qua cánh đồng quạt gió lúc bình minh, màu sắc ấm áp"
)  # Nội dung video mong muốn theo dạng text-to-video
OUTPUT_PATH = Path("demo_outputs/video_from_prompt.mp4")  # File đích để lưu video tải về
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)  # Tạo thư mục demo_outputs nếu chưa có

start_url = f"{API_ROOT}/models/{MODEL}:predictLongRunning"  # Endpoint khởi tạo tác vụ video
start_payload = {"instances": [{"prompt": PROMPT}]}  # Payload tối giản chỉ gồm prompt văn bản
start_response = requests.post(start_url, headers=HEADERS, json=start_payload, timeout=60)  # Gửi yêu cầu khởi tạo tác vụ
start_response.raise_for_status()  # Ngăn tiếp tục nếu API trả lỗi
operation_name = start_response.json()["name"]  # Lấy tên tác vụ dạng models/.../operations/...
print(f"Đã khởi tạo tác vụ video: {operation_name}")  # Thông báo người dùng biết operation nhận được

status_url = f"{API_ROOT}/{operation_name}"  # Endpoint kiểm tra trạng thái tác vụ
video_id = None  # Chuẩn bị biến lưu ID video sau khi hoàn tất
while video_id is None:  # Lặp cho đến khi nhận được ID video
    status_response = requests.get(status_url, headers={"x-goog-api-key": API_KEY}, timeout=60)  # Gửi yêu cầu GET kiểm tra trạng thái
    status_response.raise_for_status()  # Kiểm tra lỗi kết nối hoặc xác thực
    payload = status_response.json()  # Đọc dữ liệu JSON phản hồi
    if payload.get("done"):  # Nếu tác vụ đã hoàn tất
        samples = payload["response"]["generateVideoResponse"]["generatedSamples"]  # Lấy danh sách mẫu video tạo được
        uri = samples[0]["video"]["uri"]  # Lấy URI tải xuống từ mẫu đầu tiên
        path_fragment = uri.split("/")[-1]  # Cắt lấy phần cuối URI chứa video_id
        video_id = path_fragment.split(":")[0]  # Tách video_id trước chuỗi :download
        print(f"Video sẵn sàng với video_id: {video_id}")  # Thông báo video đã sẵn sàng
    else:
        print("Tác vụ chưa xong, đợi 15 giây rồi kiểm tra lại...")  # Báo cho người dùng biết đang chờ
        time.sleep(15)  # Nghỉ 15 giây trước lần kiểm tra tiếp theo

download_url = f"{DOWNLOAD_ROOT}/v1beta/files/{video_id}:download?alt=media"  # Endpoint tải video hoàn chỉnh
with requests.get(download_url, headers={"x-goog-api-key": API_KEY}, timeout=300, stream=True) as download_response:
    download_response.raise_for_status()  # Đảm bảo yêu cầu tải xuống thành công
    with OUTPUT_PATH.open("wb") as file_handle:  # Mở file đích ở chế độ ghi nhị phân
        for chunk in download_response.iter_content(chunk_size=1_048_576):  # Đọc dữ liệu theo từng khối 1MB
            if chunk:  # Bỏ qua khối rỗng để tránh ghi thừa
                file_handle.write(chunk)  # Ghi khối dữ liệu vào file mp4

print(f"Đã lưu video sinh từ prompt tại: {OUTPUT_PATH}")  # Xác nhận đường dẫn file kết quả
