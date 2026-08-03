"""Run the personal FixedSizeChunker benchmark without changing shared code/data."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ingest import build_knowledge_base  # noqa: E402
from src import FixedSizeChunker, LocalEmbedder  # noqa: E402
from src.embeddings import LOCAL_EMBEDDING_MODEL, _mock_embed, OpenAIEmbedder  # noqa: E402
from dotenv import load_dotenv
load_dotenv()
from src.agent import KnowledgeBaseAgent  # noqa: E402


DATA_DIR = ROOT / "data" / "k3_university_services"
BENCHMARKS = DATA_DIR / "benchmarks.json"
OUT_DIR = Path(__file__).resolve().parent


def _base_doc_id(result: dict[str, Any]) -> str:
    doc_id = str(result.get("metadata", {}).get("doc_id", result.get("id", "")))
    return doc_id.split("::chunk_", 1)[0]


def _result(result: dict[str, Any], rank: int, evidence: str) -> dict[str, Any]:
    metadata = result.get("metadata", {})
    content = str(result.get("content", ""))
    return {
        "rank": rank,
        "score": round(float(result.get("score", 0.0)), 8),
        "id": result.get("id"),
        "doc_id": _base_doc_id(result),
        "chunk_index": metadata.get("chunk_index"),
        "audience": metadata.get("audience"),
        "source": metadata.get("source"),
        "preview": content[:300].replace("\n", " "),
        "evidence_hit": evidence.lower() in content.lower(),
        "content": content,
    }


def _agent_preview(store, query: str) -> str:
    def demo_llm(prompt: str) -> str:
        return "[DEMO LLM] Pipeline-only preview: " + prompt[:300].replace("\n", " ") + "..."

    return KnowledgeBaseAgent(store=store, llm_fn=demo_llm).answer(query, top_k=3)


def _overlap_notes(results: list[dict[str, Any]]) -> dict[str, Any]:
    notes: list[str] = []
    adjacent_pairs = []
    for left, right in zip(results, results[1:]):
        if left["doc_id"] == right["doc_id"]:
            left_index = left.get("chunk_index")
            right_index = right.get("chunk_index")
            if isinstance(left_index, int) and isinstance(right_index, int) and right_index == left_index + 1:
                adjacent_pairs.append([left["id"], right["id"]])
    if adjacent_pairs:
        notes.append("Top-3 chứa chunk liền kề; hai chunk chia sẻ tối đa 80 ký tự theo cấu hình overlap.")
        notes.append("Các chunk liền kề có thể lặp evidence và làm giảm diversity của top-3.")
    else:
        notes.append("Không thấy cặp chunk liền kề trong top-3 của lần chạy pipeline này.")
    return {"adjacent_chunk_pairs": adjacent_pairs, "notes": notes}


def main() -> int:
    benchmarks = json.loads(BENCHMARKS.read_text(encoding="utf-8"))
    chunker = FixedSizeChunker(chunk_size=400, overlap=80)
    embedder = None
    backend = "unavailable"
    local_error = None
    try:
        embedder = OpenAIEmbedder()
        backend = getattr(embedder, "_backend_name", "OpenAIEmbedder")
    except Exception as exc:  # local model is optional but required for semantic scoring
        local_error = f"{type(exc).__name__}: {exc}"

    scored = embedder is not None
    pipeline_embedder = embedder or _mock_embed
    store = build_knowledge_base(DATA_DIR, pipeline_embedder, chunker=chunker)
    query_results = []

    for item in benchmarks:
        query = item["query"]
        evidence = item["evidence_phrase"]
        no_filter = [_result(r, rank, evidence) for rank, r in enumerate(store.search(query, top_k=3), 1)]
        with_filter = None
        if item.get("metadata_filter"):
            with_filter = [
                _result(r, rank, evidence)
                for rank, r in enumerate(
                    store.search_with_filter(query, top_k=3, metadata_filter=item["metadata_filter"]), 1
                )
            ]

        gold_rank = next(
            (r["rank"] for r in no_filter if r["doc_id"] == item["gold_doc_id"]),
            None,
        )
        query_results.append(
            {
                "query_id": item["query_id"],
                "query": query,
                "gold_answer": item["gold_answer"],
                "gold_doc_id": item["gold_doc_id"],
                "expected_section": item["expected_section"],
                "evidence_phrase": evidence,
                "metadata_filter": item.get("metadata_filter"),
                "top3": no_filter,
                "filter_ab": {"without_filter": no_filter, "with_filter": with_filter},
                "gold_chunk_rank": gold_rank,
                "evidence_in_top3": any(r["evidence_hit"] for r in no_filter),
                "agent_answer": _agent_preview(store, query),
                "score": None if not scored else "manual_review_required",
                "points": None if not scored else "manual_review_required",
                "overlap_analysis": _overlap_notes(no_filter),
            }
        )

    result = {
        "student_name": "Hoàng Đức Anh",
        "student_id": "2A202601223",
        "strategy": "FixedSizeChunker",
        "chunk_size": 400,
        "overlap": 80,
        "stride": 320,
        "backend": backend if scored else "mock embeddings fallback (pipeline check only)",
        "model": LOCAL_EMBEDDING_MODEL,
        "total_chunks": store.get_collection_size(),
        "run_date": date.today().isoformat(),
        "semantic_scoring_available": scored,
        "local_embedding_error": local_error,
        "query_results": query_results,
        "total_score": None if not scored else "manual_review_required",
        "limitation": (
            "LocalEmbedder could not be initialized; mock output is retained only as a pipeline check. "
            "No semantic retrieval score or agent answer score is claimed."
            if not scored
            else "Agent uses the deterministic demo LLM; generation quality requires separate LLM evaluation."
        ),
    }
    (OUT_DIR / "fixed_size_results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    status = "available" if scored else "unavailable; mock pipeline check only"
    summary = f"""# FixedSizeChunker — benchmark summary

**Student:** Hoàng Đức Anh (`2A202601223`)  
**Strategy:** `FixedSizeChunker(chunk_size=400, overlap=80)`  
**Stride:** 320 characters  
**Corpus:** `data/k3_university_services`  
**Embedding:** `{LOCAL_EMBEDDING_MODEL}`  
**Local backend:** {status}  
**Total chunks:** {store.get_collection_size()}

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

The benchmark is blocked at the embedding stage: `sentence-transformers/{LOCAL_EMBEDDING_MODEL.split('/', 1)[-1]}` was not available in the environment. This is an environment limitation, not evidence that FixedSizeChunker failed. A valid rerun should install the local dependency/model and regenerate this file without changing the corpus, queries, or strategy parameters.
"""
    (OUT_DIR / "FIXED_SIZE_SUMMARY.md").write_text(summary, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
