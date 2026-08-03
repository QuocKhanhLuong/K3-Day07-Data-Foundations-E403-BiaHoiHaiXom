# Benchmark Summary — RecursiveChunker Strategy

**Student:** Nguyễn Thu Huyền  
**MSSV:** 2A20261027  
**Strategy:** RecursiveChunker  
**Parameters:** `chunk_size = 400` (Không có overlap giả)  
**Corpus:** `data/k3_university_services`  
**Embedding Backend:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (Local Multilingual Embedder)

---

## 1. Kết Quả Tổng Quan

- **Tổng số chunks indexed:** 40 chunks
- **Tổng điểm benchmark:** **8 / 10** (4/5 query đạt Evidence Hit)

| Query ID | Query Text | Gold Doc ID | Metadata Filter | Top-1 Chunk Doc ID | Evidence Hit | Score (0/1/2) |
|---|---|---|---|---|---|---|
| **Q1** | Sinh viên bị cảnh cáo học tập mức 1 được đăng ký tối đa bao nhiêu tín chỉ trong một học kỳ chính? | `course-registration-student` | `{"audience": "student"}` | `course-registration-student::chunk_4` | True (Rank 1) | 2 |
| **Q2** | Quy định điều kiện xét cấp học bổng khuyến khích học tập loại A (Xuất sắc)... | `scholarship-policy` | `{"audience": "student"}` | `scholarship-policy::chunk_0` | True (Rank 2) | 2 |
| **Q3** | Hạn mượn tối đa đối với sách giáo trình dành cho sinh viên tại thư viện... | `library-services` | None | `library-services::chunk_3` | True (Rank 1) | 2 |
| **Q4** | Sinh viên thuộc các đối tượng chính sách nào được miễn 100% học phí... | `tuition-policy` | None | `tuition-policy::chunk_2` | False (Rank 1 doc) | 0 |
| **Q5** | Thẩm quyền và quy trình phê duyệt danh mục học phần tương đương... | `course-equivalency-policy` | `{"audience": "faculty"}` | `course-equivalency-policy::chunk_4` | True (Rank 1) | 2 |

---

## 2. Điểm Mạnh & Điểm Yếu Của Strategy

### Điểm mạnh:
- Khả năng bảo tồn cấu trúc tự nhiên: Tách văn bản thông minh theo thứ tự dấu phân cách (`\n\n`, `\n`, `. `, ` `), giữ vẹn toàn cấu trúc đoạn văn và câu mà không làm rách vụn từ ngữ.
- Độ chính xác truy xuất cao khi đi kèm Local Multilingual Embedder: Đạt 4/5 Evidence Hit với 3 query lọt Top-1 đúng chunk chứa bằng chứng (`q1`, `q3`, `q5`).

### Điểm yếu:
- Không có cơ chế overlap giữa các chunk lân cận (`chunk_size=400`), làm cho các đoạn danh sách liệt kê chi tiết (như danh sách các đối tượng miễn học phí ở Q4) bị trôi sang chunk tiếp theo mà không giữ được bối cảnh tiêu đề.

---

## 3. Phân Tích A/B Filter (Metadata Filtering)

- **Query Q1 (`audience: student`)**: Lọc bỏ toàn bộ tài liệu giảng viên (`course-registration-faculty`, `course-equivalency-policy`), đưa chunk chính xác `course-registration-student::chunk_4` lên vị trí Rank 1 với score **0.8415**.
- **Query Q5 (`audience: faculty`)**: Tiền lọc loại bỏ toàn bộ tài liệu sinh viên (`student`), giúp `course-equivalency-policy::chunk_4` chiếm giữ vị trí Rank 1 với score **0.7683** (đạt 2/2 điểm).
- **Kết luận:** Pre-filtering giúp tăng precision tuyệt đối bằng cách loại bỏ các tài liệu nhiễu thuộc đối tượng khác, đảm bảo recall không bị ảnh hưởng.

---

## 4. Phân Tích Lỗi (Failure Case Analysis)

- **Query:** Q4 — *"Sinh viên thuộc các đối tượng chính sách nào được miễn 100% học phí theo quy định hiện hành của nhà trường?"*
- **Gold Doc:** `tuition-policy`
- **Expected Section:** `## 3. Các đối tượng sinh viên được miễn 100% học phí`
- **Evidence Phrase:** *"Sinh viên thuộc các đối tượng sau đây được hưởng chính sách miễn 100% học phí: Sinh viên là con của người có công với cách mạng... Sinh viên mồ côi cả cha lẫn mẹ... Sinh viên bị khuyết tật nặng hoặc đặc biệt nặng... Sinh viên là người dân tộc thiểu số thuộc hộ nghèo hoặc hộ cận nghèo."*
- **Top-3 thực tế:**
  - Rank 1: `tuition-policy::chunk_2` (Score 0.8253)
  - Rank 2: `tuition-policy::chunk_0` (Score 0.6973)
  - Rank 3: `tuition-policy::chunk_1` (Score 0.6381)
- **Agent Answer:** `[DEMO LLM] Answer generated from context preview...`
- **Gold Answer:** *"Sinh viên là con của người có công với cách mạng; sinh viên mồ côi cả cha lẫn mẹ; sinh viên bị khuyết tật nặng/đặc biệt nặng; và sinh viên dân tộc thiểu số thuộc hộ nghèo hoặc hộ cận nghèo."*
- **Nguyên nhân thất bại:**
  `RecursiveChunker(chunk_size=400)` ngắt tại ranh giới 400 ký tự mà không có overlap. Tiêu đề Mục 3 nằm ở cuối `chunk_2`, trong khi danh sách liệt kê 4 đối tượng hưởng chính sách rơi vào `chunk_3`. Do query có chứa cụm từ "học phí", `chunk_2` (nói chung về quy định học phí) đạt similarity 0.8253 cao hơn `chunk_3`, làm `chunk_3` trôi khỏi Top-3.
- **Đề xuất cải thiện:**
  1. Thêm cơ chế overlap (ví dụ `overlap_size=50-100`) trong `RecursiveChunker`.
  2. Áp dụng Markdown Header Chunking để gom tiêu đề Section cùng toàn bộ danh sách liệt kê bên dưới vào chung một chunk.
