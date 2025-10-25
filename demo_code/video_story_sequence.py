import base64  # Mã hóa/giải mã dữ liệu ảnh cho tham chiếu frame
import os  # Lấy API key từ biến môi trường
import time  # Thực hiện chờ giữa các lần kiểm tra trạng thái
from pathlib import Path  # Quản lý đường dẫn lưu video và frame

import requests  # Gửi request HTTP đến gateway
from dotenv import load_dotenv  # Cho phép đọc API key từ file .env

try:
    import cv2  # Đọc và trích xuất khung hình video
except ImportError as exc:  # Xử lý khi thư viện chưa được cài
    raise SystemExit(
        "Chưa cài đặt opencv-python, hãy chạy: pip install opencv-python"
    ) from exc

load_dotenv()  # Nạp biến môi trường từ file .env trước khi sử dụng

API_KEY = os.getenv("THUCCHIEN_API_KEY")  # Lấy API key dùng chung cho các request
if not API_KEY:
    raise RuntimeError("Thiếu biến THUCCHIEN_API_KEY trong môi trường hoặc file .env")
API_ROOT = "https://api.thucchien.ai/gemini/v1beta"  # Endpoint gốc cho thao tác Gemini
DOWNLOAD_ROOT = "https://api.thucchien.ai/gemini/download"  # Endpoint tải kết quả video
MODEL = "veo-3.0-generate-001"  # Model Veo chuẩn cho quy trình story-telling

BASE_PROMPT = (
    "Phong cách phim hoạt hình 3D tươi sáng, nhân vật chính là cô bé quàng khăn đỏ,"
    " gam màu ấm và ánh sáng mềm mịn."
)  # Thiết lập phong cách chủ đạo để giữ sự đồng nhất

SCENES = [
    "Cảnh mở đầu, cô bé bước vào khu rừng với chiếc khăn đỏ nổi bật.",
    "Cô bé trò chuyện với chú chim xanh trên cành cây.",
    "Cô bé phát hiện ra con đường dẫn tới nhà bà ngoại.",
    "Sói xuất hiện phía sau thân cây lớn, dõi theo cô bé.",
    "Cô bé gõ cửa nhà bà ngoại và gọi to.",
    "Sói cải trang thành bà ngoại nằm trên giường.",
    "Cô bé nhận ra đôi mắt lấp lánh khác thường của 'bà'.",
    "Thợ săn nghe tiếng kêu cứu và lao tới.",
    "Thợ săn giải cứu cô bé và bà ngoại khỏi bụng sói.",
    "Cả nhóm quây quần bên bàn ăn, kết thúc hạnh phúc.",
]  # Danh sách mô tả từng video trong chuỗi câu chuyện

OUTPUT_DIR = Path("demo_outputs/red_riding_hood_video")  # Thư mục chứa video đầu ra
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)  # Tạo thư mục nếu chưa có

HEADERS = {
    "x-goog-api-key": API_KEY,  # Header xác thực bắt buộc cho API Gemini
    "Content-Type": "application/json",  # Khai báo kiểu nội dung JSON
}  # Bộ header dùng lặp lại trong các request

def start_video_job(prompt: str, reference_b64: str | None) -> str:
    """Gửi yêu cầu tạo video, có thể kèm frame tham chiếu."""
    payload = {
        "instances": [
            {
                "prompt": prompt,  # Nội dung mô tả cho cảnh hiện tại
                "parameters": {
                    "aspectRatio": "16:9",  # Cố định tỷ lệ khung hình để đồng bộ
                    "resolution": "720p",  # Chọn độ phân giải vừa phải để tối ưu thời gian
                    "personGeneration": "allow_adult",  # Đáp ứng yêu cầu image-to-video
                },
            }
        ]
    }  # Payload khởi tạo cơ bản
    if reference_b64 is not None:  # Nếu có frame tham chiếu từ video trước
        payload["instances"][0]["image"] = {
            "bytesBase64Encoded": reference_b64,  # Đính kèm dữ liệu ảnh cuối làm tham chiếu
            "mimeType": "image/png",  # Khai báo định dạng ảnh tham chiếu
        }
    response = requests.post(
        f"{API_ROOT}/models/{MODEL}:predictLongRunning",  # Endpoint Bước 1
        headers=HEADERS,
        json=payload,
        timeout=120,
    )  # Gửi yêu cầu tạo video mới
    response.raise_for_status()  # Báo lỗi nếu yêu cầu thất bại
    return response.json()["name"]  # Trả về operation_name để theo dõi

def wait_for_video(operation_name: str) -> str:
    """Polling trạng thái cho tới khi video sẵn sàng và trả về video_id."""
    status_url = f"{API_ROOT}/{operation_name}"  # Endpoint Bước 2
    while True:  # Lặp cho tới khi hoàn tất
        response = requests.get(
            status_url,
            headers={"x-goog-api-key": API_KEY},
            timeout=60,
        )  # Gửi yêu cầu kiểm tra trạng thái
        response.raise_for_status()  # Kiểm tra lỗi HTTP
        payload = response.json()  # Đọc nội dung JSON
        if payload.get("done"):  # Khi tác vụ báo hoàn tất
            samples = payload["response"]["generateVideoResponse"]["generatedSamples"]  # Lấy danh sách video
            uri = samples[0]["video"]["uri"]  # URI tải video đầu tiên
            path_fragment = uri.split("/")[-1]  # Phần cuối URL chứa video_id và tham số
            return path_fragment.split(":")[0]  # Tách video_id và trả về
        print("Video chưa sẵn sàng, chờ 20 giây...")  # Thông báo trạng thái chờ
        time.sleep(20)  # Nghỉ trước lần kiểm tra tiếp theo

def download_video(video_id: str, output_path: Path) -> None:
    """Tải video hoàn chỉnh về máy và lưu theo đường dẫn chỉ định."""
    download_url = f"{DOWNLOAD_ROOT}/v1beta/files/{video_id}:download?alt=media"  # Endpoint Bước 3
    with requests.get(
        download_url,
        headers={"x-goog-api-key": API_KEY},
        timeout=300,
        stream=True,
    ) as response:  # Mở kết nối tải video dạng stream
        response.raise_for_status()  # Đảm bảo tải thành công
        with output_path.open("wb") as file_handle:  # Mở file đích ghi nhị phân
            for chunk in response.iter_content(chunk_size=1_048_576):  # Đọc từng khối dữ liệu
                if chunk:  # Bỏ qua khối rỗng
                    file_handle.write(chunk)  # Ghi dữ liệu vào file mp4

def extract_last_frame_base64(video_path: Path) -> str:
    """Trích xuất frame cuối cùng của video và trả về dưới dạng base64 PNG."""
    capture = cv2.VideoCapture(str(video_path))  # Mở video bằng OpenCV
    if not capture.isOpened():  # Kiểm tra video mở thành công
        raise RuntimeError(f"Không thể mở video {video_path}")
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))  # Đếm tổng số frame
    if total_frames == 0:  # Xử lý trường hợp video rỗng
        capture.release()  # Giải phóng tài nguyên trước khi báo lỗi
        raise RuntimeError(f"Video {video_path} không có frame")
    capture.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)  # Di chuyển tới frame cuối
    success, frame = capture.read()  # Đọc frame cuối cùng
    capture.release()  # Giải phóng tài nguyên sau khi sử dụng
    if not success:  # Kiểm tra đọc frame thành công
        raise RuntimeError(f"Không thể đọc frame cuối của {video_path}")
    success, png_bytes = cv2.imencode(".png", frame)  # Mã hóa frame thành ảnh PNG
    if not success:  # Kiểm tra mã hóa thành công
        raise RuntimeError("Không thể mã hóa frame cuối thành PNG")
    return base64.b64encode(png_bytes.tobytes()).decode("utf-8")  # Chuyển thành chuỗi base64

reference_frame_b64: str | None = None  # Biến lưu frame tham chiếu cho video kế tiếp

for index, scene in enumerate(SCENES, start=1):  # Lặp qua từng cảnh trong câu chuyện
    prompt = f"{BASE_PROMPT} {scene}"  # Ghép phong cách chung với mô tả cảnh cụ thể
    operation_name = start_video_job(prompt, reference_frame_b64)  # Khởi tạo tác vụ video
    print(f"Đã khởi tạo tác vụ: {operation_name}")  # Thông báo operation đang xử lý

    video_id = wait_for_video(operation_name)  # Chờ đến khi video sẵn sàng và lấy video_id
    output_path = OUTPUT_DIR / f"scene_{index:02d}.mp4"  # Định dạng tên file video theo thứ tự
    download_video(video_id, output_path)  # Tải video hoàn chỉnh về máy
    print(f"Đã tải video cảnh {index:02d} tại: {output_path}")  # Thông báo tiến trình tải

    reference_frame_b64 = extract_last_frame_base64(output_path)  # Cập nhật frame tham chiếu cho vòng lặp tiếp
    print(f"Đã cập nhật frame tham chiếu cho cảnh kế tiếp từ: {output_path}")  # Thông báo cập nhật frame
