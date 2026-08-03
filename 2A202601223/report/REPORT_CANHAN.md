# Báo cáo cá nhân — FixedSizeChunker

**Họ tên:** Hoàng Đức Anh
**MSSV:** 2A202601223
**Strategy:** `FixedSizeChunker(chunk_size=400, overlap=80)`
**Corpus:** `data/k3_university_services`
**Ngày benchmark:** 03/08/2026

## 1. Khởi động

Cosine similarity cao nghĩa là hai embedding có hướng gần nhau, thường biểu diễn nội dung/ngữ nghĩa gần nhau. Với text embedding, cosine tập trung vào hướng vector nên ít bị ảnh hưởng bởi độ dài tuyệt đối hơn khoảng cách Euclid.

Với tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`: stride là 450 và số chunk là `ceil((10.000 - 50) / 450) = 23`. Nếu overlap tăng lên 100 thì stride là 400 và số chunk là `ceil((10.000 - 100) / 400) = 25`; đổi lại, ngữ cảnh ở biên được giữ nhiều hơn nhưng dữ liệu trùng lặp tăng.

## 2. Hướng tiếp cận

- `FixedSizeChunker` cắt theo cửa sổ ký tự cố định và di chuyển theo stride 320.
- `EmbeddingStore` lưu embedding, metadata và content của từng chunk; retrieval lấy top-k theo cosine similarity.
- `search_with_filter` lọc metadata trước khi xếp hạng, phù hợp với các query có `audience`.
- `KnowledgeBaseAgent` nhận top-3 context rồi truyền vào LLM/demo function. Trong lần chạy này demo function chỉ dùng để kiểm pipeline, không được xem là câu trả lời hoàn chỉnh.

Các file source đã hoàn thiện được giữ nguyên; thay đổi chỉ nằm trong thư mục benchmark cá nhân và report cá nhân.

## 3. Kiểm thử

Kiểm thử và benchmark chính thức dùng root `bench.py` chung của nhóm. Runner dùng cùng corpus, `data/k3_university_services/benchmarks.json`, OpenAI `text-embedding-3-small`, agent `gpt-4o-mini`, prompt, exact evidence checker và `top_k=3` cho cả bốn strategy.

## 4. Cấu hình và phạm vi

- Stride: `400 - 80 = 320` ký tự.
- Mỗi chunk dài tối đa 400 ký tự; hai chunk liền kề chia sẻ tối đa 80 ký tự.
- Giữ nguyên corpus, `benchmarks.json`, 5 query, gold answer, evidence phrase, filter và `top_k=3`.
- Kết quả chính thức được tạo bởi `bench.py`, không dùng runner riêng cho strategy này.

Embedding backend của benchmark chung là OpenAI; không có local/mock fallback trong kết quả chính thức.

## 5. Kết quả pipeline

Pipeline đã chạy với `FixedSizeChunker(400, 80)` trên đúng corpus và tạo **28 chunks**. Kết quả chi tiết nằm trong [fixed_size_results.json](/Users/alvinluong/K3-Day07-Data-Foundations/2A202601223/benchmark/fixed_size_results.json) và output tổng hợp nằm trong [benchmark_results.json](/Users/alvinluong/K3-Day07-Data-Foundations/benchmark_results.json).

| Query | Top-1 chunk | Semantic score | Evidence rank | Score (0/1/2) |
|---|---|---:|---:|---:|
| q1 | `course-registration-student::chunk_3` | 0.650069 | 1 | 1 |
| q2 | `scholarship-policy::chunk_3` | 0.640405 | 1 | 2 |
| q3 | `library-services::chunk_0` | 0.709361 | — | 0 |
| q4 | `scholarship-policy::chunk_1` | 0.677483 | 2 | 1 |
| q5 | `course-registration-student::chunk_2` | 0.696337 | 1 | 2 |

### Nội dung 5 query và đánh giá

1. **q1:** Evidence ở top-1 nhưng agent quote dùng `...`, nên chỉ đạt 1 điểm theo cùng grounding check.
2. **q2:** Evidence ở top-1 và agent trả lời đúng, đạt 2 điểm.
3. **q3:** Exact evidence phrase không nằm trọn trong một chunk 400, đạt 0 điểm dù agent có thể tóm tắt quy trình.
4. **q4:** Evidence nằm ở rank 2, đạt 1 điểm.
5. **q5:** Evidence ở top-1 và agent grounded, đạt 2 điểm.

## 6. Phân tích overlap và failure case

Overlap 80 ký tự giúp giữ thêm ngữ cảnh ở biên chunk và có thể giúp evidence ngắn không bị mất hoàn toàn. Tuy nhiên overlap không bảo đảm một evidence phrase dài sẽ nằm trong một chunk.

Failure case quan sát được ở **q3**: quy trình sử dụng phòng đọc có 4 bước, nhưng do chiều dài vượt quá 400 ký tự nên bị cắt giữa bước 4, khiến evidence không nằm trọn trong một chunk. Đây là failure mode cụ thể của fixed-size chunking: cắt giữa câu làm mất tính liên kết coherence; hoàn toàn có thể khắc phục bằng RecursiveChunker.

## 7. Filter A/B

Đã ghi cả hai nhánh trong JSON cho q5 (có áp dụng `audience: student`). Trong run này top-3 trước và sau filter giống nhau vì các chunk `audience=student` vốn đã đứng đầu; ở Recursive, filter mới loại được một faculty chunk khỏi top-3.

## 8. Điểm và giới hạn

**Tổng điểm retrieval:** **6/10**: 4/5 evidence trong top-3, 3/5 ở top-1, agent grounded 3/5.

**Giới hạn quan sát được:** q3 bị cắt giữa các chunk nên exact evidence không được tính; q4 tìm được evidence nhưng ở rank 2. Đây là failure cụ thể của fixed-size chunking.

## 9. File kết quả

- `bench.py` — runner chung của nhóm.
- [fixed_size_results.json](/Users/alvinluong/K3-Day07-Data-Foundations/2A202601223/benchmark/fixed_size_results.json)
- [benchmark_results.json](/Users/alvinluong/K3-Day07-Data-Foundations/benchmark_results.json)
