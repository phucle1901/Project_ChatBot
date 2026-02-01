# Drug Crawler Project

## Mục đích

Dự án này giúp tự động thu thập (crawl) thông tin thuốc từ website nhathuoclongchau.com.vn, lưu lại danh sách link và trích xuất chi tiết từng loại thuốc.

## Cấu trúc thư mục

```
.
├── main.py              # Script chính để crawl và trích xuất thông tin thuốc
├── get_url.py           # Script hỗ trợ lấy link danh mục hoặc link thuốc
├── utils.py             # Các hàm hỗ trợ crawl/trích xuất
├── data/
│   ├── urls/            # Chứa các file .txt, mỗi file là danh sách link thuốc theo danh mục
│   └── details/         # Chứa các thư mục con, mỗi thư mục là 1 danh mục, bên trong là file chi tiết từng thuốc
└── README.md            # Hướng dẫn sử dụng
```

## Hướng dẫn sử dụng

### 1. Cài đặt môi trường

- Tạo virtual environment (nếu chưa có):
  ```
  python -m venv .venv
  ```
- Kích hoạt môi trường ảo:
  - Windows:
    ```
    .venv\Scripts\activate
    ```
  - Linux/Mac:
    ```
    source .venv/bin/activate
    ```
- Cài đặt các thư viện cần thiết:
  ```
  pip install selenium requests parsel beautifulsoup4
  ```


### 2. Crawl danh mục và lấy link thuốc

Chạy script:
```
python get_url.py
```
- Kết quả: Tạo các file .txt trong `data/urls/`, mỗi file chứa danh sách link thuốc của một danh mục.

### 3. Crawl chi tiết từng thuốc

Chạy script:
```
python main.py
```
- Kết quả: Tạo các thư mục con trong `data/details/`, mỗi thư mục chứa file chi tiết từng thuốc (dạng JSON hoặc TXT).

### 4. Tuỳ chỉnh
- Có thể chỉnh sửa các hàm trong `utils.py` để thay đổi cách trích xuất thông tin.
- Có thể chạy riêng lẻ từng phần nếu muốn crawl lại một danh mục hoặc một thuốc cụ thể.

## Lưu ý
- Website có thể thay đổi giao diện, cần cập nhật lại các selector trong code nếu bị lỗi.
- Nên sử dụng User-Agent giả lập trình duyệt thật khi crawl.
- Không nên crawl quá nhanh để tránh bị chặn IP.

## Liên hệ
- Tác giả: [Tên của bạn]
- Email: [Email của bạn]
