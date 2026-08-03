import os
import sys

# Đảm bảo import được module từ src và thư mục gốc
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from ingest import build_knowledge_base
from src.chunking import RecursiveChunker, SentenceChunker, FixedSizeChunker
from src.embeddings import OpenAIEmbedder
from dotenv import load_dotenv

load_dotenv()

class CustomMarkdownHeaderChunker:
    """Tách chunk theo các thẻ ## Header của Markdown"""
    def chunk(self, text: str) -> list[str]:
        import re
        sections = re.split(r'(?=^## )', text, flags=re.MULTILINE)
        return [s.strip() for s in sections if s.strip()]

def main():
    print("="*80)
    print("CHẠY BENCHMARK ĐÁNH GIÁ CHẤT LƯỢNG TRUY XUẤT (LAB 7)")
    print("="*80)
    
    data_dir = "data/k3_university_services"
    
    # 1. Khởi tạo các Knowledge Base với các chiến lược chunking khác nhau
    print("Đang nạp dữ liệu với các chiến lược...")
    
    recursive_store = build_knowledge_base(data_dir, OpenAIEmbedder(), chunker=RecursiveChunker(chunk_size=400))
    print(f" [OK] RecursiveChunker nạp được {recursive_store.get_collection_size()} chunks.")
    
    sentence_store = build_knowledge_base(data_dir, OpenAIEmbedder(), chunker=SentenceChunker(max_sentences_per_chunk=2))
    print(f" [OK] SentenceChunker nạp được {sentence_store.get_collection_size()} chunks.")
    
    custom_store = build_knowledge_base(data_dir, OpenAIEmbedder(), chunker=CustomMarkdownHeaderChunker())
    print(f" [OK] CustomMarkdownHeaderChunker nạp được {custom_store.get_collection_size()} chunks.\n")
    
    # 2. Định nghĩa 5 câu hỏi benchmark chuẩn từ báo cáo
    queries = [
        {
            "id": 1,
            "q": "Khối lượng đăng ký tối đa trong một học kỳ chính đối với người học không bị cảnh báo là bao nhiêu tín chỉ?",
            "store": custom_store,
            "strategy": "CustomHeader",
            "filter": None
        },
        {
            "id": 2,
            "q": "Điều kiện GPA và điểm rèn luyện để đạt học bổng loại A là gì?",
            "store": sentence_store, 
            "strategy": "SentenceChunker",
            "filter": None
        },
        {
            "id": 3,
            "q": "Quy trình sử dụng phòng đọc tại chỗ gồm những bước nào?",
            "store": recursive_store,
            "strategy": "RecursiveChunker",
            "filter": None
        },
        {
            "id": 4,
            "q": "Học bổng KKHT có những mức nào và mức của từng loại được tính như thế nào so với loại khá?",
            "store": recursive_store,
            "strategy": "RecursiveChunker",
            "filter": None
        },
        {
            "id": 5,
            "q": "Khi cần điều chỉnh đăng ký học phần, người học có thể thực hiện những thao tác nào và trong thời điểm nào?",
            "store": custom_store,
            "strategy": "CustomHeader + Metadata Filter",
            "filter": {"audience": "student"}
        }
    ]
    
    # 3. Chạy truy xuất và in kết quả top 3
    for q in queries:
        print("-" * 80)
        print(f"Câu {q['id']} ({q['strategy']}): {q['q']}")
        if q["filter"]:
            print(f"   [Metadata Filter]: {q['filter']}")
            results = q["store"].search_with_filter(q["q"], top_k=3, metadata_filter=q["filter"])
        else:
            results = q["store"].search(q["q"], top_k=3)
            
        for i, res in enumerate(results):
            content_preview = res['content'][:120].replace('\n', ' ') + "..."
            print(f"  > Top {i+1} [Score: {res['score']:.4f}] - Doc: {res['metadata'].get('doc_id')}")
            print(f"    Preview: {content_preview}")
    
    print("\n" + "="*80)
    print("LƯU Ý: Script hiện đang dùng `OpenAIEmbedder` (text-embedding-3-small) với API Key từ file .env.")

if __name__ == "__main__":
    main()
