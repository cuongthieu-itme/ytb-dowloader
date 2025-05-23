# YouTube Downloader

Ứng dụng web đơn giản cho phép tải video và âm thanh từ YouTube sử dụng Django và yt-dlp.

## Tính năng

- Tải video (MP4) hoặc âm thanh (MP3) từ YouTube
- Xem trước thông tin video trước khi tải xuống
- Tùy chọn chất lượng (cao, trung bình, thấp)
- Hỗ trợ xử lý video dài (>= 30 phút)
- Giao diện đơn giản, dễ sử dụng

## Yêu cầu hệ thống

### Sử dụng trực tiếp
- Python 3.10 hoặc cao hơn
- Django 4.2 hoặc cao hơn
- yt-dlp (phiên bản mới nhất)

### Sử dụng Docker
- Docker
- Docker Compose

## Cài đặt và chạy ứng dụng

### Phương pháp 1: Sử dụng môi trường Python

1. Tạo và kích hoạt môi trường ảo Python:

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. Cài đặt các gói phụ thuộc:

```bash
pip install -r requirements.txt
```

3. Chạy server:

```bash
python manage.py runserver
```

Sau khi chạy lệnh trên, mở trình duyệt và truy cập địa chỉ: http://127.0.0.1:8000/

### Phương pháp 2: Sử dụng Docker

1. Xây dựng và khởi chạy container:

```bash
docker-compose up -d --build
```

2. Truy cập ứng dụng tại địa chỉ: http://localhost:8000/

3. Xem logs của ứng dụng:

```bash
docker-compose logs -f
```

4. Dừng và xóa container:

```bash
docker-compose down
```

## Cách sử dụng

1. Nhập URL video YouTube vào ô nhập liệu
2. Chọn định dạng tải xuống (MP4 hoặc MP3)
3. Tùy chọn chọn chất lượng video/âm thanh
4. Nhấn "Xem trước" để xem thông tin video
5. Sau khi xác nhận thông tin, nhấn "Tải xuống" để bắt đầu quá trình tải

## Lưu ý

- Ứng dụng này sử dụng thư viện yt-dlp để tải nội dung từ YouTube. Đôi khi, do YouTube thay đổi cấu trúc trang web, yt-dlp có thể gặp lỗi. Trong trường hợp này, bạn nên cập nhật yt-dlp lên phiên bản mới nhất bằng lệnh:

```bash
pip install -U yt-dlp
```

- Việc tải xuống nội dung có bản quyền mà không có sự cho phép có thể vi phạm điều khoản dịch vụ của YouTube và pháp luật về bản quyền. Ứng dụng này chỉ nên được sử dụng cho các mục đích cá nhân, phi thương mại và với nội dung được phép.

## Cấu trúc dự án

```
ytb-downloader/
├── downloader/              # Ứng dụng Django chính
│   ├── static/              # File tĩnh (CSS, JS)
│   ├── templates/           # Template HTML
│   ├── forms.py             # Form xử lý nhập liệu
│   ├── urls.py              # Cấu hình URL
│   └── views.py             # Logic xử lý request
├── ytb_downloader/          # Cấu hình Django project
├── Dockerfile               # Cấu hình Docker
├── docker-compose.yml       # Cấu hình Docker Compose
├── docker-entrypoint.sh     # Script khởi động Docker
├── .dockerignore            # Danh sách file bỏ qua khi build Docker
├── requirements.txt         # Danh sách thư viện cần thiết
└── README.md                # Tài liệu hướng dẫn
```

## Cấu hình Docker

Dự án này sử dụng Docker để dễ dàng triển khai và chạy ứng dụng mà không cần cài đặt các phụ thuộc trực tiếp trên máy chủ.

### Các file Docker

- **Dockerfile**: Định nghĩa cách xây dựng image Docker cho ứng dụng
- **docker-compose.yml**: Cấu hình dịch vụ, mạng và volume cho ứng dụng
- **docker-entrypoint.sh**: Script chạy khi container khởi động
- **.dockerignore**: Danh sách các file và thư mục bỏ qua khi build image

### Môi trường

Bạn có thể cấu hình các biến môi trường trong file `.env` (tạo từ `.env.example`) để thay đổi cấu hình ứng dụng khi chạy với Docker.
