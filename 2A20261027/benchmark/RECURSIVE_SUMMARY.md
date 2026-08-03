# Benchmark Summary — RecursiveChunker Strategy

**Student:** Nguyễn Thu Huyền  
**MSSV:** 2A202601027  
**Strategy:** RecursiveChunker  
**Parameters:** `chunk_size = 400` (Không có overlap giả)  
**Corpus:** `data/k3_university_services`  
**Embedding Backend:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (Local Multilingual Embedder)

---

## 1. Kết Quả Tổng Quan

- **Tổng số chunks indexed:** 32 chunks
- **Tổng điểm benchmark:** **10 / 10** (5/5 query đạt Evidence Hit trong Top-3)

| Query ID | Query Text | Gold Doc ID | Metadata Filter | Top-1 Chunk Doc ID | Evidence Hit | Score (0/1/2) |
|---|---|---|---|---|---|---|
| **Q1** | Khối lượng đăng ký tối đa trong một học kỳ chính đối với người học không bị cảnh báo là bao nhiêu tín chỉ? | `course-registration-student` | None | `course-registration-student::chunk_4` | True (Rank 2) | 2 |
| **Q2** | Điều kiện GPA và điểm rèn luyện để đạt học bổng loại A là gì? | `scholarship-policy` | None | `scholarship-policy::chunk_3` | True (Rank 1) | 2 |
| **Q3** | Quy trình sử dụng phòng đọc tại chỗ gồm những bước nào? | `library-services` | None | `library-services::chunk_1` | True (Rank 2) | 2 |
| **Q4** | Học bổng KKHT có những mức nào và mức của từng loại được tính như thế nào so với loại khá? | `scholarship-policy` | None | `scholarship-policy::chunk_1` | True (Rank 2) | 2 |
| **Q5** | Khi cần điều chỉnh đăng ký học phần, người học có thể thực hiện những thao tác nào và trong thời điểm nào? | `course-registration-student` | `{"audience": "student"}` | `course-registration-student::chunk_1` | True (Rank 2) | 2 |

---

## 2. Điểm Mạnh & Điểm Yếu Của Strategy

### Điểm mạnh:
- **Bảo tồn cấu trúc ngữ cảnh tuyệt đối:** Phân chia văn bản thông minh theo ưu tiên ranh giới tự nhiên (`\n\n`, `\n`, `. `, ` `), giữ trọn vẹn ý nghĩa của tiêu đề section và các đoạn văn bản mà không bị rách vụn từ ngữ.
- **Hiệu năng truy xuất xuất sắc (10/10 điểm):** Đạt 100% Evidence Hit trên cả 5 query benchmark khi sử dụng mô hình nhúng multilingual embedder (`paraphrase-multilingual-MiniLM-L12-v2`).

### Điểm yếu:
- Không có cơ chế overlap giữa các chunk lân cận (`chunk_size=400`), do đó ở một số query (Q1, Q3, Q4, Q5), chunk chứa bằng chứng bị ngắt sang chunk kế tiếp và đứng ở vị trí Rank 2 thay vì Rank 1.

---

## 3. Phân Tích A/B Filter (Metadata Filtering)

- **Query Q5 (`audience: student`)**:
  - *Không filter:* Top-3 gồm các chunk liên quan đến quy trình đăng ký môn học của sinh viên.
  - *Có filter:* Loại bỏ tuyệt đối các tài liệu quy trình giảng viên (`course-registration-faculty`, `course-equivalency-policy`), đưa chunk bằng chứng `course-registration-student::chunk_2` đạt score 0.7378 lọt Top-2.
- **Kết luận:** Pre-filtering giúp nâng cao precision bằng cách khoanh vùng chính xác tập đối tượng độc giả trước khi thực hiện truy xuất tương đồng vector.

---

## 4. Phân Tích Lỗi & Điểm Cần Cải Thiện (Failure / Optimization Analysis)

- **Trường hợp tối ưu (Optimization Case):** Query Q1 — *"Khối lượng đăng ký tối đa trong một học kỳ chính đối với người học không bị cảnh báo là bao nhiêu tín chỉ?"*
- **Gold Doc:** `course-registration-student`
- **Actual Top-3:**
  - Rank 1: `course-registration-student::chunk_4` (Score 0.7156)
  - Rank 2: `course-registration-student::chunk_3` (Score 0.6833 - **Evidence Hit**)
  - Rank 3: `scholarship-policy::chunk_4` (Score 0.6638)
- **Phân tích:** `chunk_3` chứa câu trả lời chính xác ("tối đa 24 tín chỉ") lọt Top-2 đạt 2/2 điểm. Tuy nhiên Rank 1 thuộc về `chunk_4` do từ khóa "học kỳ chính" có tần suất xuất hiện cao ở chunk này.
- **Đề xuất cải thiện:**
  1. Thêm cơ chế overlap (ví dụ 50 ký tự) để liên kết câu điều kiện với tiêu đề mục.
  2. Kết hợp Hybrid Search (Vector + BM25 keyword search) để kéo chunk chứa chính xác từ khóa "24 tín chỉ" lên vị trí Rank 1.
