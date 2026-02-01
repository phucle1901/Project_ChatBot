import os
import re
from utils import crawl_drug_info

# Định nghĩa đường dẫn
URL_DIR = "./data/urls/"
DETAILS_DIR = "./data/details/"

# Tạo thư mục details nếu chưa tồn tại
os.makedirs(DETAILS_DIR, exist_ok=True)

print("Bat dau crawl thong tin chi tiet thuoc...")

try:
    # Kiểm tra thư mục urls có tồn tại không
    if not os.path.exists(URL_DIR):
        print(f"[ERROR] Thu muc {URL_DIR} khong ton tai!")
        print("Vui long chay 'python get_url.py' truoc de thu thap danh sach URL.")
        exit(1)
    
    # Lấy danh sách các file trong thư mục urls
    list_catalog = os.listdir(URL_DIR)
    
    # Lọc chỉ lấy file .txt
    txt_files = [f for f in list_catalog if f.endswith('.txt')]
    
    if not txt_files:
        print(f"[ERROR] Khong tim thay file .txt nao trong thu muc {URL_DIR}")
        print("Vui long chay 'python get_url.py' truoc de thu thap danh sach URL.")
        exit(1)
    
    print(f"Tim thay {len(txt_files)} danh muc de xu ly\n")
    
    list_catalog = txt_files
    
    # Xử lý từng danh mục
    for topic in list_catalog:
        if not topic.endswith('.txt'):  # chỉ xử lý file .txt
            continue
            
        # Xử lý tên thư mục
        name = os.path.splitext(topic)[0]
        name = re.sub(r'[^0-9a-zA-ZÀ-ỹ]+', '-', name)
        name = name.strip('-')
        
        # Tạo thư mục cho danh mục
        category_dir = os.path.join(DETAILS_DIR, name)
        os.makedirs(category_dir, exist_ok=True)
        
        print(f"Dang xu ly danh muc: {name}")
        
        # Đọc và xử lý từng URL
        with open(file=os.path.join(URL_DIR, topic), mode="r", encoding="utf-8") as file:
            list_urls = file.readlines()
            total_urls = len(list_urls)
            
            for index, url in enumerate(list_urls, 1):
                url = url.strip()  # Loại bỏ ký tự xuống dòng
                if url:  # Chỉ xử lý URL không rỗng
                    print(f"  [{index}/{total_urls}] Đang xử lý: {url}")
                    try:
                        crawl_drug_info(url=url, dest_dir=name)
                    except Exception as e:
                        print(f"    [ERROR] Loi khi xu ly URL {url}: {str(e)}")
    
    print("\nHoan tat crawl thong tin chi tiet thuoc!")

except Exception as e:
    print(f"[ERROR] Loi: {str(e)}")


