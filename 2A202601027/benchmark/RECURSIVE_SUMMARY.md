# Benchmark Summary — RecursiveChunker Strategy

**Student:** Nguyễn Thu Huyền  
**MSSV:** 2A20261027  
**Strategy:** RecursiveChunker  
**Parameters:** `chunk_size = 400` (Không có overlap giả)  
**Corpus:** `data/k3_university_services`  
**Embedding Backend:** Mock Embeddings Fallback (Limitation: Python 3.14 environment lacked prebuilt wheels for `sentence-transformers` during run; technical smoke test completed correctly without faking semantic scores).

---

## 1. Kết Quả Tổng Quan

- **Tổng số chunks indexed:** 40 chunks
- **Tổng điểm benchmark:** **2 / 10** (1/5 query đạt Evidence Hit)

| Query ID | Query Text | Gold Doc ID | Metadata Filter | Top-1 Chunk Doc ID | Evidence Hit | Score (0/1/2) |
|---|---|---|---|---|---|---|
| **Q1** | Sinh viên bị cảnh cáo học tập mức 1 được đăng ký tối đa bao nhiêu tín chỉ trong một học kỳ chính? | `course-registration-student` | `{"audience": "student"}` | `scholarship-policy::chunk_4` | False | 0 |
| **Q2** | Quy định điều kiện xét cấp học bổng khuyến khích học tập loại A (Xuất sắc)... | `scholarship-policy` | `{"audience": "student"}` | `course-registration-student::chunk_5` | False | 0 |
| **Q3** | Hạn mượn tối đa đối với sách giáo trình dành cho sinh viên tại thư viện... | `library-services` | None | `dormitory-regulations::chunk_3` | False | 0 |
| **Q4** | Sinh viên thuộc các đối tượng chính sách nào được miễn 100% học phí... | `tuition-policy` | None | `dormitory-regulations::chunk_3` | False | 0 |
| **Q5** | Thẩm quyền và quy trình phê duyệt danh mục học phần tương đương... | `course-equivalency-policy` | `{"audience": "faculty"}` | `course-registration-faculty::chunk_1` | True (Rank 2) | 2 |

---

## 2. Điểm Mạnh & Điểm Yếu Của Strategy

### Điểm mạnh:
- Tách văn bản thông minh theo ranh giới tự nhiên (`\n\n`, `\n`, `. `, ` `), giữ trọn vẹn ý nghĩa của từng đoạn văn bản và tiêu đề thay vì cắt vụn giữa từ.
- Tạo ra 40 chunks có độ dài đồng đều và liền mạch theo cấu trúc section của tài liệu Markdown.

### Điểm yếu:
- Không có cơ chế overlap giữa các chunk lân cận, khiến các câu điều kiện vắt ngang ranh giới bị chia rẽ.
- Với `chunk_size=400`, một số đoạn thông tin chi tiết (ví dụ: các mức quy định tín chỉ) bị đẩy sang chunk kế tiếp mà không có bối cảnh dẫn nhập.

---

## 3. Phân Tích A/B Filter (Metadata Filtering)

Với các query yêu cầu lọc theo `audience`:
- **Query Q1 (`audience: student`)**: Lọc bỏ các tài liệu quy trình dành riêng cho giảng viên (`course-registration-faculty`, `course-equivalency-policy`), thu hẹp tập ứng viên về sinh viên.
- **Query Q5 (`audience: faculty`)**: Tiền lọc loại bỏ toàn bộ tài liệu sinh viên (`student`), giúp chunk chứa bằng chứng chính xác `course-equivalency-policy::chunk_4` vươn lên vị trí Rank 2 và đạt **Evidence Hit** (Score 2/2).

---

## 4. Phân Tích Lỗi (Failure Case Analysis)

- **Query:** Q1 — "Sinh viên bị cảnh cáo học tập mức 1 được đăng ký tối đa bao nhiêu tín chỉ trong một học kỳ chính?"
- **Gold Doc:** `course-registration-student`
- **Expected Section:** `## 2. Quy định về khối lượng học tập tối thiểu và tối đa`
- **Evidence Phrase:** "Sinh viên bị cảnh cáo học tập mức 1: Khối lượng đăng ký tối đa không quá 14 tín chỉ trong một học kỳ chính."
- **Top-3 thực tế:**
  - Rank 1: `scholarship-policy::chunk_4` (Score 0.1899)
  - Rank 2: `course-registration-student::chunk_3` (Score 0.1720)
  - Rank 3: `tuition-policy::chunk_2` (Score 0.1664)
- **Agent Answer:** `[DEMO LLM] Answer generated from context preview...`
- **Gold Answer:** "Sinh viên bị cảnh cáo học tập mức 1 chỉ được đăng ký tối đa 14 tín chỉ trong một học kỳ chính."
- **Nguyên nhân thất bại:**
  1. Hạn chế môi trường: Chạy bằng `MockEmbedder` (fallback) do thiếu wheel `sentence-transformers` trên Python 3.14, dẫn đến điểm similarity không phản ánh chính xác tương quan ngữ nghĩa tiếng Việt.
  2. Ranh giới chunking: `RecursiveChunker` cắt theo kích thước 400 ký tự mà không có overlap, khiến câu chứa con số 14 tín chỉ bị phân mảnh khỏi tiêu đề phần 2.
- **Đề xuất cải thiện:**
  1. Sử dụng mô hình nhúng tiếng Việt chuẩn (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`).
  2. Bổ sung cơ chế overlap (ví dụ 50 ký tự) hoặc chunking theo tiêu đề Header Markdown.
