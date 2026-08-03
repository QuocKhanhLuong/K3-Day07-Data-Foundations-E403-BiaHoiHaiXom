# FixedSizeChunker — benchmark summary

**Student:** Hoàng Đức Anh (`2A202601223`)  
**Strategy:** `FixedSizeChunker(chunk_size=400, overlap=80)`  
**Stride:** 320 characters  
**Corpus:** `data/k3_university_services`  
**Embedding:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`  
**Local backend:** available  
**Total chunks:** 28

## Scoring status

The local embedder was attempted exactly as specified. Semantic scores are **not claimed** because the local model was unavailable. The recorded top-3 and agent fields come from the deterministic mock backend and are pipeline diagnostics only. The demo LLM is also not a complete grounded answer generator.

**Total score:** N/A (requires a successful local-embedder run)

## Overlap analysis

- `overlap=80` preserves boundary context across adjacent chunks.
- It can duplicate evidence in neighboring chunks and reduce top-3 diversity.
- The per-query JSON records adjacent chunk pairs and evidence hits from the pipeline check.

## Filter A/B

For q1, q2 and q5, the JSON records top-3 without a filter and with the required audience filter. Since the backend is mock-only, this comparison is diagnostic and must not be treated as semantic quality evidence.

## Failure case

The benchmark is blocked at the embedding stage: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` was not available in the environment. This is an environment limitation, not evidence that FixedSizeChunker failed. A valid rerun should install the local dependency/model and regenerate this file without changing the corpus, queries, or strategy parameters.
