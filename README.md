Dưới đây là hướng dẫn chi tiết để giúp bạn và các đồng nghiệp cài đặt và chạy ứng dụng Flask của bạn, bao gồm cả việc sử dụng `SECRET_KEY` và các bước cài đặt từ đầu.

---

# Hướng Dẫn Cài Đặt và Chạy Ứng Dụng Flask

## 2. **Tạo Virtual Environment**

Tạo một môi trường ảo để cài đặt các thư viện Python cần thiết mà không làm ảnh hưởng đến các dự án khác:

```bash
python3 -m venv venv
```

Kích hoạt môi trường ảo:

- Trên **macOS/Linux**:

```bash
source venv/bin/activate
```

- Trên **Windows**:

```bash
venv\Scripts\activate
```

## 3. **Cài Đặt Dependencies**

Cài đặt các thư viện từ file `requirements.txt`:

```bash
pip install -r requirements.txt
```

**Lưu ý**: Nếu không có file `requirements.txt`, bạn có thể tự tạo nó bằng lệnh:

```bash
pip freeze > requirements.txt
```

## 4. **Cài Đặt Tesseract OCR**

Để xử lý hình ảnh và nhận diện văn bản, bạn cần cài đặt **Tesseract OCR**. Đây là phần mềm nhận dạng văn bản từ hình ảnh.

- **macOS**: Cài đặt qua Homebrew:

```bash
brew install tesseract
```

- **Windows**: Tải và cài đặt từ [tesseract-ocr](https://github.com/tesseract-ocr/tesseract).

Sau khi cài đặt, xác minh đường dẫn của Tesseract:

```bash
which tesseract
```

Đoạn đường dẫn trả về sẽ được sử dụng trong mã nguồn của bạn. Thông thường, nó sẽ giống như:

- Trên **macOS**: `/opt/homebrew/bin/tesseract`
- Trên **Windows**: `C:\Program Files\Tesseract-OCR\tesseract.exe`

## 5. **Cấu Hình Flask Secret Key**

Ứng dụng Flask của bạn sử dụng một `SECRET_KEY` để bảo vệ session và cookie. Để tạo một `SECRET_KEY` mới, bạn có thể sử dụng Python như sau trong terminal:

```python
import secrets

secret_key = secrets.token_hex(16)
print(secret_key)
```

Cập nhật `SECRET_KEY` trong file cấu hình Flask của bạn. Ví dụ, trong `__init__.py` hoặc file cấu hình chính:

```python
import secrets

app.config['SECRET_KEY'] = secrets.token_hex(16)  # Hoặc bạn có thể sử dụng giá trị SECRET_KEY đã sinh ở bước trước
```

Để bảo mật hơn, bạn có thể lưu `SECRET_KEY` vào biến môi trường thay vì hard-code vào mã nguồn.

Cách cấu hình biến môi trường:

- **macOS/Linux**: Cài đặt biến môi trường trong terminal:

```bash
export FLASK_SECRET_KEY='your_generated_secret_key'
```

- **Windows**: Sử dụng `set` trong Command Prompt:

```bash
set FLASK_SECRET_KEY=your_generated_secret_key
```

Sau đó, trong mã nguồn, bạn có thể truy xuất biến môi trường này:

```python
import os

app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(16))
```

## 6. **Chạy Ứng Dụng Flask**

Cuối cùng, để chạy ứng dụng Flask, bạn sử dụng lệnh sau trong terminal:

```bash
python3 run.py
```

Ứng dụng sẽ chạy ở chế độ **debug** nếu bạn đã cấu hình đúng như vậy trong `run.py` hoặc file cấu hình của Flask.

## 7. **Các Lệnh Thông Dụng**

- **Khởi động lại môi trường ảo**:

```bash
deactivate  # Để thoát môi trường ảo
source venv/bin/activate  # Kích hoạt lại môi trường ảo
```

- **Cài đặt lại tất cả các thư viện** (nếu cần):

```bash
pip install -r requirements.txt
```

---

### Lưu ý quan trọng:

- **Đảm bảo rằng Tesseract được cài đặt đúng** và có đường dẫn chính xác trong mã nguồn của bạn.
- **Không chia sẻ `SECRET_KEY` trên GitHub** hoặc các public repositories.
- **Nếu sử dụng các API bên ngoài** (như Google Translate, Google Text-to-Speech), bạn cần kiểm tra các credentials và cài đặt chúng.

---
