import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("THUCCHIEN_API_KEY")
if not API_KEY:
    raise RuntimeError("Thiếu biến THUCCHIEN_API_KEY trong môi trường hoặc file .env")
API_URL = "https://api.thucchien.ai/audio/speech"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def synthesize(script: str, *, voice: str = "Zephyr", retries: int = 2) -> bytes:
    payload = {
        "model": "gemini-2.5-pro-preview-tts",
        "input": script,
        "voice": voice,
        "format": "wav",
    }
    for attempt in range(retries + 1):
        response = requests.post(API_URL, headers=HEADERS, json=payload, stream=True, timeout=90)
        if response.ok:
            return b"".join(response.iter_content(chunk_size=8192))
        print(f"Tạo giọng nói thất bại (attempt {attempt + 1}), đợi 3s rồi thử lại")
        time.sleep(3)
    response.raise_for_status()


if __name__ == "__main__":
    script = (
        "Đây là phương án dự phòng chuyển văn bản thành giọng nói sử dụng model pro preview."
    )
    output_path = Path("alternative_outputs/tts_fallback.wav")
    output_path.parent.mkdir(exist_ok=True)
    audio_bytes = synthesize(script)
    output_path.write_bytes(audio_bytes)
    print(f"Đã lưu file âm thanh fallback tại: {output_path}")
