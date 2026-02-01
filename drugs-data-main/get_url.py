import os
import re
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


# ==============================
#  Hàm hỗ trợ
# ==============================

def scroll_to_bottom(driver, pause=2):
    """Cuộn xuống để trang load hết sản phẩm"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def sanitize_name(name: str) -> str:
    """Làm sạch tên thư mục để không bị lỗi Windows"""
    name = name.split("\n")[0]  # chỉ lấy dòng đầu tiên
    name = re.sub(r'[<>:"/\\|?*\n\r]+', '', name)  # bỏ ký tự cấm
    return name.strip()


def get_category_links(driver):
    """Lấy tất cả danh mục trên trang /thuoc"""
    driver.get("https://nhathuoclongchau.com.vn/thuoc")
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.mt-6.container-lite")))
    container = driver.find_element(By.CSS_SELECTOR, "div.mt-6.container-lite")
    cats = container.find_elements(By.CSS_SELECTOR, "div.grid a[href^='/thuoc/']")
    category_links = [a.get_attribute("href") for a in cats]
    category_names = [sanitize_name(a.text) for a in cats]
    return list(zip(category_names, category_links))


def get_product_links(driver, category_url):
    """Lấy danh sách tất cả link thuốc trong một danh mục, bao gồm cả sản phẩm ẩn"""
    driver.get(category_url)
    
    try:
        # chờ phần container chính chứa danh sách thuốc xuất hiện
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#category-page__products-section > div.px-4.pt-3.md\\:px-0.md\\:pt-0 > div")
            )
        )
    except TimeoutException:
        print(f"[WARN] Khong tim thay container san pham o {category_url}")
        return []

    # Kiểm tra và click nút "xem thêm" cho đến khi không còn
    while True:
        try:
            # Tìm nút "xem thêm"
            load_more_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#category-page__products-section > div.px-4.pt-3.md\\:px-0.md\\:pt-0 > button")
                )
            )
            
            # Kiểm tra nếu nút có chứa text "xem thêm" (không phân biệt hoa thường)
            button_text = load_more_button.text.lower()
            if "xem thêm" in button_text:
                # Scroll đến cuối trang trước để tránh các phần tử che khuất
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)  # đợi scroll hoàn tất
                
                try:
                    # Thử click bằng JavaScript
                    driver.execute_script("arguments[0].click();", load_more_button)
                except Exception:
                    try:
                        # Nếu không được thì thử click bình thường
                        load_more_button.click()
                    except Exception as e:
                        print(f"[WARN] Khong the click nut xem them: {str(e)}")
                        break
                
                print("Click nut xem them va doi load san pham...")
                time.sleep(2)  # đợi sản phẩm mới load
                
                # Đợi container cập nhật và sản phẩm mới xuất hiện
                try:
                    WebDriverWait(driver, 10).until(
                        lambda d: len(d.find_elements(By.CSS_SELECTOR, "#category-page__products-section > div.px-4.pt-3.md\\:px-0.md\\:pt-0 > div a[href*='/thuoc/']")) > 0
                    )
                except TimeoutException:
                    print("[WARN] Khong thay san pham moi sau khi click")
                    break
            else:
                # Nếu nút không có chữ "xem thêm" thì thoát vòng lặp
                break
                
        except TimeoutException:
            # Không tìm thấy nút "xem thêm" nữa -> đã load hết
            break

    # Sau khi load hết, lấy container chính
    container = driver.find_element(
        By.CSS_SELECTOR,
        "#category-page__products-section > div.px-4.pt-3.md\\:px-0.md\\:pt-0 > div"
    )

    # Lấy tất cả thẻ a trong container
    product_links = [
        a.get_attribute("href")
        for a in container.find_elements(By.TAG_NAME, "a")
        if a.get_attribute("href") and "/thuoc/" in a.get_attribute("href")
    ]

    # Loại bỏ trùng lặp và thông báo số lượng
    unique_links = list(set(product_links))
    print(f"Da load tat ca san pham: {len(unique_links)} thuoc")
    return unique_links


def extract_drug_info(html_content):
    """Trích xuất thông tin thuốc từ HTML content"""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Tìm tất cả các section chứa thông tin
    info = {}
    
    # Lấy tên thuốc
    product_name = soup.select_one('.product-name')
    if product_name:
        info['ten_thuoc'] = product_name.text.strip()
    
    # Lấy thông tin chi tiết
    detail_sections = soup.select('.detail-content .content-item')
    for section in detail_sections:
        # Lấy tiêu đề section
        title = section.select_one('.title')
        if title:
            title_text = title.text.strip().lower()
            # Lấy nội dung section
            content = section.select_one('.content')
            if content:
                info[title_text] = content.text.strip()
    
    return info

def get_drug_data(driver, drug_url, max_retries=3):
    """Lấy toàn bộ mã HTML của 1 trang thuốc"""
    for attempt in range(max_retries):
        try:
            driver.get(drug_url)
            # Lấy toàn bộ mã HTML
            html_content = driver.page_source
            if html_content:
                return {
                    "url": drug_url,
                    "html": html_content
                }
            else:
                if attempt < max_retries - 1:
                    print(f"[WARN] Khong lay duoc HTML o {drug_url}, thu lai lan {attempt + 2}/{max_retries}")
                    time.sleep(2)
                continue
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"[WARN] Loi khi crawl {drug_url}, thu lai lan {attempt + 2}/{max_retries}: {str(e)}")
                time.sleep(2)
            else:
                print(f"[ERROR] Khong the crawl {drug_url} sau {max_retries} lan thu: {str(e)}")
                return None
    
    return None


# ==============================
#  Hàm chính
# ==============================

def crawl_all():
    # Tạo options cho Chrome
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-gpu')  # Tắt GPU để tránh một số lỗi
    chrome_options.add_argument('--window-size=1920,1080')  # Đặt kích thước cửa sổ
    
    driver = webdriver.Chrome(options=chrome_options)
    os.makedirs("data", exist_ok=True)

    # 1. Lay danh muc
    categories = get_category_links(driver)
    print(f"Co {len(categories)} danh muc.")

    for cat_name, cat_link in categories:
        print(f"\nDang crawl danh muc: {cat_name} -> {cat_link}")

        # 2. Lay danh sach thuoc trong danh muc
        drug_links = get_product_links(driver, cat_link)
        print(f"→ Tìm thấy {len(drug_links)} thuốc.")

        # 3. Luu links vao file txt
        file_name = sanitize_name(cat_name) + ".txt"
        file_path = os.path.join("data", file_name)
        
        # Lưu từng link vào file, mỗi link một dòng
        with open(file_path, "w", encoding="utf-8") as f:
            for link in drug_links:
                f.write(link + "\n")

    driver.quit()
    print("\nCrawl hoan tat!")


if __name__ == "__main__":
    crawl_all()
