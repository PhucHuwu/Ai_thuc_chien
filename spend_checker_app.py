import json  # Dùng để format JSON trả về giúp hiển thị dễ đọc
import os  # Lấy API key từ biến môi trường
import sys  # Truy cập argv và thoát ứng dụng PyQt

import requests  # Gửi request kiểm tra chi tiêu tới gateway
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from dotenv import load_dotenv  # Đọc biến môi trường từ file .env nếu có

load_dotenv()  # Nạp biến môi trường từ file .env để tự động điền API key

API_URL = "https://api.thucchien.ai/key/info"  # Endpoint kiểm tra chi tiêu theo tài liệu


class SpendCheckerWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Spend Checker - AI Thực Chiến")
        self.resize(480, 360)

        self.api_key_input = QLineEdit()  # Cho phép dán API key khác khi cần
        env_key = os.environ.get("THUCCHIEN_API_KEY", "")
        if env_key:
            self.api_key_input.setText(env_key)  # Tự động điền key từ biến môi trường
        self.api_key_input.setEchoMode(QLineEdit.PasswordEchoOnEdit)

        self.status_label = QLabel("Nhấn CHECK để xem thông tin chi tiêu")

        self.output_view = QTextEdit()
        self.output_view.setReadOnly(True)

        self.check_button = QPushButton("CHECK")
        self.check_button.clicked.connect(self.on_check_clicked)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("API Key"))
        layout.addWidget(self.api_key_input)
        layout.addWidget(self.check_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.output_view)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def on_check_clicked(self) -> None:
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Thiếu API key", "Vui lòng nhập API key hợp lệ.")
            return

        self.status_label.setText("Đang kiểm tra chi tiêu...")
        self.check_button.setEnabled(False)
        QApplication.processEvents()  # Cập nhật giao diện trước khi gọi API

        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "accept": "application/json",
            }
            response = requests.get(API_URL, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            info = data.get("info", {})
            summary = (
                f"Alias: {info.get('key_alias', 'n/a')}\n"
                f"Spend: {info.get('spend', 'n/a')} USD\n"
                f"Max budget: {info.get('max_budget', 'n/a')}\n"
                f"RPM limit: {info.get('rpm_limit', 'n/a')}\n"
                f"TPM limit: {info.get('tpm_limit', 'n/a')}\n"
            )
            self.status_label.setText(summary)
            pretty_json = json.dumps(data, indent=2, ensure_ascii=False)
            self.output_view.setPlainText(pretty_json)
        except requests.RequestException as exc:
            QMessageBox.critical(self, "Lỗi gọi API", str(exc))
            self.status_label.setText("Không thể lấy thông tin chi tiêu")
        finally:
            self.check_button.setEnabled(True)


def main() -> None:
    app = QApplication(sys.argv)
    window = SpendCheckerWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
