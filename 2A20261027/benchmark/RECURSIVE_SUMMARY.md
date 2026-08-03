# Benchmark Summary — RecursiveChunker Strategy

**Student:** Nguyễn Thu Huyền  
**MSSV:** 2A20261027
**Strategy:** `RecursiveChunker(chunk_size=400)`
**Corpus:** `data/k3_university_services`  
**Common runner:** `bench.py`
**Embedding:** OpenAI `text-embedding-3-small`
**Agent:** OpenAI `gpt-4o-mini`
**Top-k:** 3

## Kết quả chung

- Tổng số chunks: **32**
- Evidence trong top-3: **4/5**
- Evidence ở top-1: **4/5**
- Agent grounded: **2/5**
- Tổng điểm: **6/10**

| Query | Top-1 chunk | Score | Evidence rank | Ghi chú |
|---|---|---:|---:|---|
| q1 | `course-registration-student::chunk_3` | 0.606405 | 1 | Agent quote dùng `...`, nên 1 điểm |
| q2 | `scholarship-policy::chunk_3` | 0.721844 | 1 | Agent grounded |
| q3 | `library-services::chunk_0` | 0.713061 | — | Evidence dài không nằm trong một chunk |
| q4 | `scholarship-policy::chunk_2` | 0.769859 | 1 | Evidence ở top-1 nhưng agent không có quote kiểm chứng được |
| q5 | `course-registration-student::chunk_2` | 0.675889 | 1 | Filter `audience=student`, agent grounded |

q5 có A/B metadata filter. Không filter có thêm `course-registration-faculty::chunk_1` trong top-3; filter loại nhiễu faculty và giữ gold chunk ở top-1.

Kết quả JSON cùng schema với các strategy khác nằm tại `2A20261027/benchmark/recursive_results.json`; output tổng hợp nằm tại `benchmark_results.json`.
