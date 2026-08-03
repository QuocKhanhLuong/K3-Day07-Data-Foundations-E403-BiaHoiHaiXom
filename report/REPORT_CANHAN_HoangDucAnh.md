# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Hoàng Đức Anh]
**Nhóm:** [K3-P112-N4]
**Ngày:** [3/8/2026]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai đoạn văn bản có độ tương tự cosine cao nghĩa là chúng có ý nghĩa, chủ đề hoặc nội dung ngữ nghĩa rất giống nhau. Góc giữa hai vector biểu diễn chúng trong không gian embedding là rất nhỏ (gần 0), dẫn đến giá trị cosine gần bằng 1.

**Ví dụ có độ tương tự CAO:**
- Câu A: Tôi rất thích ăn món phở bò.
- Câu B: Phở bò là món ăn yêu thích nhất của tôi.
- Tại sao tương đồng: Cả hai câu đều nói về sở thích ăn món phở bò, dù cách dùng từ và cấu trúc câu có đôi chút khác biệt.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Hôm nay trời mưa to quá.
- Câu B: Giá cổ phiếu công ty công nghệ đang tăng mạnh.
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn không liên quan (thời tiết và tài chính), do đó ngữ nghĩa của chúng khác biệt rõ rệt.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid bị ảnh hưởng bởi độ dài của vector (thường liên quan đến độ dài văn bản hoặc tần suất từ). Trong khi đó, cosine similarity chỉ quan tâm đến hướng của vector, giúp đánh giá chính xác sự tương đồng về mặt ngữ nghĩa mà không bị sai lệch khi so sánh các đoạn văn bản có độ dài khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* Số lượng chunk = làm_tròn_lên((10,000 - 50) / (500 - 50)) = làm_tròn_lên(9950 / 450) = làm_tròn_lên(22.11)
> *Đáp án:* 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi tăng độ chồng chéo (overlap) lên 100, số lượng chunk sẽ là: làm_tròn_lên((10,000 - 100) / (500 - 100)) = làm_tròn_lên(9900 / 400) = làm_tròn_lên(24.75) = 25 chunks (tăng lên so với 23 chunks ban đầu).
> Việc tăng độ chồng chéo giúp giữ lại ngữ cảnh liên kết giữa các chunk, tránh việc một câu hoặc một ý tưởng quan trọng bị cắt đứt đột ngột ở ranh giới giữa hai chunk, từ đó đảm bảo ngữ nghĩa không bị mất mát trong quá trình truy xuất thông tin.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi sử dụng biểu thức chính quy `re.split(r'(?<=[.!?])\s+|(?<=\.)\n', text.strip())` để tách văn bản thành danh sách các câu, đảm bảo giữ nguyên dấu câu. Trường hợp ngoại lệ được xử lý bằng cách bỏ qua các chuỗi rỗng sau khi split. Cuối cùng, tôi gom nhóm các câu lại (nối bằng khoảng trắng) sao cho số lượng câu trong mỗi chunk không vượt quá giới hạn `max_sentences_per_chunk`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Hàm `_split` đệ quy hoạt động bằng cách thử tách văn bản với `separator` đầu tiên trong danh sách. Base case (trường hợp cơ sở) là khi độ dài đoạn văn bản nhỏ hơn hoặc bằng `chunk_size` thì trả về mảng chứa ngay đoạn đó. Nếu đoạn văn bản lớn hơn, nó sẽ bị tách ra; đối với mỗi phần tử sau khi tách, nếu vẫn lớn hơn `chunk_size`, thuật toán tiếp tục gọi đệ quy `_split` với các `separator` còn lại để chia nhỏ tiếp.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Trong `add_documents`, tôi gọi hàm `_embedding_fn` để nhúng `content` của từng `Document` thành vector và lưu bản ghi (gồm id, text, metadata, embedding) vào list `_store`. Với hàm `search`, tôi nhúng câu truy vấn thành vector, sau đó tính độ tương tự cosine (thông qua hàm `compute_similarity`) giữa vector truy vấn với toàn bộ vector trong kho. Kết quả được sắp xếp theo điểm số giảm dần để lấy top K chunk tốt nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Đối với `search_with_filter`, tôi thực hiện bước lọc (filter) các chunks trong `_store` trước (chỉ giữ lại những chunk khớp toàn bộ điều kiện trong `metadata_filter`), sau đó mới tính toán độ tương tự trên tập dữ liệu đã rút gọn nhằm tối ưu hiệu năng. Hàm `delete_document` hoạt động bằng cách duyệt qua `_store` và chỉ giữ lại những chunk có `metadata['doc_id']` khác với tham số `doc_id` cần xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Tác tử sử dụng hàm `store.search(question, top_k)` để truy xuất các chunks liên quan nhất, sau đó trích xuất nội dung (content) và ghép lại thành một đoạn văn bản làm ngữ cảnh (context). Prompt đưa vào LLM được cấu trúc rõ ràng: "Sử dụng thông tin sau để trả lời câu hỏi...\nNgữ cảnh:\n{context}\n\nCâu hỏi: {question}". Prompt này sau đó được truyền vào `llm_fn` để sinh ra câu trả lời dựa trên ngữ cảnh thực tế.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================================= test session starts =============================================
platform win32 -- Python 3.13.12, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe
cachedir: .pytest_cache
rootdir: D:\GIT\K3-Day07-Data-Foundations
plugins: anyio-4.13.0, langsmith-0.8.16, asyncio-1.4.0
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
... (Lược bớt 40 test case ở giữa) ...
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================================= 42 passed in 0.08s ==============================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Tôi rất thích ăn táo. | Táo là loại trái cây yêu thích của tôi. | Cao | 0.5799 | Đúng |
| 2 | Thời tiết hôm nay rất đẹp. | Giá cổ phiếu công nghệ đang tăng. | Thấp | 0.4638 | Đúng |
| 3 | Mèo là loài động vật rất dễ thương. | Chó là một trong những loài vật thông minh nhất. | Cao | 0.6054 | Đúng |
| 4 | Cách nấu phở bò ngon. | Làm thế nào để chuẩn bị một bát phở bò đậm đà. | Cao | 0.5716 | Đúng |
| 5 | I deposited money in the bank. | I sat by the river bank. | Thấp | 0.3783 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 3 (Mèo và Chó) lại có độ tương đồng (0.6054) cao hơn cả cặp 1 (cùng nói về việc thích ăn táo). Điều này phản ánh rằng embeddings biểu diễn ý nghĩa dựa trên tần suất xuất hiện chung (co-occurrence context) của các từ khóa. Từ "chó" và "mèo" thường xuyên xuất hiện cùng nhau trong văn bản (cùng chủ đề động vật nuôi) nên mô hình đánh giá chúng rất gần nhau. Hơn nữa, ở cặp số 5, mô hình cũng phân biệt rất tốt từ đồng âm khác nghĩa (từ "bank" nghĩa là ngân hàng và bờ sông) dẫn đến điểm số thấp (0.3783) đúng như mong đợi.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
