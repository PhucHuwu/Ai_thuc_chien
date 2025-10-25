# Quy trình tạo sản phẩm nội dung bằng AI (Ảnh/Video)

## 1. Xác định mục tiêu và thông điệp
- Xác định rõ chủ đề, tông màu, cảm xúc và thông điệp chính của loạt ảnh hoặc video.
- Thu thập tư liệu tham khảo (hình ảnh, từ khóa, câu chuyện) để đảm bảo prompt đầy đủ ngữ cảnh.

## 2. Chuẩn bị môi trường và dữ liệu hỗ trợ
- Thiết lập biến môi trường `THUCCHIEN_API_KEY` và cài thư viện cần thiết (`pip install openai requests opencv-python`).
- Chuẩn bị thư mục lưu trữ đầu ra (`demo_outputs/`) và, nếu cần, thư mục tài nguyên đầu vào (`demo_assets/`).

## 3. Thiết kế prompt nền tảng
- Xây dựng prompt nền (style prompt) mô tả phong cách xuyên suốt: ngôn ngữ mô tả, bối cảnh, màu sắc, góc máy, chất liệu.
- Chuẩn bị danh sách prompt con mô tả từng cảnh/ảnh đơn lẻ theo chủ đề. Ví dụ: 10 cảnh kể lại truyện Cô Bé Quàng Khăn Đỏ.

## 4. Lựa chọn kỹ thuật sinh nội dung
- **Sinh ảnh từ prompt**: sử dụng `demo_code/image_from_prompt.py` với model `imagen-4` để tạo ảnh hoàn toàn mới.
- **Sinh ảnh từ ảnh mẫu**: dùng `demo_code/image_from_image.py` và endpoint Gemini kèm ảnh tham chiếu để giữ phong cách.
- **Sinh video từ prompt**: tham khảo `demo_code/video_from_prompt.py` để chạy quy trình 3 bước Veo.
- **Sinh video chuỗi liên mạch**: dùng `demo_code/video_story_sequence.py` kết hợp frame cuối của video trước cho cảnh tiếp theo.
- **Chuyển văn bản thành giọng nói**: áp dụng `demo_code/text_to_speech.py` nếu cần lồng tiếng cho video.

## 5. Tự động hóa luồng xử lý
- Gói các script trong một pipeline (ví dụ Python CLI hoặc workflow) để chạy lần lượt: sinh ảnh → sinh video → tạo voice-over.
- Sử dụng lịch sử prompt/ảnh đầu ra làm đầu vào cho bước kế tiếp giúp duy trì sự đồng nhất.
- Lưu metadata (prompt, video_id, thời gian tạo) để phục vụ tái tạo hoặc rollback.

## 6. Kiểm tra và tinh chỉnh
- Đánh giá từng sản phẩm đầu ra so với yêu cầu: bố cục, ánh sáng, nhân vật, mạch truyện.
- Điều chỉnh `temperature`, `aspect_ratio`, `resolution`, hoặc prompt chi tiết nếu chất lượng chưa đạt.
- Với video, kiểm tra chuyển động mượt mà, độ dài, tính liên tục giữa các clip.

## 7. Hậu kỳ và tích hợp
- Áp dụng chỉnh sửa thủ công (nếu cần) bằng công cụ đồ họa/video truyền thống.
- Kết hợp ảnh/video và giọng đọc thành sản phẩm hoàn chỉnh (ví dụ ghép video + audio bằng ffmpeg hoặc công cụ dựng phim).

## 8. Triển khai và lưu trữ
- Tổ chức thư mục đầu ra theo dự án/chủ đề để dễ dàng quản lý.
- Tạo bản sao lưu và chia sẻ qua hệ thống quản lý phiên bản hoặc kho lưu trữ đám mây.
- Ghi chú kết quả vào tài liệu dự án để làm nền tảng cho các chiến dịch nội dung AI tiếp theo.
