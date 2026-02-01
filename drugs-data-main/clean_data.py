import json
import re
from pathlib import Path
from typing import Dict, Any
from html import unescape

def remove_css_block(text: str, start: int, end: int) -> str:
    """
    Loại bỏ một khối CSS từ vị trí start đến end
    """
    return text[:start] + text[end:]


def find_matching_brace(text: str, start_pos: int) -> int:
    """
    Tìm vị trí của closing brace tương ứng với opening brace tại start_pos
    Trả về -1 nếu không tìm thấy
    """
    if start_pos >= len(text) or text[start_pos] != '{':
        return -1
    
    depth = 0
    pos = start_pos
    
    while pos < len(text):
        if text[pos] == '{':
            depth += 1
        elif text[pos] == '}':
            depth -= 1
            if depth == 0:
                return pos
        pos += 1
    
    return -1


def clean_css_html(text: str) -> str:
    """
    Loại bỏ các đoạn CSS và HTML code khỏi text
    """
    if not isinstance(text, str):
        return text
    
    # Loại bỏ CSS selectors đơn lẻ (không có braces) - xử lý từng dòng
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        original_line = line
        stripped = line.strip()
        
        if not stripped:
            cleaned_lines.append(line)
            continue
        
        # Nếu dòng chỉ chứa CSS selectors (bắt đầu bằng . và chỉ có CSS), bỏ qua dòng này
        # Pattern: bắt đầu bằng .css-, .custom-, .btn-, .load-more-, .ant-tooltip-, .content-
        if re.match(r'^\.(?:css-|custom-|btn-|load-more-|ant-tooltip-|content-)[a-zA-Z0-9\-]+(?:\s+[\.#:a-zA-Z0-9\-\[\]\(\):]+)*$', stripped):
            continue
        
        # Loại bỏ CSS selectors khỏi dòng nhưng giữ lại nội dung khác
        # Pattern 1: .css-xxx hoặc .custom-xxx hoặc .btn-xxx... với các selectors liên quan
        cleaned_line = re.sub(r'\.(?:css-|custom-|btn-|load-more-|ant-tooltip-|content-)[a-zA-Z0-9\-]+(?:\s+[\.#:a-zA-Z0-9\-\[\]\(\):]+)*(?:\s|$)', '', line)
        
        # Pattern 2: Chuỗi CSS selectors dài được nối với nhau (như .css-xxx .content-list.css-xxx ...)
        cleaned_line = re.sub(r'\.(?:css-|custom-|btn-|load-more-|ant-tooltip-|content-)[a-zA-Z0-9\-]+\s+\.(?:css-|custom-|btn-|load-more-|ant-tooltip-|content-)[a-zA-Z0-9\-]+(?:\s+[\.#:a-zA-Z0-9\-\[\]\(\):]+)*', '', cleaned_line)
        
        # Pattern 3: CSS selectors với pseudo-classes và pseudo-elements (như :hover, :before, :first-of-type)
        cleaned_line = re.sub(r'\.(?:css-|custom-|btn-|load-more-|ant-tooltip-|content-)[a-zA-Z0-9\-]+(?:\s+[\.#:a-zA-Z0-9\-\[\]\(\):]+)*(?::[a-zA-Z0-9\-]+)+(?:\s|$)', '', cleaned_line)
        
        # Pattern 4: Các CSS selectors phức tạp với nhiều class được nối (như .css-xxx.content-list)
        cleaned_line = re.sub(r'\.(?:css-|custom-|btn-|load-more-|ant-tooltip-|content-)[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-]+(?:\s+[\.#:a-zA-Z0-9\-\[\]\(\):]+)*', '', cleaned_line)
        
        # Loại bỏ các khoảng trắng thừa sau khi xóa CSS
        cleaned_line = re.sub(r'\s+', ' ', cleaned_line)
        cleaned_line = cleaned_line.strip()
        
        # Nếu sau khi loại bỏ CSS, dòng vẫn còn nội dung, giữ lại
        if cleaned_line:
            cleaned_lines.append(cleaned_line)
    
    text = '\n'.join(cleaned_lines)
    
    # Loại bỏ CSS selectors và rules (xử lý nested braces) - các CSS có braces
    css_patterns_with_braces = [
        r'\.css-[a-zA-Z0-9\-]+\s*\{',  # .css-xxx{...}
        r'\.custom-[a-zA-Z0-9\-]+\s*\{',  # .custom-xxx{...}
        r'\.btn-[a-zA-Z0-9\-]+\s*\{',  # .btn-xxx{...}
        r'\.load-more-[a-zA-Z0-9\-]+\s*\{',  # .load-more-xxx{...}
        r'\.ant-tooltip-[a-zA-Z0-9\-]+\s*\{',  # .ant-tooltip-xxx{...}
    ]
    
    # Xử lý từng pattern có braces
    for selector_pattern in css_patterns_with_braces:
        while True:
            match = re.search(selector_pattern, text)
            if not match:
                break
            start = match.start()
            brace_start = match.end() - 1  # Vị trí của {
            brace_end = find_matching_brace(text, brace_start)
            if brace_end != -1:
                text = remove_css_block(text, start, brace_end + 1)
            else:
                # Không tìm thấy closing brace, chỉ xóa selector
                text = text[:start] + text[match.end():]
    
    # Loại bỏ @media queries
    while True:
        media_match = re.search(r'@media\s+(?:screen\s+and\s+)?\([^)]+\)\s*\{', text)
        if not media_match:
            break
        start = media_match.start()
        brace_start = media_match.end() - 1
        brace_end = find_matching_brace(text, brace_start)
        if brace_end != -1:
            text = remove_css_block(text, start, brace_end + 1)
        else:
            text = text[:start] + text[media_match.end():]
    
    # Loại bỏ các CSS rules còn sót lại (dạng {property: value;})
    # Chỉ loại bỏ nếu chứa các từ khóa CSS phổ biến
    css_keywords = ['margin', 'padding', 'display', 'width', 'height', 'position', 
                    'color', 'text-decoration', '-webkit-', 'align-items', 'flex',
                    'background', 'border', 'font', 'line-height', 'opacity']
    
    # Tìm và loại bỏ các khối CSS còn sót
    pos = 0
    while pos < len(text):
        if text[pos] == '{':
            brace_end = find_matching_brace(text, pos)
            if brace_end != -1:
                content = text[pos+1:brace_end]
                # Kiểm tra xem có phải CSS không
                if any(keyword in content for keyword in css_keywords):
                    text = remove_css_block(text, pos, brace_end + 1)
                    continue  # Không tăng pos vì đã xóa
        pos += 1
    
    # Loại bỏ HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Loại bỏ HTML entities và decode chúng
    text = unescape(text)
    
    # Loại bỏ các số đơn lẻ không có ý nghĩa (như "00046082\n0\n0\n")
    text = re.sub(r'^\d{8,}\s*\n\s*\d+\s*\n\s*\d+\s*\n', '', text, flags=re.MULTILINE)
    
    # Loại bỏ các dòng chỉ chứa số (nhưng giữ lại số có ý nghĩa như "150mg", "3x10")
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Giữ lại dòng nếu:
        # 1. Có chữ cái
        # 2. Có ký tự đặc biệt (như mg, ml, x, v.v.)
        # 3. Là số nhưng có ngữ cảnh (như "150mg", "3x10")
        if stripped:
            if any(c.isalpha() for c in stripped):
                cleaned_lines.append(line)
            elif re.search(r'\d+[a-zA-Z]+|\d+[x×]\d+|[a-zA-Z]+\d+', stripped):
                cleaned_lines.append(line)
            elif not re.match(r'^\s*\d+\s*$', stripped):
                cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    
    # Loại bỏ các khoảng trắng thừa (nhưng giữ lại newlines)
    text = re.sub(r'[ \t]+', ' ', text)  # Nhiều spaces thành 1 space
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Nhiều newlines thành 2
    text = re.sub(r' \n', '\n', text)  # Space trước newline
    text = re.sub(r'\n ', '\n', text)  # Space sau newline
    
    # Loại bỏ các ký tự điều khiển không hợp lệ
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    return text.strip()


def clean_json_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Làm sạch tất cả các trường trong JSON data
    """
    cleaned_data = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            cleaned_data[key] = clean_css_html(value)
        elif isinstance(value, dict):
            cleaned_data[key] = clean_json_data(value)
        elif isinstance(value, list):
            cleaned_data[key] = [
                clean_css_html(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            cleaned_data[key] = value
    
    return cleaned_data


def clean_json_file(file_path: Path) -> bool:
    """
    Làm sạch một file JSON
    Trả về True nếu thành công, False nếu có lỗi
    """
    try:
        # Đọc file JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Làm sạch dữ liệu
        cleaned_data = clean_json_data(data)
        
        # Ghi lại file đã được làm sạch
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=4)
        
        return True
    except json.JSONDecodeError as e:
        print(f"Lỗi đọc JSON file {file_path}: {e}")
        return False
    except Exception as e:
        print(f"Lỗi xử lý file {file_path}: {e}")
        return False


def clean_all_json_files(data_dir: Path):
    """
    Làm sạch tất cả các file JSON trong thư mục data/details
    """
    details_dir = data_dir / "details"
    
    if not details_dir.exists():
        print(f"Thư mục {details_dir} không tồn tại!")
        return
    
    # Đếm số file
    json_files = list(details_dir.rglob("*.json"))
    total_files = len(json_files)
    
    print(f"Tìm thấy {total_files} file JSON cần làm sạch...")
    print("Bắt đầu quá trình làm sạch dữ liệu...\n")
    
    success_count = 0
    error_count = 0
    
    # Xử lý từng file
    for idx, json_file in enumerate(json_files, 1):
        if clean_json_file(json_file):
            success_count += 1
            if idx % 100 == 0:
                print(f"Đã xử lý {idx}/{total_files} files...")
        else:
            error_count += 1
            print(f"Lỗi khi xử lý: {json_file}")
    
    print(f"\n{'='*50}")
    print(f"Hoàn thành!")
    print(f"Tổng số file: {total_files}")
    print(f"Thành công: {success_count}")
    print(f"Lỗi: {error_count}")
    print(f"{'='*50}")


if __name__ == "__main__":
    # Đường dẫn đến thư mục data
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    
    print("="*50)
    print("Script làm sạch dữ liệu thuốc")
    print("="*50)
    print(f"Thư mục dữ liệu: {data_dir}")
    print()
    
    # Xác nhận trước khi chạy
    response = input("Bạn có chắc chắn muốn làm sạch tất cả các file JSON? (yes/no): ")
    if response.lower() in ['yes', 'y', 'có', 'c']:
        clean_all_json_files(data_dir)
    else:
        print("Đã hủy bỏ.")

