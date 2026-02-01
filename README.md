# MedAgent - Trợ Lý Y Tế AI Thông Minh

Hệ thống chatbot y tế thông minh sử dụng **GPT-4o** và **RAG (Retrieval-Augmented Generation)** với khả năng:
- Tư vấn thông tin thuốc (RAG với Vector Database)
- Thống kê kho hàng và vẽ biểu đồ (SQLite Database + Visualization)
- Tìm kiếm web khi cần thiết
- Giao diện chat hiện đại với Gradio
## THiết kế hệ thống

<img width="1521" height="591" alt="image" src="https://github.com/user-attachments/assets/b4b146d7-2d2f-4ec2-8f35-27944e1c202c" />


## Tính Năng

### 1. Tư Vấn Thông Tin Thuốc (RAG)
- Tìm kiếm thông tin thuốc từ database vector (Qdrant)
- Sử dụng Google Generative AI Embeddings (text-embedding-004)
- Tự động đánh giá và cải thiện câu trả lời
- Hỗ trợ tìm kiếm web khi không tìm thấy trong database

### 2. Quản Lý Kho Hàng & Thống Kê
- Truy vấn SQL tự động từ câu hỏi tự nhiên
- Thống kê tồn kho, nhập hàng, doanh thu
- Vẽ biểu đồ đa dạng: bar, line, pie, horizontal_bar
- Phân tích theo nhà cung cấp, loại thuốc, thời gian

### 3. Router Thông Minh
- Tự động phân loại câu hỏi: y tế hoặc kho hàng
- Xử lý song song các query phức tạp
- Retry mechanism cho độ tin cậy cao

## Cài Đặt

### Yêu Cầu Hệ Thống
- Python 3.8+
- pip

### Bước 1: Clone Repository

```bash
git clone <repository-url>
cd MedAgent
```

### Bước 2: Cài Đặt Dependencies

```bash
pip install -r requirements.txt
```

### Bước 3: Cấu Hình API Keys

Tạo file `.env` trong thư mục gốc của project:

```env
# BẮT BUỘC - OpenAI GPT
OPENAI_API_KEY=sk-your-openai-api-key

# TÙY CHỌN - Google Gemini (cho embedding và backup LLM)
GOOGLE_API_KEY=your-google-api-key

# TÙY CHỌN - Qdrant Vector DB
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_api_key

# TÙY CHỌN - Cerebras (OpenAI-compatible models)
CEREBRAS_API_KEY=your_cerebras_api_key
```

**Lưu ý:** 
- `OPENAI_API_KEY` là bắt buộc cho chức năng chính
- `GOOGLE_API_KEY` cần thiết nếu sử dụng embedding model
- `QDRANT_URL` và `QDRANT_API_KEY` cần thiết cho RAG (có thể dùng local hoặc cloud)

### Bước 4: Khởi Tạo Database

```bash
cd sqlite-db/src
python main.py --reset --test
```

Lệnh này sẽ:
- Tạo database SQLite tại `sqlite-db/database/drug-warehouse.db`
- Import dữ liệu từ các file CSV
- Chạy test queries để kiểm tra

### Bước 5: (Tùy chọn) Embedding Dữ Liệu Thuốc

Nếu bạn muốn sử dụng RAG với dữ liệu thuốc:

```bash
cd query/core
python embed_to_qdrant.py
```

Script này sẽ:
- Đọc dữ liệu từ `drugs-data-main/data/details/`
- Embedding và upload lên Qdrant
- Tạo collection `embedding_data`

## Sử Dụng

### Chạy Chatbot

```bash
python chatbot_app.py
```

Truy cập giao diện tại: **http://localhost:7860**

### Ví Dụ Câu Hỏi

#### Câu Hỏi Y Tế (RAG):
- "Paracetamol dùng để làm gì?"
- "Thuốc nào điều trị cảm cúm?"
- "Liều dùng của Amoxicillin cho trẻ em?"

#### Câu Hỏi Kho Hàng (Database):
- "Vẽ biểu đồ doanh thu nhập hàng theo tháng"
- "Top 10 thuốc có giá trị nhập cao nhất"
- "Thống kê tồn kho theo nhà cung cấp"
- "Thuốc nào sắp hết hạn trong 6 tháng?"

## Cấu Trúc Project

```
MedAgent/
├── chatbot_app.py              # Giao diện Gradio chính
├── requirements.txt            # Dependencies
├── .env                        # Environment variables (KHÔNG commit)
├── .gitignore                  # Git ignore rules
│
├── query/                      # Core query processing
│   ├── config/
│   │   └── config.py           # Load environment variables
│   ├── core/                   # Core components
│   │   ├── llm.py              # LLM configuration (GPT, Gemini, etc.)
│   │   ├── embedding.py        # Embedding models
│   │   ├── rag.py              # Qdrant RAG client
│   │   ├── structure.py        # Data structures
│   │   └── embed_to_qdrant.py # Script embedding data
│   │
│   ├── router/                 # Router phân loại câu hỏi
│   │   └── router.py
│   │
│   ├── medical/                # Pipeline xử lý câu hỏi y tế
│   │   ├── medical_pipeline.py
│   │   ├── medical_rag.py
│   │   └── medical_search.py   # Web search integration
│   │
│   ├── store/                  # Pipeline database + chart
│   │   └── store_pipeline.py
│   │
│   ├── prompt_templates/       # Prompt templates
│   │   ├── base.py
│   │   ├── medical.py
│   │   ├── router.py
│   │   └── store.py
│   │
│   ├── router_pipeline.py      # Main router pipeline
│   ├── medical_query_pipeline.py
│   ├── split_query.py          # Split complex queries
│   ├── eval_answer.py          # Evaluate answer quality
│   └── final_answer.py         # Final answer generation
│
├── sqlite-db/                  # SQLite database
│   ├── database/
│   │   └── drug-warehouse.db   # Database file (gitignored)
│   ├── src/
│   │   ├── init.py             # Schema và import data
│   │   └── main.py             # Script khởi tạo DB
│   └── *.csv                   # Data files
│
├── drugs-data-main/            # Dữ liệu thuốc JSON (crawler)
│   └── data/
│       └── details/            # JSON files cho từng loại thuốc
│
├── eval/                       # Evaluation scripts
│   ├── eval_metrics.py
│   ├── native_eval.py
│   ├── rerank_eval.py
│   └── rerank_eval_update.py
│
└── data/                       # Evaluation datasets
    ├── comparison_eval_set_fixed.json
    └── hybrid_eval_set_openai.json
```

## Luồng Xử Lý

```
User Query
    |
    v
+-------------+
|   Router    | --> Phân loại: medical_knowledge / store_database
+-------------+
    |
    +---> medical_knowledge
    |         |
    |         v
    |    Split Query (nếu cần)
    |         |
    |         v
    |    RAG + Answer Generation
    |         |
    |         v
    |    Evaluate Answer
    |         |
    |         +---> Retry (nếu không đạt)
    |         |
    |         v
    |    Web Search (nếu cần)
    |         |
    |         v
    |    Final Answer
    |
    +---> store_database
              |
              v
         SQL Query Generation
              |
              v
         Execute Query
              |
              v
         Create Chart (nếu cần)
              |
              v
         Final Answer
```

## Models Hỗ Trợ

| Model | Provider | Type | Mặc Định |
|-------|----------|------|----------|
| gpt-4o | OpenAI | Chat | Có |
| gpt-4o-mini | OpenAI | Chat | |
| gpt-3.5-turbo | OpenAI | Chat | |
| gemini-2.5-flash-lite | Google | Chat | |
| llama-3.3-70b | Cerebras | Chat | |
| qwen-3-32b | Cerebras | Chat | |
| text-embedding-004 | Google | Embedding | Có |

## Cấu Hình Nâng Cao

### Thay Đổi Model Mặc Định

Trong `query/core/llm.py`, hàm `get_llm()` nhận tham số `type_model`:

```python
from query.core.llm import get_llm

# Sử dụng GPT-4o
llm = get_llm("gpt-4o")

# Sử dụng Gemini
llm = get_llm("gemini")
```

### Cấu Hình RAG

Trong `query/medical/medical_pipeline.py`:
- `similarity_threshold`: Ngưỡng similarity cho RAG (mặc định: 0.55)
- `max_attempts`: Số lần thử tối đa (mặc định: 3)

### Cấu Hình Database

Database schema được định nghĩa trong `sqlite-db/src/init.py`. Các bảng chính:
- `medicines`: Thông tin thuốc
- `inventory`: Tồn kho
- `imports`: Lịch sử nhập hàng
- `import_items`: Chi tiết nhập hàng
- `suppliers`: Nhà cung cấp

## Testing & Evaluation

### Chạy Evaluation

```bash
cd eval
python native_eval.py
```

### Test Database Queries

```bash
cd sqlite-db/src
python main.py --test
```

## API Endpoints

Hệ thống sử dụng các API sau:
- **OpenAI API**: GPT-4o cho sinh câu trả lời
- **Google Generative AI**: Embedding model (text-embedding-004)
- **Qdrant**: Vector database cho RAG
- **Cerebras API**: (Tùy chọn) OpenAI-compatible models

## Lưu Ý Bảo Mật

- **KHÔNG** commit file `.env` lên GitHub
- File `.env` đã được thêm vào `.gitignore`
- Tất cả API keys được load từ environment variables
- Database files (`.db`, `.sqlite3`) cũng được ignore

## Troubleshooting

### Lỗi: "QDRANT_URL không được tìm thấy"
- Kiểm tra file `.env` có `QDRANT_URL` và `QDRANT_API_KEY`
- Nếu dùng local Qdrant: `QDRANT_URL=http://localhost:6333`

### Lỗi: "StorePipeline không khởi tạo được"
- Chạy: `cd sqlite-db/src && python main.py --reset`
- Kiểm tra file `sqlite-db/database/drug-warehouse.db` có tồn tại

### Lỗi: "OPENAI_API_KEY không được tìm thấy"
- Tạo file `.env` trong thư mục gốc
- Thêm `OPENAI_API_KEY=sk-your-key`



**Lưu ý:** Đây là hệ thống tư vấn thông tin, không thay thế cho tư vấn y tế chuyên nghiệp. Luôn tham khảo ý kiến bác sĩ trước khi sử dụng thuốc.

# Project_ChatBot
