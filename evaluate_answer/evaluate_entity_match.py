"""
Script đánh giá câu trả lời sử dụng Entity Match Score

Phương pháp: Trích xuất các thực thể y khoa từ câu trả lời Ground Truth và LLM,
sau đó tính điểm dựa trên mức độ khớp giữa các thực thể.

Các loại thực thể được trích xuất:
- Tên thuốc (drug names)
- Liều lượng (dosages): mg, ml, viên, giọt
- Tần suất (frequency): lần/ngày, ngày X lần
- Đường dùng (route): uống, nhỏ mắt, xịt mũi
- Chỉ định (indications): các triệu chứng/bệnh
- Chống chỉ định (contraindications)
"""

import json
import os
import re
from typing import List, Dict, Set, Tuple
from tqdm import tqdm
from difflib import SequenceMatcher


class MedicalEntityExtractor:
    """Trích xuất các thực thể y khoa từ văn bản tiếng Việt"""
    
    def __init__(self):
        # Patterns cho các loại entity
        self.dosage_patterns = [
            r'\d+(?:[.,]\d+)?\s*(?:mg|ml|g|mcg|µg|gram|miligram|mililit)',
            r'\d+(?:[.,]\d+)?\s*(?:viên|giọt|gói|ống|chai|lọ)',
            r'\d+\s*-\s*\d+\s*(?:viên|giọt|mg|ml|g)',
            r'\d+(?:/|\s+trên\s+)\d+\s*(?:mg|ml)',
        ]
        
        self.frequency_patterns = [
            r'\d+\s*(?:lần|lần\/ngày|lần mỗi ngày|lần/ngày)',
            r'ngày\s*\d+\s*lần',
            r'mỗi\s*\d+\s*(?:giờ|tiếng)',
            r'\d+\s*giờ\s*(?:một|1)\s*lần',
            r'(?:sáng|trưa|tối|chiều)(?:\s*và\s*(?:sáng|trưa|tối|chiều))*',
        ]
        
        self.route_patterns = [
            r'(?:uống|nhỏ mắt|nhỏ mũi|xịt mũi|tiêm|bôi|tra mắt|ngậm|hít)',
            r'(?:đường uống|đường tiêm|qua da|tại chỗ)',
            r'dùng\s+(?:ngoài|trong)',
        ]
        
        # Các từ khóa chỉ định/triệu chứng phổ biến
        self.indication_keywords = [
            'viêm', 'nhiễm khuẩn', 'nhiễm trùng', 'đau', 'sốt', 'ho', 'cảm',
            'dị ứng', 'ngứa', 'sổ mũi', 'nghẹt mũi', 'viêm xoang', 'viêm họng',
            'viêm phế quản', 'hen', 'suyễn', 'tiêu chảy', 'táo bón', 'buồn nôn',
            'đau đầu', 'chóng mặt', 'mỏi mắt', 'đỏ mắt', 'khô mắt', 'viêm kết mạc',
            'viêm giác mạc', 'tăng nhãn áp', 'glaucom', 'đục thủy tinh thể',
            'huyết áp', 'tiểu đường', 'đái tháo đường', 'cholesterol',
            'tim mạch', 'loạn nhịp', 'phù', 'viêm khớp', 'đau lưng',
            'ung thư', 'u bướu', 'loét', 'trào ngược', 'viêm dạ dày',
            'hạ sốt', 'giảm đau', 'kháng viêm', 'kháng sinh', 'kháng histamin',
        ]
        
        # Các từ khóa chống chỉ định
        self.contraindication_keywords = [
            'mang thai', 'có thai', 'cho con bú', 'trẻ em', 'trẻ dưới',
            'người cao tuổi', 'suy gan', 'suy thận', 'quá mẫn', 'dị ứng với',
            'không dùng', 'chống chỉ định', 'thận trọng',
        ]
        
        # Pattern cho tên thuốc (thường viết hoa hoặc có đặc điểm riêng)
        self.drug_name_patterns = [
            r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+\d+(?:mg|ml)?)?',  # Paracetamol 500mg
            r'(?:Thuốc|Viên|Siro|Dung dịch|Hỗn dịch|Gel|Kem|Mỡ)\s+[^\.,]+',
        ]
    
    def extract_entities(self, text: str) -> Dict[str, Set[str]]:
        """
        Trích xuất tất cả các loại entity từ văn bản
        
        Returns:
            Dict chứa các set entity theo loại
        """
        entities = {
            'dosages': set(),
            'frequencies': set(),
            'routes': set(),
            'indications': set(),
            'contraindications': set(),
            'drug_names': set(),
        }
        
        text_lower = text.lower()
        
        # Trích xuất liều lượng
        for pattern in self.dosage_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                entities['dosages'].add(self._normalize(match))
        
        # Trích xuất tần suất
        for pattern in self.frequency_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                entities['frequencies'].add(self._normalize(match))
        
        # Trích xuất đường dùng
        for pattern in self.route_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                entities['routes'].add(self._normalize(match))
        
        # Trích xuất chỉ định/triệu chứng
        for keyword in self.indication_keywords:
            if keyword in text_lower:
                # Tìm ngữ cảnh xung quanh từ khóa
                pattern = rf'\b[\w\s]{{0,20}}{re.escape(keyword)}[\w\s]{{0,20}}\b'
                matches = re.findall(pattern, text_lower)
                if matches:
                    entities['indications'].add(keyword)
        
        # Trích xuất chống chỉ định
        for keyword in self.contraindication_keywords:
            if keyword in text_lower:
                entities['contraindications'].add(keyword)
        
        # Trích xuất tên thuốc (đơn giản hóa)
        # Tìm các cụm từ bắt đầu bằng chữ hoa
        drug_matches = re.findall(r'[A-Z][a-zA-Z0-9\-]+(?:\s+[A-Z][a-zA-Z0-9\-]+)*', text)
        for match in drug_matches:
            if len(match) > 2:  # Bỏ qua các từ quá ngắn
                entities['drug_names'].add(match.lower())
        
        return entities
    
    def _normalize(self, text: str) -> str:
        """Chuẩn hóa text: lowercase, bỏ khoảng trắng thừa"""
        return ' '.join(text.lower().split())


def fuzzy_match(str1: str, str2: str, threshold: float = 0.8) -> bool:
    """So sánh 2 chuỗi với fuzzy matching"""
    ratio = SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    return ratio >= threshold


def calculate_entity_match_score(
    entities_gt: Dict[str, Set[str]],
    entities_llm: Dict[str, Set[str]],
    fuzzy_threshold: float = 0.8
) -> Dict[str, float]:
    """
    Tính điểm Entity Match giữa Ground Truth và LLM
    
    Returns:
        Dict chứa precision, recall, f1 cho từng loại entity và tổng thể
    """
    results = {}
    total_tp = 0
    total_gt = 0
    total_llm = 0
    
    for entity_type in entities_gt.keys():
        gt_set = entities_gt[entity_type]
        llm_set = entities_llm[entity_type]
        
        if len(gt_set) == 0 and len(llm_set) == 0:
            results[entity_type] = {'precision': 1.0, 'recall': 1.0, 'f1': 1.0}
            continue
        
        # Tính số lượng match với fuzzy matching
        true_positives = 0
        for llm_ent in llm_set:
            for gt_ent in gt_set:
                if fuzzy_match(llm_ent, gt_ent, fuzzy_threshold):
                    true_positives += 1
                    break
        
        precision = true_positives / len(llm_set) if len(llm_set) > 0 else 0
        recall = true_positives / len(gt_set) if len(gt_set) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        results[entity_type] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'gt_count': len(gt_set),
            'llm_count': len(llm_set),
            'matched': true_positives
        }
        
        total_tp += true_positives
        total_gt += len(gt_set)
        total_llm += len(llm_set)
    
    # Tính điểm tổng thể
    overall_precision = total_tp / total_llm if total_llm > 0 else 0
    overall_recall = total_tp / total_gt if total_gt > 0 else 0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) \
                 if (overall_precision + overall_recall) > 0 else 0
    
    results['overall'] = {
        'precision': overall_precision,
        'recall': overall_recall,
        'f1': overall_f1,
        'total_gt': total_gt,
        'total_llm': total_llm,
        'total_matched': total_tp
    }
    
    return results


def load_json_file(file_path: str) -> List[Dict]:
    """Đọc file JSON"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data: Dict, file_path: str):
    """Lưu dữ liệu vào file JSON"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def evaluate_answers_with_entity_match(
    predict_data: List[Dict],
    gt_data: List[Dict],
    extractor: MedicalEntityExtractor
) -> List[Dict]:
    """
    Đánh giá câu trả lời sử dụng Entity Match Score
    """
    results = []
    
    # Tạo dict để tra cứu nhanh ground truth theo question
    gt_dict = {item['question']: item['answer'] for item in gt_data}
    
    for pred_item in tqdm(predict_data, desc="Đánh giá Entity Match"):
        query = pred_item['query']
        answer_llm = pred_item['answer']
        
        # Tìm ground truth tương ứng
        if query not in gt_dict:
            print(f"Warning: Không tìm thấy ground truth cho query: {query[:100]}...")
            continue
        
        answer_gt = gt_dict[query]
        
        # Trích xuất entities
        entities_gt = extractor.extract_entities(answer_gt)
        entities_llm = extractor.extract_entities(answer_llm)
        
        # Tính điểm
        scores = calculate_entity_match_score(entities_gt, entities_llm)
        
        result = {
            'query': query,
            'answer_ground_truth': answer_gt,
            'answer_llm_predict': answer_llm,
            'entities_gt': {k: list(v) for k, v in entities_gt.items()},
            'entities_llm': {k: list(v) for k, v in entities_llm.items()},
            'entity_scores': scores,
            'overall_f1': scores['overall']['f1'],
            'overall_precision': scores['overall']['precision'],
            'overall_recall': scores['overall']['recall']
        }
        
        results.append(result)
    
    return results


def main():
    # Đường dẫn thư mục
    base_dir = os.path.dirname(os.path.abspath(__file__))
    predict_dir = os.path.join(base_dir, 'predict')
    gt_dir = os.path.join(base_dir, 'gt')
    output_dir = os.path.join(base_dir, 'results_entity_match')
    
    # Tạo thư mục output nếu chưa có
    os.makedirs(output_dir, exist_ok=True)
    
    # Danh sách các file cần đánh giá
    data_files = [
        'about_1_drug.json',
        'about_2_drug.json',
        'comprehensive_1_drug.json',
        'listing.json',
        'symptom.json'
    ]
    
    # Khởi tạo entity extractor
    print("Khởi tạo Medical Entity Extractor...")
    extractor = MedicalEntityExtractor()
    
    # Lưu tổng hợp kết quả
    summary = {}
    
    # Đánh giá từng file
    for data_file in data_files:
        print(f"\n{'='*60}")
        print(f"Đang xử lý file: {data_file}")
        print(f"{'='*60}")
        
        predict_path = os.path.join(predict_dir, data_file)
        gt_path = os.path.join(gt_dir, data_file)
        output_path = os.path.join(output_dir, f'entity_match_{data_file}')
        
        # Kiểm tra file tồn tại
        if not os.path.exists(predict_path):
            print(f"Lỗi: Không tìm thấy file predict: {predict_path}")
            continue
        if not os.path.exists(gt_path):
            print(f"Lỗi: Không tìm thấy file ground truth: {gt_path}")
            continue
        
        # Load dữ liệu
        predict_data = load_json_file(predict_path)
        gt_data = load_json_file(gt_path)
        
        print(f"Số lượng câu hỏi trong predict: {len(predict_data)}")
        print(f"Số lượng câu hỏi trong ground truth: {len(gt_data)}")
        
        # Đánh giá
        results = evaluate_answers_with_entity_match(predict_data, gt_data, extractor)
        
        # Tính thống kê
        if results:
            f1_scores = [r['overall_f1'] for r in results]
            precision_scores = [r['overall_precision'] for r in results]
            recall_scores = [r['overall_recall'] for r in results]
            
            avg_f1 = sum(f1_scores) / len(f1_scores)
            avg_precision = sum(precision_scores) / len(precision_scores)
            avg_recall = sum(recall_scores) / len(recall_scores)
            
            print(f"\nKết quả Entity Match cho {data_file}:")
            print(f"  - Số lượng câu hỏi đánh giá: {len(results)}")
            print(f"  - F1 trung bình: {avg_f1:.4f}")
            print(f"  - Precision trung bình: {avg_precision:.4f}")
            print(f"  - Recall trung bình: {avg_recall:.4f}")
            
            # Thêm thống kê theo từng loại entity
            entity_types = ['dosages', 'frequencies', 'routes', 'indications', 'contraindications', 'drug_names']
            print(f"\n  Điểm theo loại entity:")
            for etype in entity_types:
                type_f1s = [r['entity_scores'][etype]['f1'] for r in results]
                avg_type_f1 = sum(type_f1s) / len(type_f1s)
                print(f"    - {etype}: F1 = {avg_type_f1:.4f}")
            
            # Lưu thống kê
            statistics = {
                'total_questions': len(results),
                'average_f1': avg_f1,
                'average_precision': avg_precision,
                'average_recall': avg_recall,
                'by_entity_type': {}
            }
            
            for etype in entity_types:
                type_f1s = [r['entity_scores'][etype]['f1'] for r in results]
                type_prec = [r['entity_scores'][etype]['precision'] for r in results]
                type_rec = [r['entity_scores'][etype]['recall'] for r in results]
                statistics['by_entity_type'][etype] = {
                    'avg_f1': sum(type_f1s) / len(type_f1s),
                    'avg_precision': sum(type_prec) / len(type_prec),
                    'avg_recall': sum(type_rec) / len(type_rec)
                }
            
            output_data = {
                'statistics': statistics,
                'results': results
            }
            
            summary[data_file] = statistics
        else:
            output_data = {
                'statistics': {},
                'results': []
            }
        
        # Lưu kết quả
        save_json_file(output_data, output_path)
        print(f"Đã lưu kết quả vào: {output_path}")
    
    # Lưu tổng hợp
    summary_path = os.path.join(output_dir, 'summary.json')
    save_json_file(summary, summary_path)
    
    print(f"\n{'='*60}")
    print("Hoàn thành đánh giá Entity Match tất cả các file!")
    print(f"Kết quả được lưu trong thư mục: {output_dir}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
