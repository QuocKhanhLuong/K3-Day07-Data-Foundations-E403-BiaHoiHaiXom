# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lương Quốc Khánh
**Mã số sinh viên:** 2A202601713
**Lớp/biến thể lab:** K3
**Nhóm:** Chưa có thông tin nhóm trong repo
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
Hai vector embedding có hướng gần nhau, nên hai đoạn văn bản thường có nội dung hoặc ý nghĩa gần nhau. Điểm càng gần 1 thì mức tương đồng theo hướng càng cao.

**Ví dụ có độ tương tự CAO:**
- Câu A: Sinh viên cần kiểm tra học phần tiên quyết trước khi đăng ký.
- Câu B: Trước khi đăng ký, sinh viên phải xem các môn học tiên quyết.
- Tại sao tương đồng: Hai câu cùng diễn đạt yêu cầu kiểm tra môn tiên quyết trước khi đăng ký học phần.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Sinh viên đăng ký học phần trên cổng học vụ.
- Câu B: Thư viện cho mượn tài liệu bằng thẻ định danh.
- Tại sao khác: Một câu nói về đăng ký môn học, câu còn lại nói về dịch vụ mượn tài liệu thư viện.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
Cosine tập trung vào góc giữa hai vector và ít bị ảnh hưởng bởi độ lớn tuyệt đối của vector, phù hợp khi so sánh hướng biểu diễn ngữ nghĩa của văn bản. Khoảng cách Euclid nhạy hơn với độ dài hoặc chuẩn vector, dù hai văn bản có thể cùng hướng.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*

`stride = 500 - 50 = 450`.

`ceil((10,000 - 50) / 450) = ceil(9,950 / 450) = ceil(22.111...) = 23`.

> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
Khi `overlap=100`, `stride=500-100=400` và số chunk là `ceil((10,000-100)/400) = ceil(24.75) = 25` chunks. Overlap lớn hơn giúp giữ ngữ cảnh nằm ở ranh giới hai chunk, nhưng làm tăng số chunk, dung lượng lưu trữ và chi phí tìm kiếm.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
Mình dùng regex `(?<=[.!?])\s+` để tách sau dấu chấm, chấm than hoặc chấm hỏi khi theo sau là khoảng trắng hoặc xuống dòng; dấu câu được giữ lại trong câu. Các câu sau đó được loại khoảng trắng thừa và gom tối đa `max_sentences_per_chunk` câu mỗi chunk. Văn bản rỗng trả về danh sách rỗng, còn giá trị `max_sentences_per_chunk` nhỏ hơn 1 được chặn ở 1.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
Thuật toán thử các separator theo thứ tự ưu tiên: đoạn, dòng, câu, khoảng trắng rồi đến cắt theo ký tự. Base case là đoạn đã không dài hơn `chunk_size`; nếu không còn separator phù hợp thì cắt cố định để luôn tiến triển. Các phần quá dài được đệ quy với các separator còn lại, sau đó các phần liền kề được gộp khi vẫn nằm trong giới hạn kích thước.

**`HeadingAwareChunker` — strategy benchmark chính:**
Chiến lược tách tài liệu theo heading Markdown, giữ hierarchy heading trong nội dung chunk và dùng `RecursiveChunker` cho section vượt ngân sách. Benchmark chung khóa `chunk_size=400`; vì heading context cũng chiếm ký tự, một evidence phrase dài có thể bị tách, đây là trade-off được ghi nhận trong kết quả chứ không điều chỉnh sau khi xem điểm.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
Mỗi `Document` được chuyển thành record gồm id, nội dung, metadata và embedding; metadata được sao chép và có `doc_id` mặc định để hỗ trợ xóa. Store dùng ChromaDB nếu có, nếu không dùng danh sách trong bộ nhớ. Với store trong bộ nhớ, query được embed rồi xếp hạng các record bằng tích vô hướng giảm dần và lấy tối đa `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
Metadata được lọc trước khi tính/xếp hạng similarity; record phải khớp tất cả các cặp khóa-giá trị trong bộ lọc. `delete_document` xóa mọi record có `metadata['doc_id']` bằng `doc_id` yêu cầu, đồng thời hỗ trợ id trực tiếp cho các document chưa có metadata doc_id.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
Agent gọi `store.search(question, top_k)` để lấy các chunk liên quan, gắn nội dung và source vào từng block context, rồi đưa context cùng câu hỏi vào prompt. Prompt yêu cầu chỉ trả lời dựa trên context và nói rõ khi bằng chứng không đủ; cuối cùng agent gọi `llm_fn` đúng một lần.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ pytest tests/ -v
platform darwin -- Python 3.13.2, pytest-8.3.4
collected 42 items
============================== 42 passed in 0.04s ==============================

$ .venv/bin/python -m unittest discover -s tests -v
Python 3.11.15
----------------------------------------------------------------------
Ran 42 tests in 0.004s

OK
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

> Ghi chú môi trường: pytest đã chạy pass trên Python 3.13.2; bộ unittest tương đương cũng chạy pass trên Python 3.11.15 trong `.venv`. Venv Python 3.11 chưa có pytest vì `ensurepip` của bản Homebrew hiện lỗi khi nạp `pyexpat`; đây là vấn đề môi trường, không phải lỗi implementation.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Course registration requires checking prerequisites. | Students should check prerequisite courses before registering. | cao | -0.008684476 | Không |
| 2 | The library lends books and provides study space. | The library offers borrowing services and places to study. | cao | -0.001762505 | Không |
| 3 | Students register for courses through the academic portal. | Scholarships may have eligibility requirements. | thấp | 0.104955991 | Không |
| 4 | Check the timetable before enrolling in a course. | Borrow a book using a valid library identification card. | thấp | -0.265218510 | Có |
| 5 | Vector databases store embeddings for similarity search. | Embeddings are stored in vector databases to support similarity search. | cao | 0.100825166 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
Các cặp 1 và 2 có nội dung gần nhau theo cách hiểu của con người nhưng điểm mock lại âm hoặc gần 0, trong khi cặp 3 không liên quan lại có điểm dương. Điều này cho thấy `_mock_embed` chỉ tạo vector xác định để kiểm thử, gần như ngẫu nhiên theo toàn chuỗi; không được dùng để kết luận chất lượng semantic retrieval tiếng Việt.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Kết quả dưới đây được tạo bởi `bench.py` dùng chung cho cả nhóm, với cùng corpus, `data/k3_university_services/benchmarks.json`, OpenAI `text-embedding-3-small`, agent `gpt-4o-mini`, prompt và `top_k=3`. Strategy của mình là **Heading-aware chunking + Recursive fallback**, `chunk_size=400`.

Kết quả chi tiết nằm tại `2A202601713/benchmark_heading_aware.json`; common output nằm tại `benchmark_results.json`. Strategy tạo 41 chunks.

| Query | Top-1 chunk | Score | Evidence rank | Expected section | Agent grounding |
|---|---|---:|---:|---:|---|
| q1 numeric | `course-registration-student::chunk_5` (0.638865) | 1/2 | 1 | 1 | Evidence ở top-1 nhưng agent quote dùng `...`, không phải chuỗi liên tục |
| q2 condition | `scholarship-policy::chunk_4` (0.645013) | 2/2 | 1 | 1 | Evidence ở top-1; agent trả lời đúng và có context quote |
| q3 process | `library-services::chunk_1` (0.761519) | 0/2 | — | 1 | Agent trả lời nhưng exact evidence 349 ký tự không nằm trong một chunk |
| q4 list | `scholarship-policy::chunk_3` (0.763362) | 2/2 | 1 | 1 | Evidence ở top-1; agent trả lời đủ ba mức |
| q5 metadata-filter | `course-registration-student::chunk_3` (0.683608) | 0/2 | — | 1 | Filter đã áp dụng nhưng evidence bị tách bởi heading context |

**Tổng quan:** 3/5 query có evidence trong top-3; 3/5 có evidence ở top-1; 2/5 agent answer được xác nhận grounded vì exact gold evidence phải có trong context. Tổng điểm theo rubric chung là **5/10**.

### A/B metadata filter cho q5

q5 chạy hai lần với cùng query và `top_k=3`:

| Chế độ | Top-1 | Audience | Score | Evidence rank |
|---|---|---|---:|---:|
| Không filter | `course-registration-student::chunk_3` | student | 0.683608 | — |
| `{"audience": "student"}` | `course-registration-student::chunk_3` | student | 0.683608 | — |

Filter được áp dụng đúng và không làm thay đổi top-1/top-3 trong lần chạy này vì truy vấn không filter vốn đã xếp các chunk `audience=student` lên đầu. Tuy nhiên, filter không thể ghép hai chunk liền nhau thành một evidence chunk, nên không cứu được q5 với strategy này.

### Failure case

Có hai failure quan sát được: q1 retrieval đúng top-1 nhưng agent quote rút gọn bằng `...`, nên không đạt kiểm tra grounding exact; q3 và q5 có câu trả lời được agent sinh ra nhưng exact evidence không nằm trọn trong một chunk 400 do heading context. Bài học là heading-aware giúp giữ cấu trúc, nhưng phải cân đối ngân sách heading với evidence phrase khi chấm ở mức chunk.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
Chưa có dữ liệu demo hoặc kết quả của thành viên khác trong repo để đưa ra nhận xét có căn cứ.

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
