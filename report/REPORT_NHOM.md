# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** BiaHoiHaiXom  
**Thành viên:**  
1. Lương Quốc Khánh (MSSV: 2A202601713)
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
> Bộ tài liệu tập trung vào các dịch vụ & quy định cốt lõi của sinh viên và giảng viên bao gồm: quy định đăng ký học tập & giới hạn tín chỉ, thông báo học phí, quy định học bổng khuyến khích học tập, quy trình sử dụng phòng đọc, hướng dẫn đăng ký phòng ký túc xá và quy định về học phần tương đương/thay thế.

### Danh sách tài liệu (Data Inventory)

Tất cả tài liệu được lưu trong thư mục `data/k3_university_services/` và kê khai khớp 1-1 trong `data/k3_university_services/sources.csv`:

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Quy chế đào tạo — đăng ký học tập chương trình đại học (`course-registration-student.md`) | https://ctt.hust.edu.vn/Upload/Nguy%E1%BB%85n%20Qu%E1%BB%91c%20%C4%90%E1%BA%A1t/files/DTDH_QDQC/Hoctap/QCDT_2025_5445_QD-DHBK.pdf | 2026-08-03 / 2025 | 1.659 | `doc_id`, `audience: student`, `category: hoc-vu`, `department: ban-dao-tao`, `language: vi` |
| 2 | Thông báo cập nhật đăng ký học tập chương trình đào tạo ngành Công nghệ giáo dục (`course-registration-faculty.md`) | https://fed.hust.edu.vn/vi/news/tin-tuc/thong-bao-cap-nhat-dang-ky-hoc-tap-chuong-trinh-dao-tao-nganh-cong-nghe-giao-duc-302797.html | 2026-08-03 / not-stated | 820 | `doc_id`, `audience: faculty`, `category: hoc-vu`, `department: khoa-kh-cn-giao-duc`, `language: vi` |
| 3 | Thông báo về học phí kỳ I năm học 2025-2026 (20251) - đợt 2 (`tuition-policy.md`) | https://ctt.hust.edu.vn/DisplayWeb/DisplayKehoach?kehoach=27231 | 2026-08-03 / 2025-2026 | 1.096 | `doc_id`, `audience: student`, `category: hoc-phi`, `department: ban-dao-tao`, `language: vi` |
| 4 | Quy định về việc xét cấp học bổng khuyến khích học tập tại Trường Đại học Bách khoa Hà Nội (`scholarship-policy.md`) | https://ctt.hust.edu.vn/Upload/Nguyen%20Viet%20Tien/files/Quy%20%C4%91%E1%BB%8Bnh%20v%E1%BB%81%20vi%E1%BB%87c%20x%C3%A9t%20c%E1%BA%A5p%20HB%20KKHT.pdf | 2026-08-03 / 2020-11-30 | 1.549 | `doc_id`, `audience: student`, `category: hoc-bong`, `department: phong-cong-tac-sinh-vien`, `language: vi` |
| 5 | Quy trình sử dụng phòng đọc (`library-services.md`) | https://library.hust.edu.vn/vi/node/471 | 2026-08-03 / not-stated | 964 | `doc_id`, `audience: all`, `category: thu-vien`, `department: trung-tam-truyen-thong-va-tri-thuc-so`, `language: vi` |
| 6 | Hướng dẫn đăng ký phòng (`dormitory-regulations.md`) | https://ktx.hust.edu.vn/huong-dan-dang-ky-phong | 2026-08-03 / not-stated | 1.259 | `doc_id`, `audience: student`, `category: ky-tuc-xa`, `department: trung-tam-dich-vu-va-ho-tro-bach-khoa`, `language: vi` |
| 7 | Quy chế đào tạo — học phần tương đương và học phần thay thế (`course-equivalency-policy.md`) | https://ctt.hust.edu.vn/Upload/Nguy%E1%BB%85n%20Qu%E1%BB%91c%20%C4%90%E1%BA%A1t/files/DTDH_QDQC/Hoctap/QCDT_2025_5445_QD-DHBK.pdf | 2026-08-03 / 2025 | 1.360 | `doc_id`, `audience: all`, `category: hoc-vu`, `department: ban-dao-tao`, `language: vi` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Corpus có 7 tài liệu Markdown, nằm trong giới hạn 5–10 tài liệu của CP2.
- [x] Mỗi tài liệu dùng một trang/PDF công khai trên domain chính thức của HUST; nội dung chép vào corpus không gồm tài khoản, mật khẩu, email mẫu, số điện thoại hay hồ sơ cá nhân.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version`, `audience`, `category`, `department` và `language` trong front matter.
- [x] `sources.csv` có đúng một dòng cho mỗi Markdown; `doc_id`, đường dẫn, tiêu đề, URL, ngày lấy và phiên bản đã được đối chiếu với front matter.
- [x] Corpus có ba audience (`student`, `faculty`, `all`) và cặp cùng chủ đề `course-registration-student`/`course-registration-faculty` có nội dung khác nhau theo vai trò.
- [x] Năm benchmark có đủ section và evidence phrase liên tục; validator tạm kiểm tra sau khi chuẩn hóa whitespace và Markdown bold.

### Audit nguồn

Các URL dưới đây đã được mở/đối chiếu ngày 2026-08-03. Những URL `NewsID` và đường dẫn cũ không chứng minh được nội dung tương ứng đã được thay bằng nguồn chính thức phù hợp; không giữ lại số liệu chưa xác minh.

1. `course-registration-student` — [Quy chế đào tạo 2025](https://ctt.hust.edu.vn/Upload/Nguy%E1%BB%85n%20Qu%E1%BB%91c%20%C4%90%E1%BA%A1t/files/DTDH_QDQC/Hoctap/QCDT_2025_5445_QD-DHBK.pdf) — đã thay `NewsID=582`; đối chiếu được ba giai đoạn đăng ký, giới hạn 24/12 TC và điều chỉnh đăng ký.
2. `course-registration-faculty` — [Thông báo của Khoa KH & CN Giáo dục](https://fed.hust.edu.vn/vi/news/tin-tuc/thong-bao-cap-nhat-dang-ky-hoc-tap-chuong-trinh-dao-tao-nganh-cong-nghe-giao-duc-302797.html) — đã thay `NewsID=789`; nội dung tập trung vào cập nhật điều kiện học phần và trách nhiệm phối hợp thông báo của CVHT/cán bộ quản lý lớp.
3. `tuition-policy` — [Thông báo học phí kỳ I 2025-2026 đợt 2](https://ctt.hust.edu.vn/DisplayWeb/DisplayKehoach?kehoach=27231) — đã thay `NewsID=1205`; chỉ giữ hướng dẫn tra cứu, hai đợt tính học phí, thanh toán và xử lý nghĩa vụ chưa hoàn thành.
4. `scholarship-policy` — [Quy định xét cấp HB KKHT](https://ctt.hust.edu.vn/Upload/Nguyen%20Viet%20Tien/files/Quy%20%C4%91%E1%BB%8Bnh%20v%E1%BB%81%20vi%E1%BB%87c%20x%C3%A9t%20c%E1%BA%A5p%20HB%20KKHT.pdf) — đã thay `NewsID=1204`; đối chiếu được quỹ 8%, ba mức học bổng và ngưỡng GPA/điểm rèn luyện.
5. `library-services` — [Quy trình sử dụng phòng đọc](https://library.hust.edu.vn/vi/node/471) — đã thay đường dẫn quy định cũ; đối chiếu được bốn bước sử dụng phòng đọc và các lưu ý tại chỗ.
6. `dormitory-regulations` — [Hướng dẫn đăng ký phòng](https://ktx.hust.edu.vn/huong-dan-dang-ky-phong) — đã thay đường dẫn nội quy cũ; chỉ giữ quy trình đăng nhập, chọn phòng, giữ phòng 15 phút, thanh toán QR và các lưu ý thanh toán.
7. `course-equivalency-policy` — [Quy chế đào tạo 2025](https://ctt.hust.edu.vn/Upload/Nguy%E1%BB%85n%20Qu%E1%BB%91c%20%C4%90%E1%BA%A1t/files/DTDH_QDQC/Hoctap/QCDT_2025_5445_QD-DHBK.pdf) — đã thay `NewsID=789`; PDF này thật sự có riêng phần học phần tương đương/thay thế nên được dùng chung URL với tài liệu đăng ký học tập, không phải với tài liệu faculty.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `course-registration-student` | Định danh duy nhất tài liệu nguồn, phục vụ quản lý và truy vết nguồn gốc chunk. |
| `audience` | string | `student`, `faculty`, `all` | Lọc kết quả theo đối tượng (ví dụ: phân biệt quy định đăng ký môn dành riêng cho sinh viên vs quy định duyệt cho giảng viên). |
| `category` | string | `hoc-vu`, `hoc-bong`, `hoc-phi`, `thu-vien`, `ky-tuc-xa` | Giúp lọc nhanh phân vùng nghiệp vụ đại học, loại bỏ hoàn toàn nhiễu từ phân vùng khác. |
| `department` | string | `ban-dao-tao`, `phong-cong-tac-sinh-vien`, `khoa-kh-cn-giao-duc` | Phân loại theo đơn vị ban hành và quản lý quy định. |
| `source_url` | string | `https://ctt.hust.edu.vn/DisplayWeb/DisplayKehoach?kehoach=27231` | Lưu liên kết tới nguồn công khai chính thức để xác minh thông tin. |
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

| # | Type | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Gold doc / section / evidence phrase |
|---|------|----------------|----------------------------------|-------------------------------------|
| 1 | `numeric` | Khối lượng đăng ký tối đa trong một học kỳ chính đối với người học không bị cảnh báo là bao nhiêu tín chỉ? | Người học không thuộc diện cảnh báo học tập được đăng ký tối đa 24 TC trong học kỳ chính. | `course-registration-student` / `## 2. Khối lượng tín chỉ đăng ký` / `được đăng ký tối đa 24 TC và tối thiểu 12 TC trong học kỳ chính` |
| 2 | `condition` | Điều kiện GPA và điểm rèn luyện để đạt học bổng loại A là gì? | Học bổng loại A yêu cầu GPA từ 3,6 trở lên và điểm rèn luyện học kỳ từ 90 điểm trở lên. | `scholarship-policy` / `## 3. Tiêu chuẩn xét cấp học bổng` / `Học bổng loại A: GPA ≥ 3,6 và điểm rèn luyện học kỳ ≥ 90 điểm.` |
| 3 | `process` | Quy trình sử dụng phòng đọc tại chỗ gồm những bước nào? | Tra cứu tài liệu; checkin tại quầy thủ thư; tự chọn sách theo ký hiệu xếp giá; đọc xong trả sách đúng nơi quy định. | `library-services` / `## 1. Quy trình sử dụng phòng đọc tại chỗ` / bốn câu `Bước 1`–`Bước 4` trong `benchmarks.json` |
| 4 | `list` | Học bổng KKHT có những mức nào và mức của từng loại được tính như thế nào so với loại khá? | Có 3 mức: C bằng tổng học phí các học phần tính GPA; B bằng 1,2 lần loại khá; A bằng 1,5 lần loại khá. | `scholarship-policy` / `## 2. Các mức học bổng` / khối ba dòng `Học bổng KKHT có 3 mức` trong `benchmarks.json` |
| 5 | `metadata-filter` | Khi cần điều chỉnh đăng ký học phần, người học có thể thực hiện những thao tác nào và trong thời điểm nào? | Có thể chuyển lớp, hủy lớp hoặc đăng ký lớp bổ sung; mỗi học kỳ chính có hai đợt điều chỉnh và đăng ký bổ sung lớp đã mở chỉ thực hiện trong tuần đầu học kỳ. | `course-registration-student` / `## 1. Ba giai đoạn đăng ký học tập` / evidence bắt đầu `c) Điều chỉnh đăng ký` / filter `{"audience": "student"}` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

> Benchmark chính thức chưa chạy; các ô kết quả bên dưới được giữ TODO, không điền score/retrieval result trước khi nhóm chạy cùng chiến lược.

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
