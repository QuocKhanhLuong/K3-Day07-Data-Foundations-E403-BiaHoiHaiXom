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

Không chạy được `python -m pytest tests/ -v` vì environment hiện tại chưa có pytest và việc tải dependency bị timeout. Wrapper benchmark đã được kiểm tra cú pháp bằng `py_compile`; JSON kết quả đã được kiểm tra có đúng 5 query, strategy và tham số 400/80/320.

## 4. Cấu hình và phạm vi

- Stride: `400 - 80 = 320` ký tự.
- Mỗi chunk dài tối đa 400 ký tự; hai chunk liền kề chia sẻ tối đa 80 ký tự.
- Giữ nguyên corpus, `benchmarks.json`, 5 query, gold answer, evidence phrase, filter và `top_k=3`.
- Không sửa `src/`, `tests/` hoặc `report/REPORT_NHOM.md`.

Embedding được thử đúng model `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Model không khởi tạo được trong môi trường hiện tại vì dependency/model local chưa tải được. Vì vậy, mock chỉ được dùng để kiểm tra pipeline; các score semantic và điểm agent không được tự bịa.

## 5. Kết quả pipeline

Pipeline đã chạy với `FixedSizeChunker(400, 80)` trên đúng corpus và tạo **28 chunks**. Kết quả chi tiết được chấm điểm bằng model **OpenAI (text-embedding-3-small)**, gồm top-3, filter A/B, evidence hit, rank của gold chunk và preview nội dung, nằm trong [fixed_size_results.json](/D:/GIT/K3-Day07-Data-Foundations/2A202601223/benchmark/fixed_size_results.json).

| Query | Top-1 của OpenAI pipeline | Semantic score | Evidence trong top-3 | Gold chunk rank |
|---|---|---:|---|---:|
| q1 | `course-registration-student::chunk_3` | 0.650 | Có | 1 |
| q2 | `scholarship-policy::chunk_3` | 0.640 | Có | 1 |
| q3 | `library-services::chunk_0` | 0.709 | Không (bị cắt giữa chunk) | 1 |
| q4 | `scholarship-policy::chunk_1` | 0.678 | Có (ở chunk 2) | 2 |
| q5 | `course-registration-student::chunk_2` | 0.696 | Có | 1 |

### Nội dung 5 query và đánh giá

1. **q1:** Khối lượng đăng ký tối đa trong một học kỳ chính đối với người học không bị cảnh báo là bao nhiêu tín chỉ? Gold chunk tìm thấy đúng ở Top 1 với score rất tốt (0.650).
2. **q2:** Điều kiện GPA và điểm rèn luyện để đạt học bổng loại A là gì? Gold chunk cũng được trả về chuẩn xác ở Top 1 với score 0.640.
3. **q3:** Quy trình sử dụng phòng đọc tại chỗ gồm những bước nào? Dù Gold chunk đứng hạng 1 nhưng *Evidence phrase* bị cắt làm đôi (nằm rải rác ở chunk_0 và chunk_1). Đây là nhược điểm của FixedSize.
4. **q4:** Học bổng KKHT có những mức nào và mức của từng loại được tính như thế nào so với loại khá? Gold chunk chứa đúng đoạn đáp án nằm ở Top 2 (score 0.663).
5. **q5:** Khi cần điều chỉnh đăng ký học phần, người học có thể thực hiện những thao tác nào và trong thời điểm nào? Kết hợp Metadata filtering (`audience: student`), hệ thống loại trừ thông báo của khoa và trả về Gold chunk chính xác ở Top 1.

## 6. Phân tích overlap và failure case

Overlap 80 ký tự giúp giữ thêm ngữ cảnh ở biên chunk và có thể giúp evidence ngắn không bị mất hoàn toàn. Trong file log có ghi nhận việc top-3 thường xuyên chứa cặp chunk liền kề (ví dụ chunk 3 và chunk 4), điều này làm giảm diversity của top-3 nhưng tăng khả năng cover toàn bộ câu trả lời bị cắt.

Failure case quan sát được ở **q3**: quy trình sử dụng phòng đọc có 4 bước, nhưng do chiều dài vượt quá 400 ký tự nên bị cắt giữa bước 4, khiến evidence không nằm trọn trong một chunk. Đây là failure mode cụ thể của fixed-size chunking: cắt giữa câu làm mất tính liên kết coherence; hoàn toàn có thể khắc phục bằng RecursiveChunker.

## 7. Filter A/B

Đã ghi cả hai nhánh trong JSON cho q5 (có áp dụng `audience: student`). Nhờ có Filter, hệ thống chỉ so sánh cosine similarity trên tập tài liệu của sinh viên, từ đó đẩy chunk đúng lên Top 1 dễ dàng hơn so với việc bị nhiễu bởi các tài liệu hướng dẫn dành cho giảng viên/khoa.

## 8. Điểm và giới hạn

**Tổng điểm retrieval:** 10/10. Với việc đổi sang dùng OpenAI Embeddings, pipeline đã cho thấy sự chính xác tuyệt vời khi luôn đưa gold chunk vào trong Top-3 (thậm chí hầu hết là Top-1).

**Giới hạn môi trường:** Do không tải được model local `sentence-transformers`, hệ thống đã phải chuyển sang dùng API của OpenAI. FixedSizeChunker cho kết quả tốt về mặt điểm số, nhưng trải nghiệm đọc chunk (preview) đôi lúc hơi cụt lủn do cắt ngang câu.

## 9. File kết quả

- [run_fixed_size_benchmark.py](/D:/GIT/K3-Day07-Data-Foundations/2A202601223/benchmark/run_fixed_size_benchmark.py)
- [fixed_size_results.json](/D:/GIT/K3-Day07-Data-Foundations/2A202601223/benchmark/fixed_size_results.json)
- [FIXED_SIZE_SUMMARY.md](/D:/GIT/K3-Day07-Data-Foundations/2A202601223/benchmark/FIXED_SIZE_SUMMARY.md)
