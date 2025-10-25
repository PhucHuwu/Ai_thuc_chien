import base64
import json
import os
import time
from pathlib import Path
from typing import Any

import cv2
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("THUCCHIEN_API_KEY")
if not API_KEY:
    raise RuntimeError("Thiếu biến THUCCHIEN_API_KEY trong môi trường hoặc file .env")
API_ROOT = "https://api.thucchien.ai/gemini/v1beta"
DOWNLOAD_ROOT = "https://api.thucchien.ai/gemini/download"
MODEL = "veo-3.0-generate-001"
STATE_FILE = Path("alternative_outputs/video_story_state.json")
OUTPUT_DIR = Path("alternative_outputs/red_riding_video_stateful")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_PROMPT = (
    "Phong cách hoạt hình 3D ấm áp, ánh sáng vàng nhạt, nhân vật cô bé quàng khăn đỏ luôn xuất hiện."
)
SCENES = [
    "Cảnh 1: cô bé rời khỏi nhà với chiếc khăn đỏ và giỏ bánh.",
    "Cảnh 2: cô bé trò chuyện với chú thỏ trên lối mòn.",
    "Cảnh 3: sói quan sát từ phía sau bụi cây.",
    "Cảnh 4: cô bé gõ cửa nhà bà ngoại.",
    "Cảnh 5: sói cải trang làm bà ngoại trong phòng ngủ.",
    "Cảnh 6: cô bé nhận ra điều bất thường.",
    "Cảnh 7: thợ săn phá cửa xông vào.",
    "Cảnh 8: mọi người ôm nhau sau khi được cứu.",
    "Cảnh 9: cả nhóm ăn bánh trong căn phòng ấm cúng.",
    "Cảnh 10: cô bé rời đi với bài học kinh nghiệm.",
]

HEADERS = {
    "x-goog-api-key": API_KEY,
    "Content-Type": "application/json",
}


def load_state() -> dict[str, Any]:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"next_index": 0, "reference_frame": None}


def save_state(state: dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def start_job(prompt: str, reference_frame: str | None) -> str:
    instance = {
        "prompt": prompt,
        "parameters": {
            "aspectRatio": "16:9",
            "resolution": "720p",
            "personGeneration": "allow_all",
        },
    }
    if reference_frame is not None:
        instance["image"] = {
            "bytesBase64Encoded": reference_frame,
            "mimeType": "image/png",
        }
    payload = {"instances": [instance]}
    response = requests.post(
        f"{API_ROOT}/models/{MODEL}:predictLongRunning", headers=HEADERS, json=payload, timeout=120
    )
    response.raise_for_status()
    return response.json()["name"]


def wait_for_video(operation_name: str) -> str:
    status_url = f"{API_ROOT}/{operation_name}"
    while True:
        response = requests.get(status_url, headers={"x-goog-api-key": API_KEY}, timeout=60)
        response.raise_for_status()
        data = response.json()
        if data.get("done"):
            samples = data["response"]["generateVideoResponse"]["generatedSamples"]
            uri = samples[0]["video"]["uri"]
            fragment = uri.split("/")[-1]
            return fragment.split(":")[0]
        print("Chưa hoàn tất, chờ 15 giây rồi poll lại...")
        time.sleep(15)


def download_video(video_id: str, output_path: Path) -> None:
    download_url = f"{DOWNLOAD_ROOT}/v1beta/files/{video_id}:download?alt=media"
    with requests.get(
        download_url, headers={"x-goog-api-key": API_KEY}, timeout=300, stream=True
    ) as response:
        response.raise_for_status()
        with output_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1_048_576):
                if chunk:
                    handle.write(chunk)


def extract_last_frame(video_path: Path) -> str:
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Không thể mở video {video_path}")
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if total == 0:
        capture.release()
        raise RuntimeError(f"Video {video_path} không chứa frame")
    capture.set(cv2.CAP_PROP_POS_FRAMES, total - 1)
    success, frame = capture.read()
    capture.release()
    if not success:
        raise RuntimeError(f"Không đọc được frame cuối của {video_path}")
    success, buffer = cv2.imencode(".png", frame)
    if not success:
        raise RuntimeError("Không mã hóa được frame cuối sang PNG")
    return base64.b64encode(buffer.tobytes()).decode("utf-8")


def main() -> None:
    state = load_state()
    for index in range(state["next_index"], len(SCENES)):
        prompt = f"{BASE_PROMPT} {SCENES[index]}"
        print(f"Bắt đầu cảnh {index + 1}: {prompt}")
        operation = start_job(prompt, state.get("reference_frame"))
        print(f"Operation: {operation}")
        video_id = wait_for_video(operation)
        output_path = OUTPUT_DIR / f"scene_{index + 1:02d}.mp4"
        download_video(video_id, output_path)
        print(f"Đã lưu {output_path}")
        reference_frame = extract_last_frame(output_path)
        state = {"next_index": index + 1, "reference_frame": reference_frame}
        save_state(state)
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    print("Hoàn tất toàn bộ chuỗi video đồng bộ")


if __name__ == "__main__":
    main()
