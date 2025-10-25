# Tóm tắt Hướng dẫn API AI Thực Chiến

## Thông tin cốt lõi
- Gateway cung cấp một endpoint hợp nhất `https://api.thucchien.ai`, tương thích giao diện OpenAI thông qua LiteLLM proxy.
- Một API key duy nhất dùng cho mọi yêu cầu; chuyển mô hình chỉ cần đổi trường `model`.
- Bốn nhóm chức năng chính: sinh văn bản, sinh hình ảnh, sinh video Veo 3 (bất đồng bộ), và chuyển văn bản thành giọng nói.

## Xác thực & cấu hình
- Header tiêu chuẩn: `Authorization: Bearer <API_KEY>`; thiếu hoặc sai sẽ trả về lỗi `401 Unauthorized`.
- Riêng quy trình Veo 3 phải dùng header `x-goog-api-key: <API_KEY>`.
- Khi dùng SDK OpenAI, cấu hình `base_url="https://api.thucchien.ai"` cùng API key gateway.

```python
from openai import OpenAI

client = OpenAI(api_key="<API_KEY>", base_url="https://api.thucchien.ai")
```

## Tham số quan trọng
- Đầu vào: dùng `prompt` (tác vụ đơn) hoặc `messages` (đối thoại nhiều lượt).
- Kiểm soát đầu ra: `temperature`, `top_p`, `max_tokens`, `n` (số kết quả), `response_format` (ví dụ `b64_json` cho ảnh/audio).
- Cấu trúc phản hồi thống nhất: mảng `choices` cho văn bản, mảng `data` cho tài sản nhị phân (ảnh, audio, video).

## Sinh văn bản
- Mô hình tiêu biểu: `gemini-2.5-pro`, `gemini-2.5-flash`.
- Endpoint: `POST /v1/chat/completions`.
- Ví dụ tối thiểu:

```python
resp = client.chat.completions.create(
    model="gemini-2.5-pro",
    messages=[{"role": "user", "content": "Giải thích API Gateway là gì."}],
)
print(resp.choices[0].message.content)
```

## Sinh hình ảnh
- Phương thức chuẩn: `POST /v1/images/generations`, trả về ảnh base64; model hỗ trợ `imagen-4`.
- Phương thức trò chuyện: `POST /v1/chat/completions` với `gemini-2.5-flash-image-preview`, dữ liệu ảnh nằm trong `choices[0].message.images` (base64).
- Luôn giải mã base64 và lưu file cục bộ; thêm biến ngẫu nhiên vào prompt để tránh cache.

## Sinh video với Veo 3
- Quy trình 3 bước bất đồng bộ:
  1. `POST https://api.thucchien.ai/gemini/v1beta/models/veo-3.0-generate-preview:predictLongRunning` kèm `x-goog-api-key` và prompt.
  2. Poll `GET .../operations/{operation_id}` cho tới khi nhận `"done": true`.
  3. Trích `video_id` từ URI trả về và tải qua `https://api.thucchien.ai/gemini/download/v1beta/files/{video_id}:download?alt=media`.
- Thời lượng, tỷ lệ khung hình, chất lượng tùy chỉnh theo tham số của Google Veo.

## Text-to-Speech (TTS)
- Endpoint: `POST /v1/audio/speech` (có thể hiển thị dưới `/audio/speech` tùy tài liệu SDK).
- Mô hình: `gemini-2.5-flash-preview-tts`, `gemini-2.5-pro-preview-tts`.
- Tham số bắt buộc: `model`, `input` (văn bản), `voice`. Có thể bổ sung tốc độ, định dạng, đa giọng theo hướng dẫn Google Gemini TTS.

## Tài liệu tham khảo cần thiết
- LiteLLM: cấu hình proxy, caching, fallback, virtual keys.
- Google Gemini/Vertex AI: tham số chi tiết cho Gemini, Imagen, Veo, và Gemini TTS.
