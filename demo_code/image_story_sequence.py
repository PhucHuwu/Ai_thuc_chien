import base64  # Dùng để giải mã ảnh trả về và tái sử dụng ảnh trước trong chuỗi
import os  # Lấy API key từ biến môi trường tránh hard-code
from pathlib import Path  # Quản lý đường dẫn thư mục lưu ảnh đầu ra
import requests  # Gửi yêu cầu HTTP trực tiếp tới endpoint Gemini

from dotenv import load_dotenv  # Nạp biến môi trường từ file .env nếu có

load_dotenv()  # Đảm bảo có thể lấy API key từ file .env

API_KEY = os.getenv("THUCCHIEN_API_KEY")  # Đọc API key của gateway để xác thực
if not API_KEY:
    raise RuntimeError("Thiếu biến THUCCHIEN_API_KEY trong môi trường hoặc file .env")
MODEL = "gemini-2.5-flash-image-preview"  # Chọn model hỗ trợ chế độ image-to-image giữ phong cách
API_URL = (
    f"https://api.thucchien.ai/gemini/v1beta/models/{MODEL}:generateContent"
)  # Endpoint sinh/sửa ảnh qua gateway AI Thực Chiến

OUTPUT_DIR = Path("demo_outputs/red_riding_hood")  # Thư mục chứa bộ ảnh kết quả
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)  # Tạo thư mục nếu chưa tồn tại

BASE_STYLE = (
    "Minh họa truyện cổ tích phong cách tranh màu nước, ánh sáng ấm áp, nhân vật chính là cô bé quàng khăn đỏ."
)  # Định nghĩa phong cách nền tảng để giữ sự đồng nhất giữa các ảnh

SCENES = [
    "Cô bé quàng khăn đỏ đi vào khu rừng rậm rạp với giỏ bánh trên tay.",
    "Cô bé gặp chú chim xanh đang hót trên cành cây cổ thụ.",
    "Một lối mòn dẫn cô bé đến ngôi nhà của bà ngoại nằm sâu trong rừng.",
    "Sói xám lấp ló phía sau thân cây, quan sát cô bé từ xa.",
    "Cô bé gõ cửa nhà bà ngoại và mỉm cười chờ đợi.",
    "Sói đội mũ ngủ và giả làm bà ngoại trên giường.",
    "Cô bé nghi ngờ khi thấy đôi mắt to khác thường của bà.",
    "Thợ săn xuất hiện ở cửa với chiếc rìu trên vai.",
    "Thợ săn giải cứu cô bé và bà ngoại khỏi bụng sói.",
    "Cả ba cùng ngồi uống trà trong căn nhà ấm áp sau cuộc phiêu lưu.",
]  # Mô tả chi tiết từng cảnh để tạo 10 bức minh họa liên kết nội dung

HEADERS = {
    "x-goog-api-key": API_KEY,  # Gemini yêu cầu truyền key qua header x-goog-api-key
    "Content-Type": "application/json",  # Thiết lập kiểu dữ liệu JSON cho payload
}  # Bộ header cố định cho mọi yêu cầu trong quy trình

previous_image_b64 = None  # Biến lưu ảnh trước đó ở dạng base64 để tái sử dụng cho cảnh kế tiếp

for index, scene in enumerate(SCENES, start=1):  # Lặp qua từng cảnh cùng chỉ số bắt đầu từ 1
    parts = [{"text": f"{BASE_STYLE} {scene}"}]  # Thêm phần prompt văn bản kết hợp phong cách và cảnh cụ thể
    if previous_image_b64 is not None:  # Nếu đã có ảnh trước đó thì chèn thêm làm tham chiếu hình ảnh
        parts.append(
            {
                "inlineData": {
                    "mimeType": "image/png",  # Khai báo đúng định dạng ảnh đã lưu
                    "data": previous_image_b64,  # Truyền dữ liệu ảnh base64 của cảnh trước
                }
            }
        )  # Đính kèm ảnh trước vào cùng request để model giữ phong cách nhất quán

    payload = {
        "contents": [{"parts": parts}],  # Gói các phần prompt và dữ liệu ảnh vào cấu trúc contents
        "generationConfig": {
            "temperature": 0.3,  # Giảm độ ngẫu nhiên để phong cách ổn định
            "aspectRatio": "3:2",  # Chọn tỷ lệ khung hình đồng nhất giữa các cảnh
        },  # Thiết lập cấu hình sinh ảnh bổ sung
    }  # Payload hoàn chỉnh gửi đến endpoint

    response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=120)  # Gửi request sinh ảnh cho cảnh hiện tại
    response.raise_for_status()  # Kiểm tra và dừng sớm nếu gặp lỗi HTTP

    data = response.json()  # Phân tích phản hồi JSON trả về từ API
    candidates = data.get("candidates", [])  # Lấy danh sách ứng viên ảnh sinh ra
    if not candidates:  # Nếu không có ảnh trả về thì báo lỗi rõ ràng
        raise RuntimeError(f"API không trả về ảnh cho cảnh thứ {index}, hãy kiểm tra lại prompt")

    inline_data = candidates[0]["content"]["parts"][0]["inlineData"]  # Lấy dữ liệu ảnh từ ứng viên đầu tiên
    current_image_b64 = inline_data["data"]  # Trích xuất chuỗi base64 đại diện cho ảnh sinh ra

    output_path = OUTPUT_DIR / f"scene_{index:02d}.png"  # Xác định đường dẫn file ảnh theo thứ tự cảnh
    output_path.write_bytes(base64.b64decode(current_image_b64))  # Giải mã base64 và lưu ảnh ra đĩa

    previous_image_b64 = current_image_b64  # Cập nhật ảnh trước đó để dùng cho vòng lặp tiếp theo

    print(f"Đã tạo ảnh cảnh {index:02d} tại: {output_path}")  # Thông báo tiến trình tạo ảnh cho người dùng
