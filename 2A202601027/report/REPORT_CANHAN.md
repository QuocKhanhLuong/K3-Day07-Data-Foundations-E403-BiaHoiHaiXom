# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Thu Huyền  
**MSSV:** 2A202601027  
**Chiến lược phân công:** RecursiveChunker (`chunk_size = 400`)  
**Nhóm:** BiaHoiHaiXom  
**Ngày:** 03/08/2026  

> **Legacy snapshot:** thư mục này dùng MSSV cũ `2A202601027`. Không dùng phần benchmark cũ bên dưới để so sánh; kết quả chính thức của Nguyễn Thu Huyền dùng MSSV `2A20261027` và được cập nhật tại [report/REPORT_CANHAN.md](../../report/REPORT_CANHAN.md).

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Góc giữa hai vector embed nhỏ (hướng trùng nhau), phản ánh hai đoạn văn bản có ý nghĩa/nội dung rất tương đồng với nhau, không phụ thuộc vào độ dài ngắn của từng câu.

**Ví dụ có độ tương tự CAO:**
- Câu A: Sinh viên có thể mượn tối đa 5 cuốn sách tại thư viện trường.
- Câu B: Thư viện đại học cho phép người học mượn tối đa 5 đầu sách.
- Tại sao tương đồng: Cả hai câu đều diễn đạt cùng một chủ đề (quy định mượn sách thư viện) với các từ ngữ mang ý nghĩa tương đương.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Sinh viên có thể mượn tối đa 5 cuốn sách tại thư viện trường.
- Câu B: Đội tuyển bóng đá nam đã giành chiến thắng thuyết phục trong trận chung kết.
- Tại sao khác: Hai câu thuộc hai lĩnh vực hoàn toàn khác nhau (quy định thư viện vs thể thao), không có mối liên hệ ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid bị ảnh hưởng bởi độ dài (độ lớn vector), khiến hai văn bản cùng nội dung nhưng độ dài khác nhau có khoảng cách xa. Độ tương tự cosine chỉ đo góc hướng vector (đã chuẩn hóa độ dài), giúp đánh giá chính xác độ tương đồng ngữ nghĩa.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* $\text{số lượng chunk} = \text{làm\_tròn\_lên}\left(\frac{10000 - 50}{500 - 50}\right) = \text{làm\_tròn\_lên}\left(\frac{9950}{450}\right) = \text{làm\_tròn\_lên}(22.11) = 23$
> *Đáp án:* 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, số lượng chunk tăng từ 23 lên 25 chunks ($\frac{9900}{400} = 24.75 \rightarrow 25$). Tăng độ chồng chéo giúp giữ lại ngữ cảnh liên tục ở ranh giới giữa các chunk lân cận, tránh việc ý nghĩa của câu bị ngắt đoạn khi chia nhỏ.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng biểu thức chính quy `re.split(r'(?<=[.!?])\s+|\.\n', text)` với kỹ thuật lookbehind để tách văn bản chính xác theo ranh giới câu mà không làm mất dấu câu. Sau đó nhóm các câu lại thành từng chunk có tối đa `max_sentences_per_chunk` câu. Xử lý các edge cases như văn bản rỗng, văn bản không có dấu câu hoặc ngắn hơn kích thước nhóm.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Sử dụng giải thuật đệ quy thử nghiệm danh sách dấu phân cách theo thứ tự ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Base case là khi đoạn văn bản ngắn hơn `chunk_size` hoặc không còn separator nào (sẽ cắt chuỗi theo độ dài). Nếu một đoạn tách ra vẫn lớn hơn `chunk_size`, hàm sẽ gọi đệ quy `_split` với danh sách dấu phân cách tiếp theo.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Với `add_documents`, mỗi document được chuẩn hóa thành một record chứa `id`, `content`, `metadata` và vector `embedding` (sinh bởi `self._embedding_fn`) rồi đưa vào `self._store`. Với `search`, query được nhúng thành vector và tính điểm Cosine Similarity với từng chunk trong store, sắp xếp giảm dần và lấy `top_k` kết quả tốt nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` thực hiện pre-filtering (lọc trước): lọc danh sách các chunk trong store khớp toàn bộ điều kiện `metadata_filter` rồi mới tính similarity search trên tập kết quả đó. `delete_document` lọc bỏ tất cả chunk có `id` hoặc `metadata['doc_id']` trùng với `doc_id` cần xóa, trả về `True` nếu có ít nhất 1 chunk bị loại bỏ.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Lấy ra top `top_k` chunks liên quan nhất từ `EmbeddingStore`, định dạng thành chuỗi `Context` có đánh số thứ tự. Ghép `Context` và `Question` vào template prompt RAG chuẩn rồi truyền vào `llm_fn` (tích hợp OpenAI API `gpt-4o-mini` hoặc fallback demo) để tạo ra câu trả lời cuối cùng.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.1.1, pluggy-1.6.0 -- D:\vin\lab06\K3-Day07-Data-Foundations\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\vin\lab06\K3-Day07-Data-Foundations
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.12s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên được mượn tối đa 5 cuốn sách. | Thư viện cho phép người học mượn tối đa 5 đầu sách. | cao | 0.892 | Đúng |
| 2 | Quy định về đóng học phí học kỳ 1. | Hướng dẫn mượn trả sách tại thư viện. | thấp | 0.105 | Đúng |
| 3 | Thời hạn đăng ký học phần là tuần thứ 2. | Sinh viên đăng ký môn học trước tuần 2 của kỳ. | cao | 0.854 | Đúng |
| 4 | Điều kiện xét học bổng khuyến khích học tập. | Quy định xử lý kỷ luật sinh viên vi phạm. | thấp | 0.187 | Đúng |
| 5 | Thủ tục tạm ngưng học tập xin lưu kết quả. | Hướng dẫn xin tạm hoãn học tập giữ điểm. | cao | 0.831 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 5 gây bất ngờ nhất vì hai câu sử dụng các từ ngữ khác nhau ("tạm ngưng" vs "tạm hoãn", "lưu kết quả" vs "giữ điểm") nhưng điểm độ tương tự vẫn rất cao (0.831). Điều này cho thấy vector embeddings biểu diễn khái niệm ngữ nghĩa trong không gian nhiều chiều chứ không phụ thuộc vào từ vựng trùng lặp chính xác (exact word match).

---

## 5. Kết quả truy xuất cá nhân (Benchmark Results with `RecursiveChunker`) — Cá nhân (10 điểm)

Đây là snapshot legacy dùng MSSV cũ `2A202601027`; không dùng bảng cũ bên dưới để so sánh. Kết quả chính thức của Nguyễn Thu Huyền dùng MSSV `2A20261027`, được chạy bằng `bench.py` với OpenAI `text-embedding-3-small`, `gpt-4o-mini`, `top_k=3`, exact chunk-level evidence checker và cùng prompt với các thành viên còn lại. Kết quả chính thức nằm tại [report/REPORT_CANHAN.md](../../report/REPORT_CANHAN.md), [2A20261027/benchmark/recursive_results.json](../../2A20261027/benchmark/recursive_results.json) và `benchmark_results.json`.

| # | Query ID | Câu hỏi (Query) | Top-1 Chunk truy xuất được | Điểm Score | Evidence Hit (Top-3) | Agent Answer (tóm tắt) | Điểm (0/1/2) |
|---|---|---|---|---|---|---|---|
| 1 | `q1` | Khối lượng đăng ký tối đa... | `course-registration-student::chunk_3` | 0.606405 | True (Rank 1) | Agent trả lời đúng số liệu nhưng quote dùng `...` | 1 |
| 2 | `q2` | Điều kiện GPA và điểm rèn luyện... | `scholarship-policy::chunk_3` | 0.721844 | True (Rank 1) | Agent trả lời đúng và có context quote | 2 |
| 3 | `q3` | Quy trình sử dụng phòng đọc... | `library-services::chunk_0` | 0.713061 | False | Exact evidence không nằm trong một chunk | 0 |
| 4 | `q4` | Học bổng KKHT có những mức... | `scholarship-policy::chunk_2` | 0.769859 | True (Rank 1) | Evidence ở top-1 nhưng agent không có quote kiểm chứng được | 1 |
| 5 | `q5` | Khi cần điều chỉnh đăng ký... | `course-registration-student::chunk_2` | 0.675889 | True (Rank 1) | Filter student, agent grounded | 2 |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5
**Agent answer được xác nhận grounded:** 2 / 5
**Tổng điểm Benchmark chính thức:** **6 / 10**

### Phân tích Phân Tách & Tối Ưu (Chunking & Optimization Analysis):
- **Query Q1 (`q1`):** Evidence ở `course-registration-student::chunk_3`, rank 1, nhưng agent quote dùng `...`, nên đạt 1/2.
- **Query Q2 (`q2`):** `scholarship-policy::chunk_3` đứng rank 1 và agent có context quote, đạt 2/2.
- **Query Q3 (`q3`):** Evidence phrase dài không nằm trọn trong một chunk, đạt 0/2.
- **Query Q4 (`q4`):** Evidence ở rank 1 nhưng agent không có quote kiểm chứng được, đạt 1/2.
- **Query Q5 (`q5`):** Filter student giữ evidence ở rank 1 và agent grounded, đạt 2/2.

**Bài học về `RecursiveChunker`:**
> Kết quả chính thức đạt **6 / 10** trong run công bằng. Evidence của q3 quá dài để nằm trọn trong một chunk 400 ký tự; q4 có evidence ở top-1 nhưng agent không cung cấp quote kiểm chứng được theo evaluator chung.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
