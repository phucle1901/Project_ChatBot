"""
Script đánh giá câu trả lời sử dụng mô hình BAAI/bge-reranker-v2-m3

Mô hình reranker sẽ tính điểm similarity giữa:
- Query + Answer Ground Truth
- Query + Answer LLM Predict

Sau đó so sánh điểm để đánh giá chất lượng câu trả lời của LLM.
"""

import json
import os
from typing import List, Dict, Any
from tqdm import tqdm

# Import model reranker
from FlagEmbedding import FlagReranker


def load_json_file(file_path: str) -> List[Dict]:
    """Đọc file JSON và trả về danh sách dict"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data: List[Dict], file_path: str):
    """Lưu dữ liệu vào file JSON"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def evaluate_answers(
    predict_data: List[Dict],
    gt_data: List[Dict],
    reranker: FlagReranker
) -> List[Dict]:
    """
    Đánh giá câu trả lời bằng mô hình reranker
    
    Args:
        predict_data: Danh sách câu trả lời từ LLM (có key 'query', 'answer')
        gt_data: Danh sách câu trả lời ground truth (có key 'question', 'answer')
        reranker: Mô hình FlagReranker
    
    Returns:
        Danh sách kết quả đánh giá
    """
    results = []
    
    # Tạo dict để tra cứu nhanh ground truth theo question
    gt_dict = {item['question']: item['answer'] for item in gt_data}
    
    for pred_item in tqdm(predict_data, desc="Đánh giá câu trả lời"):
        query = pred_item['query']
        answer_llm = pred_item['answer']
        
        # Tìm ground truth tương ứng
        if query not in gt_dict:
            print(f"Warning: Không tìm thấy ground truth cho query: {query[:100]}...")
            continue
        
        answer_gt = gt_dict[query]
        
        # Tính điểm reranker
        # Reranker tính điểm relevance giữa query và passage
        # Ta cần so sánh answer_gt với answer_llm dựa trên query
        
        # Cách tiếp cận: Tính điểm giữa (answer_gt, answer_llm)
        # Score cao = hai câu trả lời tương đồng nhau
        pairs = [[answer_gt, answer_llm]]
        
        scores = reranker.compute_score(pairs, normalize=True)
        
        # Nếu chỉ có 1 cặp, scores là số, không phải list
        if isinstance(scores, float):
            score = scores
        else:
            score = scores[0]
        
        result = {
            'query': query,
            'answer_ground_truth': answer_gt,
            'answer_llm_predict': answer_llm,
            'score': float(score)
        }
        
        results.append(result)
    
    return results


def main():
    # Đường dẫn thư mục
    base_dir = os.path.dirname(os.path.abspath(__file__))
    predict_dir = os.path.join(base_dir, 'predict')
    gt_dir = os.path.join(base_dir, 'gt')
    output_dir = os.path.join(base_dir, 'results')
    
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
    
    # Load mô hình reranker
    print("Đang tải mô hình BAAI/bge-reranker-v2-m3...")
    reranker = FlagReranker(
        'BAAI/bge-reranker-v2-m3',
        use_fp16=True  # Sử dụng FP16 để tiết kiệm bộ nhớ
    )
    print("Đã tải mô hình thành công!")
    
    # Đánh giá từng file
    for data_file in data_files:
        print(f"\n{'='*60}")
        print(f"Đang xử lý file: {data_file}")
        print(f"{'='*60}")
        
        predict_path = os.path.join(predict_dir, data_file)
        gt_path = os.path.join(gt_dir, data_file)
        output_path = os.path.join(output_dir, f'eval_{data_file}')
        
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
        results = evaluate_answers(predict_data, gt_data, reranker)
        
        # Tính thống kê
        if results:
            scores = [r['score'] for r in results]
            avg_score = sum(scores) / len(scores)
            min_score = min(scores)
            max_score = max(scores)
            
            print(f"\nKết quả đánh giá cho {data_file}:")
            print(f"  - Số lượng câu hỏi đánh giá: {len(results)}")
            print(f"  - Điểm trung bình: {avg_score:.4f}")
            print(f"  - Điểm thấp nhất: {min_score:.4f}")
            print(f"  - Điểm cao nhất: {max_score:.4f}")
            
            # Thêm thống kê vào kết quả
            output_data = {
                'statistics': {
                    'total_questions': len(results),
                    'average_score': avg_score,
                    'min_score': min_score,
                    'max_score': max_score
                },
                'results': results
            }
        else:
            output_data = {
                'statistics': {
                    'total_questions': 0,
                    'average_score': 0,
                    'min_score': 0,
                    'max_score': 0
                },
                'results': []
            }
        
        # Lưu kết quả
        save_json_file(output_data, output_path)
        print(f"Đã lưu kết quả vào: {output_path}")
    
    print(f"\n{'='*60}")
    print("Hoàn thành đánh giá tất cả các file!")
    print(f"Kết quả được lưu trong thư mục: {output_dir}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
