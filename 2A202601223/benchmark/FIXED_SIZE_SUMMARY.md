# FixedSizeChunker — common benchmark summary

**Student:** Hoàng Đức Anh (`2A202601223`)  
**Strategy:** `FixedSizeChunker(chunk_size=400, overlap=80)`  
**Stride:** 320 characters  
**Corpus:** `data/k3_university_services`  
**Common runner:** `bench.py`
**Embedding:** OpenAI `text-embedding-3-small`
**Agent:** OpenAI `gpt-4o-mini`
**Top-k:** 3
**Total chunks:** 28

## Kết quả

- Evidence trong top-3: **4/5**
- Evidence ở top-1: **3/5**
- Agent grounded: **3/5**
- Tổng điểm: **6/10**

| Query | Top-1 chunk | Score | Evidence rank | Ghi chú |
|---|---|---:|---:|---|
| q1 | `course-registration-student::chunk_3` | 0.650069 | 1 | Agent quote dùng `...`, nên 1 điểm |
| q2 | `scholarship-policy::chunk_3` | 0.640405 | 1 | Agent grounded |
| q3 | `library-services::chunk_0` | 0.709361 | — | Evidence dài bị cắt giữa chunks |
| q4 | `scholarship-policy::chunk_1` | 0.677483 | 2 | Evidence không ở top-1 |
| q5 | `course-registration-student::chunk_2` | 0.696337 | 1 | Filter student, agent grounded |

q5 A/B có cùng top-3 trước và sau filter trong run này; các chunk top-3 vốn đã thuộc audience `student`.

JSON cùng schema nằm tại `2A202601223/benchmark/fixed_size_results.json`; output tổng hợp nằm tại `benchmark_results.json`.
