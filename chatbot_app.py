"""
Giao diện chatbot y tế sử dụng Gradio với thiết kế chuyên nghiệp
Hỗ trợ GPT và hiển thị biểu đồ thống kê từ database
"""
import gradio as gr
import sys
import os
from typing import Tuple, List, Union
import logging
from dotenv import load_dotenv
import base64
import io
import numpy as np

# Load .env file từ thư mục MedAgent
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=env_path)

# Thêm thư mục hiện tại vào path để import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from query.router_pipeline import RouterPipeline

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Khởi tạo router pipeline (tích hợp RAG và Database Search)
pipeline = RouterPipeline(max_retries=3)

# Lưu lịch sử chat
chat_history = []


def numpy_to_base64(img_array: np.ndarray) -> str:
    """
    Chuyển đổi numpy array (image) sang base64 string để hiển thị trong Gradio.
    
    Args:
        img_array: Numpy array của hình ảnh
        
    Returns:
        str: Base64 encoded string của hình ảnh
    """
    try:
        from PIL import Image
        
        # Đảm bảo array là uint8
        if img_array.dtype != np.uint8:
            img_array = img_array.astype(np.uint8)
        
        # Chuyển BGR sang RGB nếu cần (OpenCV format)
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            # Check if it's BGR (OpenCV) format
            img_array = img_array[:, :, ::-1]
        
        # Tạo PIL Image
        pil_image = Image.fromarray(img_array)
        
        # Encode sang base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        logger.error(f"Error converting image to base64: {e}")
        return None


def format_answer(answer_text: str, sources: List[str], confidence: float) -> str:
    """
    Format câu trả lời.
    
    Args:
        answer_text: Nội dung câu trả lời
        sources: Danh sách nguồn tham khảo (không sử dụng)
        confidence: Độ tin cậy (không sử dụng)
        
    Returns:
        str: Câu trả lời đã được format
    """
    return answer_text


def chat_with_bot(message: str, history: List[Tuple[str, Union[str, tuple]]]) -> Tuple[str, List[Tuple[str, Union[str, tuple]]]]:
    """
    Xử lý tin nhắn từ người dùng và trả về phản hồi từ chatbot.
    Hỗ trợ hiển thị cả text và hình ảnh (biểu đồ thống kê).
    
    Args:
        message: Tin nhắn từ người dùng
        history: Lịch sử chat (list of tuples (user_message, bot_response))
        
    Returns:
        Tuple[str, List]: (empty string để clear input, updated history)
    """
    if not message or not message.strip():
        return "", history
    
    try:
        # Xử lý câu hỏi qua router pipeline
        logger.info(f"User query: {message}")
        result = pipeline.process_query_unified(message)
        
        # Kiểm tra xem có phải là kết quả có hình ảnh không
        is_image = result.get("is_image", False)
        image_data = result.get("image", None)
        
        if is_image and image_data is not None:
            # Nếu có biểu đồ, hiển thị cả text và hình ảnh
            logger.info("Response includes chart/image")
            
            # Chuyển đổi image array sang base64 để hiển thị
            if isinstance(image_data, np.ndarray):
                img_base64 = numpy_to_base64(image_data)
                if img_base64:
                    # Tạo HTML để hiển thị hình ảnh
                    answer_text = result.get("answer", "Biểu đồ thống kê:")
                    bot_response = f"{answer_text}\n\n![Biểu đồ thống kê]({img_base64})"
                else:
                    bot_response = result.get("answer", "Không thể hiển thị biểu đồ.")
            elif isinstance(image_data, bytes):
                # Nếu là raw bytes
                img_base64 = base64.b64encode(image_data).decode()
                answer_text = result.get("answer", "Biểu đồ thống kê:")
                bot_response = f"{answer_text}\n\n![Biểu đồ thống kê](data:image/png;base64,{img_base64})"
            else:
                bot_response = result.get("answer", "Đã xử lý yêu cầu.")
        else:
            # Format câu trả lời thông thường (text only)
            bot_response = format_answer(
                result["answer"],
                result.get("sources", []),
                result.get("confidence", 0.0)
            )
        
        # Cập nhật lịch sử
        history.append((message, bot_response))
        chat_history.extend(history)
        
        logger.info(f"Bot response generated with confidence: {result.get('confidence', 0.0):.2f}, is_image: {is_image}")
        
        return "", history
        
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        error_message = f"Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi của bạn. Vui lòng thử lại.\n\nLỗi: {str(e)}"
        history.append((message, error_message))
        return "", history




def clear_chat() -> Tuple[str, List]:
    """
    Xóa lịch sử chat.
    
    Returns:
        Tuple[str, List]: (empty string, empty list)
    """
    chat_history.clear()
    return "", []


def use_example(example: str) -> str:
    """Sử dụng câu hỏi mẫu."""
    return example


# Custom CSS chuyên nghiệp
CUSTOM_CSS = """
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600;700&display=swap');

/* Root Variables */
:root {
    --primary-color: #0d9488;
    --primary-dark: #0f766e;
    --primary-light: #14b8a6;
    --secondary-color: #0ea5e9;
    --accent-color: #f59e0b;
    --bg-gradient-start: #0f172a;
    --bg-gradient-end: #1e293b;
    --card-bg: rgba(30, 41, 59, 0.8);
    --card-border: rgba(148, 163, 184, 0.1);
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --success-color: #10b981;
    --error-color: #ef4444;
}

/* Global Styles */
.gradio-container {
    font-family: 'Be Vietnam Pro', sans-serif !important;
    background: linear-gradient(135deg, var(--bg-gradient-start) 0%, var(--bg-gradient-end) 100%) !important;
    min-height: 100vh;
    max-width: 1400px !important;
    margin: 0 auto !important;
}

/* Main Container */
.main-container {
    padding: 2rem;
}

/* Header Styling */
.header-section {
    text-align: center;
    padding: 2rem 1rem;
    margin-bottom: 1.5rem;
    background: linear-gradient(135deg, rgba(13, 148, 136, 0.15) 0%, rgba(14, 165, 233, 0.15) 100%);
    border-radius: 20px;
    border: 1px solid var(--card-border);
    backdrop-filter: blur(10px);
}

.header-section h1 {
    font-size: 2.5rem !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, var(--primary-light) 0%, var(--secondary-color) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5rem !important;
    letter-spacing: -0.5px;
}

.header-section p {
    color: var(--text-secondary) !important;
    font-size: 1.1rem !important;
    font-weight: 400;
    max-width: 600px;
    margin: 0 auto !important;
    line-height: 1.6;
}

/* Logo Container */
.logo-container {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    margin-bottom: 1rem;
}

.logo-icon {
    width: 60px;
    height: 60px;
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    box-shadow: 0 10px 40px rgba(13, 148, 136, 0.3);
}

/* Feature Cards */
.features-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
    justify-content: center;
}

.feature-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 1.25rem;
    flex: 1;
    min-width: 200px;
    max-width: 280px;
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}

.feature-card:hover {
    transform: translateY(-4px);
    border-color: var(--primary-color);
    box-shadow: 0 10px 40px rgba(13, 148, 136, 0.2);
}

.feature-icon {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
}

.feature-title {
    color: var(--text-primary);
    font-weight: 600;
    font-size: 0.95rem;
    margin-bottom: 0.25rem;
}

.feature-desc {
    color: var(--text-secondary);
    font-size: 0.8rem;
    line-height: 1.4;
}

/* Chat Container */
.chat-container {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 20px;
    padding: 1.5rem;
    backdrop-filter: blur(10px);
    margin-bottom: 1rem;
}

/* Chatbot Styling */
.chatbot-wrapper {
    border-radius: 16px !important;
    overflow: hidden;
}

.chatbot {
    background: transparent !important;
    border: none !important;
}

.chatbot .message {
    padding: 1rem 1.25rem !important;
    border-radius: 18px !important;
    margin: 0.5rem 0 !important;
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
    max-width: 85% !important;
}

.chatbot .user {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%) !important;
    color: white !important;
    margin-left: auto !important;
    border-bottom-right-radius: 6px !important;
}

.chatbot .bot {
    background: rgba(51, 65, 85, 0.8) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--card-border);
    border-bottom-left-radius: 6px !important;
}

/* Input Area */
.input-container {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 20px;
    padding: 1.25rem;
    backdrop-filter: blur(10px);
}

.input-row {
    display: flex;
    gap: 0.75rem;
    align-items: flex-end;
}

/* Textbox */
.textbox-container textarea {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 2px solid var(--card-border) !important;
    border-radius: 14px !important;
    color: var(--text-primary) !important;
    font-family: 'Be Vietnam Pro', sans-serif !important;
    font-size: 1rem !important;
    padding: 1rem 1.25rem !important;
    transition: all 0.3s ease !important;
    resize: none !important;
}

.textbox-container textarea:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.2) !important;
    outline: none !important;
}

.textbox-container textarea::placeholder {
    color: var(--text-secondary) !important;
}

/* Labels */
.textbox-container label {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    margin-bottom: 0.5rem !important;
}

/* Primary Button */
.primary-btn {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%) !important;
    border: none !important;
    border-radius: 14px !important;
    color: white !important;
    font-family: 'Be Vietnam Pro', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    padding: 0.9rem 2rem !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 20px rgba(13, 148, 136, 0.3) !important;
    min-width: 120px !important;
}

.primary-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(13, 148, 136, 0.4) !important;
}

.primary-btn:active {
    transform: translateY(0) !important;
}

/* Secondary Button */
.secondary-btn {
    background: rgba(51, 65, 85, 0.6) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 12px !important;
    color: var(--text-secondary) !important;
    font-family: 'Be Vietnam Pro', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    padding: 0.75rem 1.5rem !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
}

.secondary-btn:hover {
    background: rgba(71, 85, 105, 0.6) !important;
    color: var(--text-primary) !important;
    border-color: var(--primary-color) !important;
}

/* Example Questions */
.examples-section {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--card-border);
}

.examples-title {
    color: var(--text-secondary);
    font-size: 0.85rem;
    font-weight: 500;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.examples-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.example-btn {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 20px !important;
    color: var(--text-secondary) !important;
    font-family: 'Be Vietnam Pro', sans-serif !important;
    font-size: 0.85rem !important;
    padding: 0.5rem 1rem !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    white-space: nowrap;
}

.example-btn:hover {
    background: rgba(13, 148, 136, 0.2) !important;
    border-color: var(--primary-color) !important;
    color: var(--primary-light) !important;
}

/* Footer Info */
.footer-section {
    margin-top: 1.5rem;
    padding: 1.25rem;
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 16px;
    backdrop-filter: blur(10px);
}

.footer-grid {
    display: flex;
    justify-content: center;
    gap: 2rem;
    flex-wrap: wrap;
}

.footer-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--text-secondary);
    font-size: 0.85rem;
}

.footer-badge {
    background: rgba(13, 148, 136, 0.2);
    color: var(--primary-light);
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
}

/* Warning Notice */
.warning-notice {
    background: rgba(245, 158, 11, 0.1);
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-radius: 12px;
    padding: 1rem;
    margin-top: 1rem;
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
}

.warning-icon {
    font-size: 1.25rem;
    flex-shrink: 0;
}

.warning-text {
    color: var(--text-secondary);
    font-size: 0.85rem;
    line-height: 1.5;
}

.warning-text strong {
    color: var(--accent-color);
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(15, 23, 42, 0.4);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: rgba(148, 163, 184, 0.3);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(148, 163, 184, 0.5);
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.animate-fade-in {
    animation: fadeIn 0.5s ease forwards;
}

/* Loading Animation */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.loading {
    animation: pulse 1.5s ease-in-out infinite;
}

/* Responsive */
@media (max-width: 768px) {
    .header-section h1 {
        font-size: 1.75rem !important;
    }
    
    .feature-card {
        min-width: 100%;
    }
    
    .footer-grid {
        flex-direction: column;
        align-items: center;
        gap: 1rem;
    }
    
    .input-row {
        flex-direction: column;
    }
    
    .primary-btn {
        width: 100% !important;
    }
}

/* Hide default Gradio elements */
.gr-form {
    background: transparent !important;
    border: none !important;
}

footer {
    display: none !important;
}

/* Button container styling */
.button-row {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-start;
    margin-top: 0.75rem;
}

"""


def create_interface():
    """
    Tạo giao diện Gradio chuyên nghiệp cho chatbot.
    
    Returns:
        gr.Blocks: Gradio interface
    """
    
    with gr.Blocks(
        title="MedAgent - Trợ lý Y tế AI",
        theme=gr.themes.Base(
            primary_hue=gr.themes.colors.teal,
            secondary_hue=gr.themes.colors.cyan,
            neutral_hue=gr.themes.colors.slate,
            font=gr.themes.GoogleFont("Be Vietnam Pro"),
        ),
        css=CUSTOM_CSS
    ) as demo:
        
        # Header Section
        gr.HTML("""
            <div class="header-section animate-fade-in">
                <div class="logo-container">
                    <div class="logo-icon">🏥</div>
                </div>
                <h1>MedAgent</h1>
                <p>Trợ lý y tế thông minh được hỗ trợ bởi AI. Giúp bạn tìm hiểu thông tin về thuốc, 
                triệu chứng và các vấn đề sức khỏe một cách nhanh chóng và chính xác.</p>
            </div>
        """)
        
        # Feature Cards
        gr.HTML("""
            <div class="features-row animate-fade-in" style="animation-delay: 0.1s;">
                <div class="feature-card">
                    <div class="feature-icon">💊</div>
                    <div class="feature-title">Thông tin thuốc</div>
                    <div class="feature-desc">Tra cứu công dụng, liều lượng và cách sử dụng các loại thuốc</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🩺</div>
                    <div class="feature-title">Tư vấn triệu chứng</div>
                    <div class="feature-desc">Phân tích triệu chứng và đề xuất hướng xử lý phù hợp</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">⚠️</div>
                    <div class="feature-title">Cảnh báo tương tác</div>
                    <div class="feature-desc">Kiểm tra tương tác thuốc và tác dụng phụ tiềm ẩn</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📚</div>
                    <div class="feature-title">Kiến thức y khoa</div>
                    <div class="feature-desc">Cung cấp thông tin từ nguồn dữ liệu y tế đáng tin cậy</div>
                </div>
            </div>
        """)
        
        # Chat Container
        with gr.Column(elem_classes=["chat-container", "animate-fade-in"]):
            chatbot = gr.Chatbot(
                label="",
                height=450,
                show_label=False,
                elem_classes=["chatbot-wrapper"],
                type="tuples",
                avatar_images=(
                    None,
                    "https://api.dicebear.com/7.x/bottts/svg?seed=medagent&backgroundColor=0d9488"
                ),
                bubble_full_width=False,
            )
        
        # Input Container
        with gr.Column(elem_classes=["input-container", "animate-fade-in"]):
            with gr.Row(elem_classes=["input-row"]):
                msg = gr.Textbox(
                    label="Đặt câu hỏi của bạn",
                    placeholder="Ví dụ: Paracetamol có tác dụng gì? Liều dùng như thế nào?",
                    lines=2,
                    max_lines=4,
                    elem_classes=["textbox-container"],
                    scale=5,
                    show_label=True,
                )
                submit_btn = gr.Button(
                    "Gửi →",
                    variant="primary",
                    elem_classes=["primary-btn"],
                    scale=1,
                )
            
            with gr.Row(elem_classes=["button-row"]):
                clear_btn = gr.Button(
                    "🗑️ Xóa lịch sử",
                    variant="secondary",
                    elem_classes=["secondary-btn"],
                    size="sm",
                )
            
            # Example Questions
            gr.HTML("""
                <div class="examples-section">
                    <div class="examples-title">
                        <span>💡</span>
                        <span>Câu hỏi gợi ý:</span>
                    </div>
                </div>
            """)
            
            with gr.Row(elem_classes=["examples-grid"]):
                example_btns = []
                examples = [
                    "Paracetamol có tác dụng gì?",
                    "Thuốc ho cho trẻ em",
                    "Thống kê tồn kho theo nhà cung cấp",
                    "Vẽ biểu đồ doanh thu nhập hàng theo tháng",
                    "Top 10 thuốc có giá trị nhập cao nhất",
                ]
                for ex in examples:
                    btn = gr.Button(ex, elem_classes=["example-btn"], size="sm")
                    example_btns.append(btn)
        
        # Warning Notice
        gr.HTML("""
            <div class="warning-notice animate-fade-in" style="animation-delay: 0.3s;">
                <span class="warning-icon">⚠️</span>
                <div class="warning-text">
                    <strong>Lưu ý quan trọng:</strong> Thông tin được cung cấp chỉ mang tính chất tham khảo 
                    và không thay thế cho tư vấn từ bác sĩ hoặc chuyên gia y tế. Vui lòng tham khảo ý kiến 
                    bác sĩ trước khi sử dụng bất kỳ loại thuốc nào.
                </div>
            </div>
        """)
        
        # Footer
        gr.HTML("""
            <div class="footer-section animate-fade-in" style="animation-delay: 0.4s;">
                <div class="footer-grid">
                    <div class="footer-item">
                        <span>🤖</span>
                        <span>Model:</span>
                        <span class="footer-badge">GPT-4o</span>
                    </div>
                    <div class="footer-item">
                        <span>🔍</span>
                        <span>Embedding:</span>
                        <span class="footer-badge">text-embedding-004</span>
                    </div>
                    <div class="footer-item">
                        <span>⚡</span>
                        <span>Hệ thống:</span>
                        <span class="footer-badge">RAG + Database + Chart</span>
                    </div>
                </div>
            </div>
        """)
        
        # Event handlers
        msg.submit(
            chat_with_bot,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot]
        )
        
        submit_btn.click(
            chat_with_bot,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot]
        )
        
        clear_btn.click(
            clear_chat,
            outputs=[msg, chatbot]
        )
        
        # Example button handlers
        for i, btn in enumerate(example_btns):
            btn.click(
                lambda x=examples[i]: x,
                outputs=[msg]
            )
    
    return demo


if __name__ == "__main__":
    print("=" * 60)
    print("Dang khoi dong MedAgent - Tro ly Y te AI...")
    print("Giao dien se mo tai: http://localhost:7860")
    print("=" * 60)
    
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        favicon_path=None,
    )
