# K3 — Ngày 7: Nền Tảng Dữ Liệu, Embedding & Vector Store

## Team

- **Team:** BiaHoiHaiXom
- **Members:** 4 thành viên
  
  | STT | Họ và tên | Mã sinh viên |
  |:---:|---|---|
  | 1 | Lương Quốc Khánh | 2A202601713 |
  | 2 | Hoàng Đức Anh | 2A202601223 |
  | 3 | Trần Nguyễn Mỹ Anh | 2A20261019 |
  | 4 | Nguyễn Thu Huyền | 2A20261027 |

> Bản K3 của Lab 07. Hướng dẫn Codelabs được phát riêng trên lớp/LMS (không kèm trong repo); yêu cầu Giai đoạn 2 riêng xem [K3_VARIANT.md](K3_VARIANT.md).

---

## Mục Tiêu

Sau bài thực hành (lab) này, bạn cần có thể:
- Giải thích độ tương tự cosine (cosine similarity) và dự đoán điểm tương đồng giữa các văn bản
- Triển khai 3 chiến lược chia nhỏ (chunking) và so sánh ưu nhược điểm
- Xây dựng kho lưu trữ vector (vector store) với các tính năng tìm kiếm (search), lọc (filter), và xóa (delete)
- Kết nối cơ sở tri thức (knowledge base) với tác tử (agent) qua mô hình RAG
- Chỉ ra khi nào việc truy xuất (retrieval) giúp ích và khi nào nó thất bại

---

## Cấu Trúc Lab: 2 Giai Đoạn (Phase)

### Giai Đoạn 1 — Cá Nhân: Hoàn Thành gói mã nguồn `src`

Mỗi sinh viên **tự mình** hoàn thành tất cả các mục CẦN LÀM (TODO) trong `src/chunking.py`, `src/store.py`, và `src/agent.py`. Lớp dữ liệu `Document` (dataclass) và `FixedSizeChunker` đã được lập trình sẵn làm ví dụ.

### Giai Đoạn 2 — Nhóm: So Sánh Chiến Lược Truy Xuất (Retrieval Strategy)

Nhóm cùng chọn một bộ tài liệu và thống nhất 5 câu hỏi đánh giá (benchmark queries). Mỗi thành viên **thử chiến lược riêng** (chunking, metadata), chạy cùng các câu hỏi, rồi **so sánh kết quả trong nhóm** để học hỏi lẫn nhau.

---

## Thiết Lập Môi Trường

### Python 3.11 là chuẩn của Lab

Phần bắt buộc được kiểm thử trên **Python 3.11**. Dùng đúng trình thông dịch (interpreter) này khi tạo môi trường ảo (virtual environment) (`py -3.11` trên Windows hoặc `python3.11` trên macOS/Linux); file `.python-version` cũng đã khai báo phiên bản chuẩn.

```bash
pip install -r requirements.txt
pytest tests/ -v          # Phần lớn bài kiểm thử sẽ THẤT BẠI (chưa được lập trình)
```

Mặc định, lab vẫn chạy với trình nhúng giả lập `_mock_embed` nên **không bắt buộc** cài đặt mô hình nhúng (embedder) thật.
File `.env` được tự động nạp khi chạy `main.py`. Với các đoạn mã Python (snippet) chạy trực tiếp, hãy dùng lệnh `export` cho các biến môi trường cần thiết hoặc gọi hàm `load_dotenv()` nếu cần.

> **Giai đoạn 2 (so sánh retrieval): đặt `EMBEDDING_PROVIDER=local`** để dùng trình nhúng đa ngữ (mô tả bên dưới). Mock sinh vector xác định nhưng **gần như ngẫu nhiên theo cả chuỗi** — chỉ hợp để chạy unit test, **không phản ánh chất lượng ngữ nghĩa** và không nên dùng để kết luận chiến lược chunking/tiếng Việt nào tốt hơn.

## Tùy Chọn Mô Hình Nhúng (Embedding Backend)

### 1) Mặc định: Trình nhúng giả lập (Mock embedder)

Không cần cài gì thêm ngoài:
```bash
pip install -r requirements.txt
```

### 2) Tùy chọn: Trình nhúng đa ngữ cục bộ (Local multilingual embedder)

```bash
pip install -r requirements-local.txt
python3 - <<'PY'
from src import LocalEmbedder
embedder = LocalEmbedder()
print(embedder._backend_name)
print(len(embedder("embedding smoke test")))
PY
```

- Gói `src` hỗ trợ mô hình `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, phù hợp với kho ngữ liệu tiếng Việt, thông qua thư viện `sentence-transformers`.
- Lần chạy đầu tiên, mô hình và thư viện phụ thuộc PyTorch sẽ được tải về; đây là phần **tùy chọn**, không cần thiết để làm các TODO hoặc chạy bài kiểm thử.

### 3) Tùy chọn: Trình nhúng OpenAI (OpenAI embedder)

```bash
pip install openai
export OPENAI_API_KEY=your-key-here
python3 - <<'PY'
from src import OpenAIEmbedder
embedder = OpenAIEmbedder()
print(embedder._backend_name)
print(len(embedder("embedding smoke test")))
PY
```

- Mô hình mặc định cho lựa chọn này là `text-embedding-3-small`
- Có thể đổi mô hình bằng cách:
```bash
export OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Quy tắc dự phòng (fallback)

- Nếu không chọn gì, lab mặc định dùng `_mock_embed`
- Nếu chọn `local` hoặc `openai` nhưng thiết lập bị thiếu, mã nguồn sẽ tự động chuyển về dùng `_mock_embed`
- Có thể cấu hình qua file `.env` mà không cần chạy lệnh `source .env`
- File kịch bản `main.py` chạy từ đầu đến cuối và nhập (import) các API công khai từ gói `src`

### Lệnh xác minh nhanh (verify)

Sau khi cài đặt các thư viện tùy chọn, bạn có thể kiểm tra từng backend riêng:

**Kiểm tra local embedder**

```bash
python3 - <<'PY'
from src import LocalEmbedder

embedder = LocalEmbedder()
print(embedder._backend_name, len(embedder("embedding smoke test")))
PY
```

**Kiểm tra OpenAI embedder**

```bash
python3 - <<'PY'
from pathlib import Path
from dotenv import load_dotenv
from src import OpenAIEmbedder

load_dotenv(dotenv_path=Path(".env"), override=False)
embedder = OpenAIEmbedder()
print(embedder._backend_name, len(embedder("embedding smoke test")))
PY
```

> Lưu ý: `OpenAIEmbedder` cần biến môi trường `OPENAI_API_KEY` hợp lệ hoặc có trong file `.env`.

---

## Cấu Trúc Thư Mục

```
├── README.md              ← Bạn đang đọc file này
├── exercises.md           ← Bài tập (4 phần)
├── main.py               ← Điểm bắt đầu cho việc chạy thử thủ công (manual demo)
├── ingest.py             ← Pipeline nạp dữ liệu ĐÃ CUNG CẤP (front matter → chunk → metadata → store)
├── src/
│   ├── chunking.py       ← Các lớp Chunking + hàm hỗ trợ tính độ tương tự
│   ├── store.py          ← Lớp EmbeddingStore
│   ├── agent.py          ← Lớp KnowledgeBaseAgent
│   └── ...               ← Các module nhỏ hơn
├── data/                  ← Tài liệu mẫu + tài liệu do nhóm thu thập (.txt/.md)
├── tests/
│   └── test_solution.py   ← Bộ kiểm thử (42 tests)
├── report/
│   ├── REPORT_NHOM.md    ← Báo cáo nhóm (1 file/nhóm)
│   └── REPORT_CANHAN.md  ← Báo cáo cá nhân (1 file/sinh viên)
├── docs/
│   ├── DATA_COLLECTION.md ← Hướng dẫn thu thập & format dữ liệu
│   ├── EVALUATION.md     ← Các tiêu chí đánh giá
│   └── SCORING.md        ← Tiêu chí chấm điểm
└── requirements.txt
```

---

## Các Giai Đoạn Của Lab

| Giai Đoạn | Hoạt Động |
|-----------|-----------|
| Chuẩn bị tài liệu | Nhóm thu thập tài liệu theo **chủ đề cố định của lớp K3** (dịch vụ/quy định đại học), chuyển sang định dạng .md/.txt |
| Lập trình cá nhân | Khởi động + hoàn thành tất cả TODO (cá nhân) |
| Thiết kế chiến lược | Mỗi người thử chiến lược riêng, thống nhất 5 câu hỏi đánh giá |
| So sánh trong nhóm | Chạy đánh giá (benchmark), so sánh kết quả, chuẩn bị thuyết trình |
| Thuyết trình & thảo luận | Trình bày chiến lược + so sánh, thảo luận giữa các nhóm |

---

## Nhiệm Vụ Cá Nhân (Giai Đoạn 1)

### Đã lập trình sẵn (để tham khảo)
- `Document` dataclass — cấu trúc lưu trữ văn bản + siêu dữ liệu (metadata)
- `FixedSizeChunker` — chia nhỏ theo kích thước cố định với cơ chế cửa sổ trượt (sliding window)

### Cần lập trình (CẦN LÀM)
- `SentenceChunker` — chia nhỏ theo ranh giới câu
- `RecursiveChunker` — thử nghiệm từng dấu phân cách theo thứ tự
- `compute_similarity` — tính độ tương tự cosine
- `ChunkingStrategyComparator` — so sánh 3 chiến lược
- `EmbeddingStore` — lớp bao bọc (wrapper) cho kho lưu trữ vector (gồm 5 phương thức)
- `KnowledgeBaseAgent` — tác tử theo mô hình RAG

---

## Nhiệm Vụ Nhóm (Giai Đoạn 2) — So Sánh Chiến Lược

> Trước khi thu thập dữ liệu, đọc [Hướng dẫn crawl và format dữ liệu](docs/DATA_COLLECTION.md). Mỗi nhóm crawl theo **chủ đề cố định của lớp K3** (dịch vụ/quy định đại học — xem [K3_VARIANT.md](K3_VARIANT.md)), dùng 5–10 nguồn công khai/được phép và lưu kèm metadata có thể truy vết.

1. **Thu thập bộ tài liệu** (5-10 tài liệu) trong chủ đề cố định của lớp K3: quy định/chính sách/FAQ/hướng dẫn về đăng ký môn, học phí, học bổng, thư viện, ký túc xá
2. **Chuyển sang định dạng .txt/.md** nếu cần (xem mẹo trong exercises.md); nạp bằng `build_knowledge_base()` trong `ingest.py`
3. **Thống nhất 5 câu hỏi đánh giá** kèm theo câu trả lời chuẩn (gold answers)
4. **Mỗi thành viên thử chiến lược riêng**: phương pháp chunking, các tham số, cấu trúc metadata
5. **So sánh kết quả trong nhóm**: chiến lược nào cho việc truy xuất tốt hơn? Tại sao?

---

## Cách Tự Đánh Giá Kết Quả Truy Xuất (Retrieval)

Khi chạy đánh giá (benchmark), đừng chỉ hỏi **"code có chạy không?"** mà hãy tự kiểm tra 5 góc nhìn sau:

1. **Độ chính xác của truy xuất (Retrieval Precision)**
   - Top-3 kết quả trả về có chứa chunk thực sự liên quan không?
   - Điểm số (Score) có giúp phân biệt được kết quả tốt và kết quả nhiễu không?

2. **Tính mạch lạc của Chunk (Chunk Coherence)**
   - Chunk có giữ được trọn vẹn ý nghĩa không?
   - Chiến lược nào làm cho chunk dễ đọc và dễ truy xuất hơn?

3. **Tính hữu dụng của Metadata (Metadata Utility)**
   - Hàm `search_with_filter()` có giúp tăng độ chính xác không?
   - Bộ lọc có quá khắt khe, làm mất đi các kết quả tốt không?

4. **Chất lượng thông tin nền (Grounding Quality)**
   - Câu trả lời của tác tử (agent) có thực sự dựa trên ngữ cảnh được truy xuất không?
   - Bạn có thể chỉ ra chunk nào cung cấp thông tin cho câu trả lời không?

5. **Tác động của chiến lược dữ liệu (Data Strategy Impact)**
   - Bộ tài liệu mà nhóm chọn có phù hợp với các câu hỏi đánh giá không?
   - Chiến lược chunking / metadata của bạn có phù hợp với chủ đề không?

> Xem `docs/EVALUATION.md` nếu bạn muốn một danh sách kiểm tra (checklist) chi tiết hơn cho phần này.

---

## Chấm Điểm

Xem chi tiết tại `docs/SCORING.md`. Tóm tắt:

| Phần | Điểm |
|------|------|
| Cá nhân (mã nguồn + phân tích) | 60 |
| Nhóm (chiến lược + so sánh) | 40 |
| **Tổng** | **100** |

---

## Sản Phẩm Nộp Bài

1. Thư mục `src/` — hoàn thành tất cả các mục CẦN LÀM (TODO) cần thiết
2. File `report/REPORT_NHOM.md` — **một báo cáo nhóm** (chung: lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo)
3. File `report/REPORT_CANHAN.md` — **một báo cáo cá nhân cho mỗi sinh viên** (riêng: hướng tiếp cận, hoàn thiện code, dự đoán, kết quả truy xuất)

---

## Chạy Kiểm Thử

```bash
pytest tests/ -v
```
