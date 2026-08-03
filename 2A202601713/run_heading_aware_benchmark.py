"""Run Lương Quốc Khánh's locked benchmark with heading-aware chunks.

The runner deliberately uses the shared corpus and benchmark file.  It uses
OpenAI embeddings (the group's selected backend), evaluates evidence at chunk
level, runs the q5 metadata-filter A/B, and stores the observed results in the
personal folder.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any


PERSONAL_DIR = Path(__file__).resolve().parent
REPO_ROOT = PERSONAL_DIR.parent
sys.path.insert(0, str(PERSONAL_DIR))
sys.path.insert(1, str(REPO_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env", override=False)
except ImportError:
    # The benchmark environment already provides python-dotenv.  Keeping this
    # fallback makes the import failure explicit rather than hiding a secret
    # or silently switching embedding providers.
    pass

from ingest import chunk_document, load_documents  # noqa: E402
from src.agent import KnowledgeBaseAgent  # noqa: E402
from src.chunking import RecursiveChunker  # noqa: E402
from src.embeddings import OPENAI_EMBEDDING_MODEL, OpenAIEmbedder  # noqa: E402
from src.models import Document  # noqa: E402
from src.store import EmbeddingStore  # noqa: E402
from src.strategy import HeadingAwareChunker  # noqa: E402


DATA_DIR = REPO_ROOT / "data" / "k3_university_services"
BENCHMARK_PATH = DATA_DIR / "benchmarks.json"
RESULT_PATH = PERSONAL_DIR / "benchmark_heading_aware.json"
CHUNK_SIZE = 800
TOP_K = 3
COLLECTION_NAME = "qkhanh_heading_aware_benchmark"


def normalize_for_match(text: str) -> str:
    """Normalize whitespace and Markdown emphasis for exact evidence checks."""
    text = re.sub(r"(?:\*\*|__)", "", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def _base_doc_id(result: dict[str, Any]) -> str:
    metadata = result.get("metadata") or {}
    explicit_doc_id = metadata.get("doc_id")
    if explicit_doc_id:
        return str(explicit_doc_id)
    return str(result.get("id", "")).split("::", 1)[0]


def _result_payload(result: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(result.get("metadata") or {})
    return {
        "id": result.get("id"),
        "doc_id": _base_doc_id(result),
        "chunk_index": metadata.get("chunk_index"),
        "audience": metadata.get("audience"),
        "score": float(result.get("score", 0.0)),
        "content": result.get("content", ""),
        "metadata": metadata,
    }


def evaluate_retrieval(
    benchmark: dict[str, Any],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Evaluate whether the exact evidence occurs in a retrieved chunk."""
    gold_doc_id = str(benchmark["gold_doc_id"])
    evidence = normalize_for_match(str(benchmark["evidence_phrase"]))
    expected_section = normalize_for_match(str(benchmark["expected_section"]))

    evidence_ranks: list[int] = []
    section_ranks: list[int] = []
    for rank, result in enumerate(results, start=1):
        content = normalize_for_match(str(result.get("content", "")))
        is_gold_doc = _base_doc_id(result) == gold_doc_id
        if is_gold_doc and evidence and evidence in content:
            evidence_ranks.append(rank)
        if is_gold_doc and expected_section and expected_section in content:
            section_ranks.append(rank)

    evidence_rank = evidence_ranks[0] if evidence_ranks else None
    return {
        "gold_doc_id": gold_doc_id,
        "evidence_in_top1": evidence_rank == 1,
        "evidence_in_top3": evidence_rank is not None,
        "evidence_rank": evidence_rank,
        "expected_section_in_top3": bool(section_ranks),
        "expected_section_rank": section_ranks[0] if section_ranks else None,
        "top_results": [_result_payload(result) for result in results],
    }


def _context_quote(answer: str, results: list[dict[str, Any]]) -> str | None:
    """Find a meaningful verbatim context quote in the agent response."""
    answer_normalized = normalize_for_match(answer)
    for result in results:
        content = str(result.get("content", ""))
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", content):
            sentence_normalized = normalize_for_match(sentence)
            if len(sentence_normalized) >= 45 and sentence_normalized in answer_normalized:
                return sentence.strip()
    return None


def evaluate_agent_answer(
    answer: str,
    benchmark: dict[str, Any],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    evidence = normalize_for_match(str(benchmark["evidence_phrase"]))
    answer_normalized = normalize_for_match(answer)
    quote = _context_quote(answer, results)
    contains_phrase = bool(evidence and evidence in answer_normalized)
    return {
        "answer": answer,
        "contains_gold_evidence_phrase": contains_phrase,
        "context_quote": quote,
        "contains_context_quote": quote is not None,
        "grounded": bool(answer.strip()) and (contains_phrase or quote is not None),
    }


class StaticResultStore:
    """Expose already evaluated retrieval results to KnowledgeBaseAgent."""

    def __init__(self, results: list[dict[str, Any]]) -> None:
        self.results = results

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        del query
        return self.results[:top_k]


def _openai_answerer() -> tuple[str, Any]:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing after loading the repository .env")

    from openai import OpenAI

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI()

    def answer(prompt: str) -> str:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a grounded university-services assistant. "
                        "Answer in Vietnamese using only the retrieved context. "
                        "Do not add facts that are absent from context. "
                        "Include a short section named 'Bằng chứng:' and copy the "
                        "most relevant sentence verbatim from the context. "
                        "If context is insufficient, say so clearly."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        content = response.choices[0].message.content
        return content or ""

    return model, answer


def _run_agent(
    question: str,
    results: list[dict[str, Any]],
    benchmark: dict[str, Any],
    llm_fn: Any,
) -> dict[str, Any]:
    agent = KnowledgeBaseAgent(StaticResultStore(results), llm_fn=llm_fn)
    answer = agent.answer(question, top_k=TOP_K)
    return evaluate_agent_answer(answer, benchmark, results)


def _failure_analysis(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Select the first observed weakness for the personal report."""
    for record in records:
        retrieval = record["retrieval"]
        agent = record["agent"]
        if not retrieval["evidence_in_top3"]:
            return {
                "type": "evidence_not_retrieved",
                "query_id": record["query_id"],
                "observation": "Gold evidence was absent from the evaluated top-3 chunks.",
                "evidence_rank": retrieval["evidence_rank"],
                "top_doc_ids": [item["doc_id"] for item in retrieval["top_results"]],
            }
        if retrieval["evidence_rank"] != 1:
            return {
                "type": "evidence_not_top1",
                "query_id": record["query_id"],
                "observation": "Gold evidence was retrieved, but another chunk ranked above it.",
                "evidence_rank": retrieval["evidence_rank"],
                "top1_doc_id": retrieval["top_results"][0]["doc_id"]
                if retrieval["top_results"]
                else None,
            }
        if not agent["grounded"]:
            return {
                "type": "agent_grounding_check",
                "query_id": record["query_id"],
                "observation": "Retrieval put the evidence first, but the answer did not contain a verifiable context quote.",
                "evidence_rank": retrieval["evidence_rank"],
                "contains_context_quote": agent["contains_context_quote"],
            }

    q5 = next((record for record in records if record["query_id"] == "q5"), None)
    if q5 and q5.get("ab"):
        unfiltered = q5["ab"]["unfiltered"]["retrieval"]
        filtered = q5["ab"]["filtered"]["retrieval"]
        unfiltered_top = unfiltered["top_results"][0] if unfiltered["top_results"] else {}
        filtered_top = filtered["top_results"][0] if filtered["top_results"] else {}
        return {
            "type": "metadata_filter_ab_no_change",
            "query_id": "q5",
            "observation": "All official checks passed, but the student filter did not change the top-1 chunk in this run.",
            "unfiltered_top1": {
                "doc_id": unfiltered_top.get("doc_id"),
                "audience": unfiltered_top.get("audience"),
            },
            "filtered_top1": {
                "doc_id": filtered_top.get("doc_id"),
                "audience": filtered_top.get("audience"),
            },
        }

    return {
        "type": "no_failure_observed",
        "observation": "No retrieval or grounding weakness was observed in the five official runs.",
    }


def main() -> int:
    if not DATA_DIR.is_dir():
        raise FileNotFoundError(DATA_DIR)
    if not BENCHMARK_PATH.is_file():
        raise FileNotFoundError(BENCHMARK_PATH)

    benchmarks = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    if len(benchmarks) != 5:
        raise AssertionError(f"Expected exactly five locked queries, got {len(benchmarks)}")

    embedder = OpenAIEmbedder(
        model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL)
    )
    chat_model, llm_fn = _openai_answerer()

    documents = load_documents(DATA_DIR)
    chunker = HeadingAwareChunker(chunk_size=CHUNK_SIZE)
    chunk_documents: list[Document] = []
    inventory: list[dict[str, Any]] = []
    for document in documents:
        chunks = chunk_document(document, chunker)
        chunk_documents.extend(chunks)
        inventory.append(
            {
                "doc_id": document.id,
                "chunk_count": len(chunks),
                "chunk_lengths": [len(chunk.content) for chunk in chunks],
                "chunker_stats": dict(chunker.last_stats),
            }
        )

    if not chunk_documents:
        raise AssertionError("Heading-aware strategy produced no chunks")
    if any(len(chunk.content) > CHUNK_SIZE for chunk in chunk_documents):
        raise AssertionError("A final chunk exceeded the configured character budget")

    store = EmbeddingStore(
        collection_name=COLLECTION_NAME,
        embedding_fn=embedder,
    )
    store.add_documents(chunk_documents)

    records: list[dict[str, Any]] = []
    for benchmark in benchmarks:
        query = str(benchmark["query"])
        metadata_filter = benchmark.get("metadata_filter")
        unfiltered_results = store.search(query, top_k=TOP_K)
        unfiltered_retrieval = evaluate_retrieval(benchmark, unfiltered_results)

        if metadata_filter:
            filtered_results = store.search_with_filter(
                query,
                top_k=TOP_K,
                metadata_filter=metadata_filter,
            )
            filtered_retrieval = evaluate_retrieval(benchmark, filtered_results)
            unfiltered_agent = _run_agent(query, unfiltered_results, benchmark, llm_fn)
            filtered_agent = _run_agent(query, filtered_results, benchmark, llm_fn)
            effective_results = filtered_results
            retrieval = filtered_retrieval
            agent = filtered_agent
            ab = {
                "unfiltered": {
                    "retrieval": unfiltered_retrieval,
                    "agent": unfiltered_agent,
                },
                "filtered": {
                    "retrieval": filtered_retrieval,
                    "agent": filtered_agent,
                },
            }
        else:
            effective_results = unfiltered_results
            retrieval = unfiltered_retrieval
            agent = _run_agent(query, effective_results, benchmark, llm_fn)
            ab = None

        score = 0
        if retrieval["evidence_in_top3"]:
            score = 1
            if retrieval["evidence_in_top1"] and agent["grounded"]:
                score = 2

        records.append(
            {
                "query_id": benchmark["query_id"],
                "type": benchmark["type"],
                "query": query,
                "gold_answer": benchmark["gold_answer"],
                "gold_doc_id": benchmark["gold_doc_id"],
                "expected_section": benchmark["expected_section"],
                "evidence_phrase": benchmark["evidence_phrase"],
                "metadata_filter": metadata_filter,
                "filter_applied": bool(metadata_filter),
                "retrieval": retrieval,
                "agent": agent,
                "score": score,
                "ab": ab,
            }
        )

    scores = [record["score"] for record in records]
    payload = {
        "student": {
            "name": "Lương Quốc Khánh",
            "student_id": "2A202601713",
            "branch": "qkhanh",
        },
        "strategy": {
            "name": "Heading-aware chunking + Recursive fallback",
            "implementation": "2A202601713/src/strategy.py",
            "chunk_size_characters": CHUNK_SIZE,
            "fallback_separators": list(RecursiveChunker.DEFAULT_SEPARATORS),
        },
        "configuration": {
            "corpus": str(DATA_DIR.relative_to(REPO_ROOT)),
            "benchmark_file": str(BENCHMARK_PATH.relative_to(REPO_ROOT)),
            "embedding_provider": "openai",
            "embedding_model": embedder.model_name,
            "agent_provider": "openai",
            "agent_model": chat_model,
            "top_k": TOP_K,
            "collection_size": store.get_collection_size(),
        },
        "chunk_inventory": inventory,
        "queries": records,
        "summary": {
            "query_count": len(records),
            "top3_evidence_hits": sum(
                record["retrieval"]["evidence_in_top3"] for record in records
            ),
            "top1_evidence_hits": sum(
                record["retrieval"]["evidence_in_top1"] for record in records
            ),
            "grounded_agent_answers": sum(record["agent"]["grounded"] for record in records),
            "score_total": sum(scores),
            "score_max": 2 * len(scores),
        },
        "failure_analysis": _failure_analysis(records),
    }
    RESULT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "result_path": str(RESULT_PATH.relative_to(REPO_ROOT)),
                "embedding_model": embedder.model_name,
                "agent_model": chat_model,
                "collection_size": store.get_collection_size(),
                "scores": scores,
                "summary": payload["summary"],
                "failure_analysis": payload["failure_analysis"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
