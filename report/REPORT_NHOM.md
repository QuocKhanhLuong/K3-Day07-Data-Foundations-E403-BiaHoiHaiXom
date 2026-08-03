# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** BiaHoiHaiXom  
**Thành viên:**  
1. Lương Quốc Khánh (MSSV: 2A20261713)  
2. Hoàng Đức Anh (MSSV: 2A202601223)  
3. Trần Nguyễn Mỹ Anh (MSSV: 2A20261019)  
4. Nguyễn Thu Huyền (MSSV: 2A20261027)  
**Ngày:** 2026-08-03

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K3):** Dịch vụ / quy định đại học (đăng ký môn, học phí, học bổng, thư viện, ký túc xá…).

**Phạm vi cụ thể nhóm tập trung:**
> Bộ tài liệu tập trung vào các dịch vụ & quy định cốt lõi của sinh viên và giảng viên bao gồm: quy định đăng ký học phần & giới hạn tín chỉ, quy định học bổng khuyến khích học tập, chính sách miễn giảm học phí, quy định mượn trả tài liệu thư viện, nội quy ký túc xá và quy định chuyển đổi học phần tương đương/thay thế.

### Danh sách tài liệu (Data Inventory)

Tất cả tài liệu được lưu trong thư mục `data/k3_university_services/` và kê khai khớp 1-1 trong `data/k3_university_services/sources.csv`:

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Quy định về đăng ký học phần và khối lượng học tập dành cho sinh viên (`course-registration-student.md`) | https://ctt.hust.edu.vn/Display/DisplayMNews?NewsID=582 | 2026-08-03 / not-stated | ~1.600 | `doc_id`, `audience: student`, `category: hoc-vu`, `department: phong-dao-tao`, `language: vi` |
| 2 | Quy định về tư vấn và phê duyệt kế hoạch học tập dành cho Giảng viên và Cố vấn học tập (`course-registration-faculty.md`) | https://ctt.hust.edu.vn/Display/DisplayMNews?NewsID=789 | 2026-08-03 / not-stated | ~1.400 | `doc_id`, `audience: faculty`, `category: hoc-vu`, `department: phong-dao-tao`, `language: vi` |
| 3 | Quy định về mức thu học phí, thời hạn nộp và chính sách miễn giảm học phí (`tuition-policy.md`) | https://ctt.hust.edu.vn/Display/DisplayMNews?NewsID=1205 | 2026-08-03 / not-stated | ~1.800 | `doc_id`, `audience: student`, `category: hoc-phi`, `department: phong-tai-chinh-ke-toan`, `language: vi` |
| 4 | Quy định về xét cấp học bổng khuyến khích học tập dành cho sinh viên (`scholarship-policy.md`) | https://ctt.hust.edu.vn/Display/DisplayMNews?NewsID=1204 | 2026-08-03 / not-stated | ~1.900 | `doc_id`, `audience: student`, `category: hoc-bong`, `department: phong-cong-tac-sinh-vien`, `language: vi` |
| 5 | Quy định sử dụng dịch vụ thư viện và quy tắc mượn trả tài liệu (`library-services.md`) | https://library.hust.edu.vn/quy-dinh-su-dung-thu-vien | 2026-08-03 / not-stated | ~1.700 | `doc_id`, `audience: all`, `category: thu-vien`, `department: trung-tam-tri-thuc-so`, `language: vi` |
| 6 | Nội quy quản lý và quy định lưu trú Ký túc xá sinh viên (`dormitory-regulations.md`) | https://ktx.hust.edu.vn/noi-quy-ky-tuc-xa | 2026-08-03 / not-stated | ~1.700 | `doc_id`, `audience: student`, `category: ky-tuc-xa`, `department: ban-quan-ly-ky-tuc-xa`, `language: vi` |
| 7 | Quy định về học phần tương đương và học phần thay thế (`course-equivalency-policy.md`) | https://ctt.hust.edu.vn/Display/DisplayMNews?NewsID=789 | 2026-08-03 / not-stated | ~1.500 | `doc_id`, `audience: faculty`, `category: hoc-vu`, `department: phong-dao-tao`, `language: vi` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `course-registration-student` | Định danh duy nhất tài liệu nguồn, phục vụ quản lý và truy vết nguồn gốc chunk. |
| `audience` | string | `student`, `faculty`, `all` | Lọc kết quả theo đối tượng (ví dụ: phân biệt quy định đăng ký môn dành riêng cho sinh viên vs quy định duyệt cho giảng viên). |
| `category` | string | `hoc-vu`, `hoc-bong`, `hoc-phi`, `thu-vien`, `ky-tuc-xa` | Giúp lọc nhanh phân vùng nghiệp vụ đại học, loại bỏ hoàn toàn nhiễu từ phân vùng khác. |
| `department` | string | `phong-dao-tao`, `phong-cong-tac-sinh-vien`, `phong-tai-chinh-ke-toan` | Phân loại theo đơn vị ban hành và quản lý quy định. |
| `source_url` | string | `https://ctt.hust.edu.vn/...` | Lưu liên kết tới nguồn công khai chính thức để xác minh thông tin. |
| `retrieved_at` | string | `2026-08-03` | Lưu ngày thu thập để quản lý tính cập nhật của tri thức. |
| `document_version` | string | `not-stated` | Lưu phiên bản văn bản quy định hoặc đánh dấu `not-stated` khi không ghi rõ. |
| `language` | string | `vi` | Phân loại ngôn ngữ của văn bản. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Lương Quốc Khánh**
- **Loại chiến lược:**
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — Hoàng Đức Anh**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — Trần Nguyễn Mỹ Anh**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 4 — Nguyễn Thu Huyền**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Sinh viên bị cảnh cáo học tập mức 1 được đăng ký tối đa bao nhiêu tín chỉ trong một học kỳ chính? | Sinh viên bị cảnh cáo học tập mức 1 chỉ được đăng ký tối đa 14 tín chỉ trong một học kỳ chính. | `course-registration-student` (Mục 2: Khối lượng học tập tối thiểu và tối đa) |
| 2 | Quy định điều kiện xét cấp học bổng khuyến khích học tập loại A (Xuất sắc) dành cho sinh viên bao gồm những tiêu chuẩn gì về GPA và điểm rèn luyện? | HB KKHT loại A (Xuất sắc) yêu cầu sinh viên có GPA đạt từ 3.6 trở lên (thang 4) và điểm rèn luyện đạt từ 90 điểm trở lên (thang 100). | `scholarship-policy` (Mục 2: Tiêu chuẩn và phân loại mức học bổng — lọc `audience: student`) |
| 3 | Hạn mượn tối đa đối với sách giáo trình dành cho sinh viên tại thư viện là bao nhiêu ngày và được gia hạn mấy lần? | Sách giáo trình được mượn tối đa 5 cuốn trong thời hạn 30 ngày và được gia hạn 01 lần với thời gian gia hạn thêm là 15 ngày nếu không có độc giả khác đặt trước. | `library-services` (Mục 3: Thời hạn mượn và quy định gia hạn tài liệu) |
| 4 | Sinh viên thuộc các đối tượng chính sách nào được miễn 100% học phí theo quy định hiện hành? | Sinh viên là con người có công cách mạng; sinh viên mồ côi cả cha lẫn mẹ; sinh viên khuyết tật nặng/đặc biệt nặng; và sinh viên dân tộc thiểu số hộ nghèo/cận nghèo. | `tuition-policy` (Mục 3: Các đối tượng sinh viên được miễn 100% học phí) |
| 5 | Thẩm quyền và quy trình phê duyệt danh mục học phần tương đương hoặc học phần thay thế dành cho giảng viên/cố vấn học tập được thực hiện qua các cấp nào? | Quy trình gồm 3 cấp: Trưởng bộ môn chuyên môn lập danh mục đề xuất, Trưởng Khoa/Viện ký duyệt hồ sơ thẩm định, và Trưởng Phòng Đào tạo ra quyết định công nhận chính thức. | `course-equivalency-policy` (Mục 3: Quy trình và thẩm quyền phê duyệt — lọc `audience: faculty`) |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
