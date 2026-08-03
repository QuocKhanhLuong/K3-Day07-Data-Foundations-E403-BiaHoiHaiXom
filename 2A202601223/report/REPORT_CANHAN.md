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

Pipeline đã chạy với `FixedSizeChunker(400, 80)` trên đúng corpus và tạo **33 chunks**. Kết quả chi tiết, gồm top-3, filter A/B, evidence hit, rank của gold chunk và preview nội dung, nằm trong [fixed_size_results.json](/D:/GIT/K3-Day07-Data-Foundations/2A202601223/benchmark/fixed_size_results.json).

| Query | Top-1 của mock pipeline | Mock score* | Evidence trong top-3 | Gold chunk rank |
|---|---|---:|---|---:|
| q1 | `course-equivalency-policy::chunk_0` | 0.19005149 | Không | 2 |
| q2 | `scholarship-policy::chunk_0` | 0.22888288 | Không | 1 |
| q3 | `course-registration-student::chunk_2` | 0.22926551 | Không | — |
| q4 | `course-registration-student::chunk_4` | 0.38452980 | Không | 3 |
| q5 | `tuition-policy::chunk_0` | 0.23117919 | Không | — |

\* Đây là score của mock deterministic backend, chỉ để kiểm tra pipeline và **không dùng để chấm retrieval**. Agent cũng chỉ trả về demo preview, không phải câu trả lời grounded hoàn chỉnh.

### Nội dung 5 query và đánh giá

1. **q1:** Sinh viên bị cảnh cáo học tập mức 1 được đăng ký tối đa bao nhiêu tín chỉ? Gold answer là tối đa 14 tín chỉ. Mock top-3 không chứa evidence đầy đủ; chưa chấm semantic.
2. **q2:** Học bổng loại A yêu cầu GPA từ 3.6 và điểm rèn luyện từ 90. Gold chunk đứng hạng 1 theo mock nhưng evidence phrase đầy đủ không xuất hiện trong chunk; chưa chấm semantic.
3. **q3:** Sách giáo trình được mượn 30 ngày và gia hạn 01 lần thêm 15 ngày. Evidence bị chia qua ranh giới chunk 2/3; chưa chấm semantic.
4. **q4:** Các đối tượng được miễn 100% học phí gồm con người có công, mồ côi cả cha mẹ, người khuyết tật nặng/đặc biệt nặng và dân tộc thiểu số thuộc hộ nghèo/cận nghèo. Mock không đưa đủ evidence vào top-3; chưa chấm semantic.
5. **q5:** Quy trình phê duyệt gồm Trưởng bộ môn lập danh mục, Trưởng Khoa/Viện ký duyệt và Trưởng Phòng Đào tạo ra quyết định. Mock không đưa gold chunk vào top-3; chưa chấm semantic.

## 6. Phân tích overlap và failure case

Overlap 80 ký tự giúp giữ thêm ngữ cảnh ở biên chunk và có thể giúp evidence ngắn không bị mất hoàn toàn. Tuy nhiên, nó cũng làm tăng dữ liệu trùng lặp; nếu hai chunk liền kề cùng lọt top-3 thì diversity giảm. Trong lần mock pipeline này không có cặp chunk liền kề nào cùng nằm trong top-3.

Failure case quan sát được ở **q3**: nội dung sách giáo trình nằm tại `library-services.md`, nhưng câu dài bị cắt giữa chunk 2 và chunk 3. Chunk 2 kết thúc ở phần “nếu không có độc giả khác đặt mượn”, còn chunk 3 bắt đầu bằng “01 lần với thời gian gia hạn thêm là 15 ngày”. Vì vậy evidence phrase đầy đủ không nằm trọn trong một chunk. Đây là failure mode cụ thể của fixed-size chunking: cắt giữa câu làm mất coherence; có thể cải thiện bằng sentence/recursive chunking hoặc tăng chunk size, nhưng không thay đổi tham số trong benchmark hiện tại.

## 7. Filter A/B

Đã ghi cả hai nhánh trong JSON cho q1, q2 và q5:

- A: `store.search(query, top_k=3)`.
- B: `store.search_with_filter(query, top_k=3, metadata_filter=...)` với audience tương ứng.

Do chỉ có mock backend, A/B hiện là kiểm tra cấu trúc filter và metadata, chưa đủ cơ sở kết luận filter cải thiện recall hay giảm nhầm lẫn semantic.

## 8. Điểm và giới hạn

**Tổng điểm retrieval:** N/A. Cần chạy lại sau khi cài thành công local embedder cùng model đã chỉ định; không dùng mock score để thay thế.

**Giới hạn môi trường:** dependency `sentence-transformers` và model local chưa khả dụng; pytest cũng chưa được cài trong Python environment hiện tại. Không sửa source code để vượt qua giới hạn này.

## 9. File kết quả

- [run_fixed_size_benchmark.py](/D:/GIT/K3-Day07-Data-Foundations/2A202601223/benchmark/run_fixed_size_benchmark.py)
- [fixed_size_results.json](/D:/GIT/K3-Day07-Data-Foundations/2A202601223/benchmark/fixed_size_results.json)
- [FIXED_SIZE_SUMMARY.md](/D:/GIT/K3-Day07-Data-Foundations/2A202601223/benchmark/FIXED_SIZE_SUMMARY.md)
