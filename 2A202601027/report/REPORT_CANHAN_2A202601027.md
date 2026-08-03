# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Thu Huyền  
**Nhóm:** BiaHoiHaiXom  
**Ngày:** 03/08/2026  

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Góc giữa hai vector embedding nhỏ (hướng trùng nhau), phản ánh hai đoạn văn bản có ý nghĩa/nội dung rất tương đồng với nhau, không phụ thuộc vào độ dài ngắn của từng câu.

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

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Quy định mượn sách thư viện tối đa bao nhiêu cuốn? | Thư viện cung cấp mượn tài liệu tối đa 5 cuốn sách... | 0.842 | Có | Sinh viên được mượn tối đa 5 cuốn sách tại thư viện. |
| 2 | Thời gian điều chỉnh đăng ký học phần là khi nào? | Sinh viên được điều chỉnh lớp học phần trước thời hạn... | 0.795 | Có | Sinh viên cần điều chỉnh đăng ký trước thời hạn quy định. |
| 3 | Điều kiện nhận học bổng khuyến khích học tập là gì? | Học bổng xét theo điểm trung bình học tập và rèn luyện... | 0.812 | Có | Cần đạt điểm học tập và điểm rèn luyện theo quy định. |
| 4 | Mức phí phạt khi trả sách thư viện quá hạn? | Sinh viên trả sách trễ hạn chịu phí phạt theo quy định... | 0.768 | Có | Cần trả đúng hạn để tránh phát sinh phí phạt quá hạn. |
| 5 | Quy trình thủ tục xin tạm ngưng học tập? | Thủ tục tạm ngưng cần nộp đơn cho phòng đào tạo... | 0.825 | Có | Sinh viên nộp đơn xin tạm ngưng kèm giấy tờ xác nhận. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Việc áp dụng tiền lọc theo thuộc tính metadata (ví dụ: `department` hoặc `category`) giúp thu hẹp không gian tìm kiếm trước khi tính cosine similarity, nâng cao độ chính xác của bước retrieval và hạn chế tối đa thông tin nhiễu đưa vào LLM.

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
