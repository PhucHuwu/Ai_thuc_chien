import json  # Lưu trạng thái tạm thời để resume khi cần
import os  # Đọc API key từ biến môi trường
import time  # Điều khiển khoảng cách giữa các lần poll
from pathlib import Path  # Quản lý đường dẫn file đầu ra và cache

import requests  # Thực hiện HTTP request tới gateway
from dotenv import load_dotenv  # Cho phép đọc API key từ file .env

load_dotenv()  # Nạp biến môi trường từ file .env nếu có

API_KEY = os.getenv("THUCCHIEN_API_KEY")  # API key dùng chung cho tất cả bước
if not API_KEY:
    raise RuntimeError("Thiếu biến THUCCHIEN_API_KEY trong môi trường hoặc file .env")
API_ROOT = "https://api.thucchien.ai/gemini/v1beta"  # Endpoint chính cho thao tác Veo
DOWNLOAD_ROOT = "https://api.thucchien.ai/gemini/download"  # Endpoint tải video hoàn tất
MODEL = "veo-3.0-fast-generate-001"  # Dùng model tốc độ cao làm phương án dự phòng
CACHE_FILE = Path("alternative_outputs/video_operation_cache.json")  # Cache lưu operation để resume

HEADERS = {
    "x-goog-api-key": API_KEY,
    "Content-Type": "application/json",
}


def start_job(prompt: str) -> str:
    """Khởi tạo job mới và lưu operation_name vào cache để có thể resume."""
    payload = {
        "instances": [
            {
                "prompt": prompt,
                "parameters": {
                    "aspectRatio": "16:9",
                    "resolution": "720p",
                    "personGeneration": "allow_all",
                },
            }
        ]
    }
    response = requests.post(
        f"{API_ROOT}/models/{MODEL}:predictLongRunning",
        headers=HEADERS,
        json=payload,
        timeout=90,
    )
    response.raise_for_status()
    operation_name = response.json()["name"]
    CACHE_FILE.parent.mkdir(exist_ok=True)
    CACHE_FILE.write_text(json.dumps({"operation": operation_name}))
    return operation_name


def resume_operation() -> str | None:
    """Đọc lại operation đã lưu nếu script bị dừng giữa chừng."""
    if CACHE_FILE.exists():
        data = json.loads(CACHE_FILE.read_text())
        return data.get("operation")
    return None


def wait_completion(operation_name: str, *, max_attempts: int = 60) -> str:
    """Poll trạng thái có giới hạn số lần thử để tránh loop vô hạn."""
    status_url = f"{API_ROOT}/{operation_name}"
    for attempt in range(1, max_attempts + 1):
        response = requests.get(status_url, headers={"x-goog-api-key": API_KEY}, timeout=60)
        response.raise_for_status()
        payload = response.json()
        if payload.get("done"):
            samples = payload["response"]["generateVideoResponse"]["generatedSamples"]
            uri = samples[0]["video"]["uri"]
            fragment = uri.split("/")[-1]
            return fragment.split(":")[0]
        print(f"Lần poll {attempt}/{max_attempts}: job chưa xong, chờ 10 giây...")
        time.sleep(10)
    raise TimeoutError("Hết số lần kiểm tra trạng thái, hãy thử lại sau")


def download(video_id: str, output_path: Path) -> None:
    """Tải video kết quả và xóa cache khi thành công."""
    download_url = f"{DOWNLOAD_ROOT}/v1beta/files/{video_id}:download?alt=media"
    with requests.get(
        download_url,
        headers={"x-goog-api-key": API_KEY},
        timeout=240,
        stream=True,
    ) as response:
        response.raise_for_status()
        with output_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1_048_576):
                if chunk:
                    handle.write(chunk)
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()  # Xóa cache vì job đã hoàn tất


if __name__ == "__main__":
    prompt_text = (
        "Một đoạn phim hoạt hình ngắn về cô bé quàng khăn đỏ đi qua khu rừng mùa thu"
    )
    output_path = Path("alternative_outputs/video_fast_model.mp4")
    output_path.parent.mkdir(exist_ok=True)

    operation = resume_operation() or start_job(prompt_text)
    print(f"Đang theo dõi operation: {operation}")
    video_id = wait_completion(operation)
    download(video_id, output_path)
    print(f"Đã lưu video fallback tại: {output_path}")
