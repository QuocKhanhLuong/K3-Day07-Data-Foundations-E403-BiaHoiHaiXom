"""Common fair benchmark for all four Lab 07 group strategies.

Every strategy is evaluated with the same corpus, locked benchmark file,
OpenAI embedding model, agent model, prompt contract, metadata filter, exact
chunk-level evidence check, and 0/1/2 scoring rule.  Only the chunker and its
locked parameters vary.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "k3_university_services"
BENCHMARK_PATH = DATA_DIR / "benchmarks.json"
COMMON_RESULT_PATH = ROOT / "benchmark_results.json"
TOP_K = 3
CHUNK_SIZE = 400
EMBEDDING_MODEL = "text-embedding-3-small"
AGENT_MODEL = "gpt-4o-mini"

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env", override=False)
except ImportError:
    pass

from ingest import chunk_document, load_documents  # noqa: E402
from src.agent import KnowledgeBaseAgent  # noqa: E402
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker  # noqa: E402
from src.embeddings import OpenAIEmbedder  # noqa: E402
from src.models import Document  # noqa: E402
from src.store import EmbeddingStore  # noqa: E402


def _load_heading_chunker() -> type:
    """Load Khánh's custom strategy without replacing the shared ``src`` package."""
    strategy_path = ROOT / "2A202601713" / "src" / "strategy.py"
    spec = importlib.util.spec_from_file_location("qkhanh_heading_strategy", strategy_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load heading strategy from {strategy_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.HeadingAwareChunker


class CachedEmbedder:
    """Cache identical text embeddings while preserving one common backend."""

    def __init__(self, embedder: Callable[[str], list[float]]) -> None:
        self.embedder = embedder
        self.cache: dict[str, list[float]] = {}

    def __call__(self, text: str) -> list[float]:
        if text not in self.cache:
            self.cache[text] = self.embedder(text)
        return self.cache[text]


class StaticResultStore:
    """Pass one already-evaluated result list to the common agent prompt."""

    def __init__(self, results: list[dict[str, Any]]) -> None:
        self.results = results

    def search(self, query: str, top_k: int = TOP_K) -> list[dict[str, Any]]:
        del query
        return self.results[:top_k]


@dataclass(frozen=True)
class StrategySpec:
    key: str
    student_name: str
    student_id: str
    label: str
    output_path: Path
    factory: Callable[[], Any]
    parameters: dict[str, Any]


def strategy_specs() -> list[StrategySpec]:
    heading_chunker = _load_heading_chunker()
    return [
        StrategySpec(
            key="heading_aware",
            student_name="Lương Quốc Khánh",
            student_id="2A202601713",
            label="Heading-aware chunking + Recursive fallback",
            output_path=ROOT / "2A202601713" / "benchmark_heading_aware.json",
            factory=lambda: heading_chunker(chunk_size=CHUNK_SIZE),
            parameters={"chunk_size": CHUNK_SIZE},
        ),
        StrategySpec(
            key="fixed_size",
            student_name="Hoàng Đức Anh",
            student_id="2A202601223",
            label="FixedSizeChunker",
            output_path=ROOT / "2A202601223" / "benchmark" / "fixed_size_results.json",
            factory=lambda: FixedSizeChunker(chunk_size=CHUNK_SIZE, overlap=80),
            parameters={"chunk_size": CHUNK_SIZE, "overlap": 80, "stride": 320},
        ),
        StrategySpec(
            key="recursive",
            student_name="Nguyễn Thu Huyền",
            student_id="2A20261027",
            label="RecursiveChunker",
            output_path=ROOT / "2A20261027" / "benchmark" / "recursive_results.json",
            factory=lambda: RecursiveChunker(chunk_size=CHUNK_SIZE),
            parameters={"chunk_size": CHUNK_SIZE},
        ),
        StrategySpec(
            key="sentence",
            student_name="Trần Nguyễn Mỹ Anh",
            student_id="2A20261019",
            label="SentenceChunker",
            output_path=ROOT / "2A20261019" / "benchmark" / "sentence_results.json",
            factory=lambda: SentenceChunker(max_sentences_per_chunk=2),
            parameters={"max_sentences_per_chunk": 2},
        ),
    ]


def normalize_for_match(text: str) -> str:
    """Normalize only Markdown emphasis and whitespace; do not fuzzy-match evidence."""
    text = re.sub(r"(?:\*\*|__)", "", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def base_doc_id(result: dict[str, Any]) -> str:
    metadata = result.get("metadata") or {}
    doc_id = metadata.get("doc_id") or result.get("id", "")
    return str(doc_id).split("::chunk_", 1)[0]


def serialize_result(result: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(result.get("metadata") or {})
    return {
        "id": result.get("id"),
        "doc_id": base_doc_id(result),
        "chunk_index": metadata.get("chunk_index"),
        "audience": metadata.get("audience"),
        "score": float(result.get("score", 0.0)),
        "content": str(result.get("content", "")),
        "metadata": metadata,
    }


def evaluate_retrieval(
    benchmark: dict[str, Any],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Check evidence and expected heading within one retrieved chunk."""
    gold_doc_id = str(benchmark["gold_doc_id"])
    evidence = normalize_for_match(str(benchmark["evidence_phrase"]))
    section = normalize_for_match(str(benchmark["expected_section"]))
    evidence_ranks: list[int] = []
    section_ranks: list[int] = []

    for rank, result in enumerate(results, start=1):
        content = normalize_for_match(str(result.get("content", "")))
        if base_doc_id(result) != gold_doc_id:
            continue
        if evidence and evidence in content:
            evidence_ranks.append(rank)
        if section and section in content:
            section_ranks.append(rank)

    evidence_rank = evidence_ranks[0] if evidence_ranks else None
    return {
        "gold_doc_id": gold_doc_id,
        "evidence_in_top1": evidence_rank == 1,
        "evidence_in_top3": evidence_rank is not None,
        "evidence_rank": evidence_rank,
        "expected_section_in_top3": bool(section_ranks),
        "expected_section_rank": section_ranks[0] if section_ranks else None,
        "top_results": [serialize_result(result) for result in results],
    }


def _context_quote(answer: str, results: list[dict[str, Any]]) -> str | None:
    answer_normalized = normalize_for_match(answer)
    for result in results:
        content = str(result.get("content", ""))
        pieces = re.split(r"(?<=[.!?])\s+|\n+", content)
        for piece in pieces:
            normalized_piece = normalize_for_match(piece)
            if len(normalized_piece) >= 45 and normalized_piece in answer_normalized:
                return piece.strip()
    return None


def evaluate_agent(
    answer: str,
    benchmark: dict[str, Any],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    answer_normalized = normalize_for_match(answer)
    evidence = normalize_for_match(str(benchmark["evidence_phrase"]))
    quote = _context_quote(answer, results)
    contains_evidence = bool(evidence and evidence in answer_normalized)
    gold_evidence_in_context = any(
        base_doc_id(result) == str(benchmark["gold_doc_id"])
        and evidence in normalize_for_match(str(result.get("content", "")))
        for result in results
    )
    return {
        "answer": answer,
        "non_empty": bool(answer.strip()),
        "contains_gold_evidence_phrase": contains_evidence,
        "context_quote": quote,
        "contains_context_quote": quote is not None,
        "gold_evidence_in_context": gold_evidence_in_context,
        "grounded": bool(answer.strip())
        and gold_evidence_in_context
        and (contains_evidence or quote is not None),
    }


def openai_answerer() -> tuple[str, Callable[[str], str]]:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing; common benchmark refuses local/mock fallback")

    from openai import OpenAI

    client = OpenAI()

    def answer(prompt: str) -> str:
        response = client.chat.completions.create(
            model=AGENT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the common grounded university-services benchmark agent. "
                        "Answer in Vietnamese using only the retrieved context. "
                        "Do not invent facts. Include a section named 'Bằng chứng:' "
                        "and copy the most relevant sentence verbatim from context. "
                        "If context is insufficient, say so clearly."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        return response.choices[0].message.content or ""

    return AGENT_MODEL, answer


def chunk_inventory(documents: list[Document], chunker: Any) -> tuple[list[Document], list[dict[str, Any]]]:
    chunks: list[Document] = []
    inventory: list[dict[str, Any]] = []
    for document in documents:
        document_chunks = chunk_document(document, chunker)
        chunks.extend(document_chunks)
        lengths = [len(chunk.content) for chunk in document_chunks]
        row: dict[str, Any] = {
            "doc_id": document.id,
            "chunk_count": len(document_chunks),
            "chunk_lengths": lengths,
            "avg_chunk_length": sum(lengths) / len(lengths) if lengths else 0.0,
            "min_chunk_length": min(lengths) if lengths else 0,
            "max_chunk_length": max(lengths) if lengths else 0,
        }
        if hasattr(chunker, "last_stats"):
            row["chunker_stats"] = dict(chunker.last_stats)
        inventory.append(row)
    return chunks, inventory


def run_agent(question: str, results: list[dict[str, Any]], benchmark: dict[str, Any], llm_fn: Callable[[str], str]) -> dict[str, Any]:
    agent = KnowledgeBaseAgent(StaticResultStore(results), llm_fn=llm_fn)
    answer = agent.answer(question, top_k=TOP_K)
    return evaluate_agent(answer, benchmark, results)


def score_query(retrieval: dict[str, Any], agent: dict[str, Any]) -> int:
    if not retrieval["evidence_in_top3"]:
        return 0
    if retrieval["evidence_rank"] == 1 and agent["grounded"]:
        return 2
    return 1


def failure_analysis(records: list[dict[str, Any]]) -> dict[str, Any]:
    for record in records:
        retrieval = record["retrieval"]
        if not retrieval["evidence_in_top3"]:
            return {
                "type": "evidence_not_in_top3",
                "query_id": record["query_id"],
                "evidence_rank": None,
                "top_doc_ids": [item["doc_id"] for item in retrieval["top_results"]],
            }
        if retrieval["evidence_rank"] != 1:
            return {
                "type": "evidence_not_top1",
                "query_id": record["query_id"],
                "evidence_rank": retrieval["evidence_rank"],
                "top1_doc_id": retrieval["top_results"][0]["doc_id"] if retrieval["top_results"] else None,
            }
        if not record["agent"]["grounded"]:
            return {
                "type": "agent_not_verifiably_grounded",
                "query_id": record["query_id"],
                "evidence_rank": retrieval["evidence_rank"],
                "contains_context_quote": record["agent"]["contains_context_quote"],
            }

    q5 = next((record for record in records if record["query_id"] == "q5"), None)
    if q5 and q5.get("ab"):
        before = q5["ab"]["unfiltered"]["retrieval"]["top_results"]
        after = q5["ab"]["filtered"]["retrieval"]["top_results"]
        return {
            "type": "metadata_filter_no_rank_change",
            "query_id": "q5",
            "unfiltered_top_ids": [item["id"] for item in before],
            "filtered_top_ids": [item["id"] for item in after],
        }
    return {"type": "no_failure_observed"}


def build_strategy_result(
    spec: StrategySpec,
    run_config: dict[str, Any],
    chunks: list[Document],
    inventory: list[dict[str, Any]],
    store: EmbeddingStore,
    benchmarks: list[dict[str, Any]],
    llm_fn: Callable[[str], str],
) -> dict[str, Any]:
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
            unfiltered_agent = run_agent(query, unfiltered_results, benchmark, llm_fn)
            filtered_agent = run_agent(query, filtered_results, benchmark, llm_fn)
            retrieval = filtered_retrieval
            agent = filtered_agent
            effective_results = filtered_results
            ab = {
                "unfiltered": {"retrieval": unfiltered_retrieval, "agent": unfiltered_agent},
                "filtered": {"retrieval": filtered_retrieval, "agent": filtered_agent},
            }
        else:
            retrieval = unfiltered_retrieval
            effective_results = unfiltered_results
            agent = run_agent(query, effective_results, benchmark, llm_fn)
            ab = None

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
                "score": score_query(retrieval, agent),
                "ab": ab,
            }
        )

    scores = [record["score"] for record in records]
    return {
        "student": {"name": spec.student_name, "student_id": spec.student_id},
        "strategy": {"name": spec.label, "key": spec.key, "parameters": spec.parameters},
        "chunk_inventory": inventory,
        "collection_size": len(chunks),
        "queries": records,
        "summary": {
            "query_count": len(records),
            "top3_evidence_hits": sum(record["retrieval"]["evidence_in_top3"] for record in records),
            "top1_evidence_hits": sum(record["retrieval"]["evidence_in_top1"] for record in records),
            "grounded_agent_answers": sum(record["agent"]["grounded"] for record in records),
            "score_total": sum(scores),
            "score_max": 2 * len(scores),
        },
        "failure_analysis": failure_analysis(records),
        "output_path": str(spec.output_path.relative_to(ROOT)),
    }


def main() -> int:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing; set it in .env or the environment")
    if not DATA_DIR.is_dir() or not BENCHMARK_PATH.is_file():
        raise FileNotFoundError("Shared corpus or benchmarks.json is missing")

    benchmarks = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    if len(benchmarks) != 5:
        raise AssertionError(f"Expected exactly 5 benchmark queries, got {len(benchmarks)}")
    if [item["query_id"] for item in benchmarks] != ["q1", "q2", "q3", "q4", "q5"]:
        raise AssertionError("Benchmark IDs must be q1..q5 in order")

    base_embedder = OpenAIEmbedder(model_name=EMBEDDING_MODEL)
    cached_embedder = CachedEmbedder(base_embedder)
    agent_model, llm_fn = openai_answerer()
    documents = load_documents(DATA_DIR)
    common_run = {
        "run_date": date.today().isoformat(),
        "corpus": str(DATA_DIR.relative_to(ROOT)),
        "benchmark_file": str(BENCHMARK_PATH.relative_to(ROOT)),
        "query_ids": [item["query_id"] for item in benchmarks],
        "embedding_provider": "openai",
        "embedding_model": EMBEDDING_MODEL,
        "agent_provider": "openai",
        "agent_model": agent_model,
        "top_k": TOP_K,
        "evidence_check": "casefold + remove Markdown emphasis + normalize whitespace; exact phrase must occur in one gold-doc chunk",
        "score_rule": "2=evidence top1 plus grounded agent; 1=evidence top3 but not both; 0=no evidence in top3",
    }

    results: dict[str, dict[str, Any]] = {}
    for spec in strategy_specs():
        chunker = spec.factory()
        chunks, inventory = chunk_inventory(documents, chunker)
        if not chunks:
            raise AssertionError(f"{spec.key} produced no chunks")
        if any(not chunk.content.strip() for chunk in chunks):
            raise AssertionError(f"{spec.key} produced an empty chunk")
        if spec.key != "sentence" and any(len(chunk.content) > CHUNK_SIZE for chunk in chunks):
            raise AssertionError(f"{spec.key} exceeded the 400-character chunk budget")

        store = EmbeddingStore(
            collection_name=f"lab07_common_{spec.key}",
            embedding_fn=cached_embedder,
        )
        store.add_documents(chunks)
        results[spec.key] = {
            "run": common_run,
            **build_strategy_result(spec, common_run, chunks, inventory, store, benchmarks, llm_fn),
        }

    comparison = []
    for key, result in results.items():
        summary = result["summary"]
        lengths = [length for item in result["chunk_inventory"] for length in item["chunk_lengths"]]
        comparison.append(
            {
                "strategy_key": key,
                "student_name": result["student"]["name"],
                "student_id": result["student"]["student_id"],
                "strategy": result["strategy"],
                "collection_size": result["collection_size"],
                "avg_chunk_length": sum(lengths) / len(lengths) if lengths else 0.0,
                **summary,
            }
        )

    common_payload = {
        "schema_version": "lab07-common-benchmark-v2",
        "run": common_run,
        "strategies": results,
        "comparison": comparison,
    }
    COMMON_RESULT_PATH.write_text(
        json.dumps(common_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    for spec in strategy_specs():
        spec.output_path.parent.mkdir(parents=True, exist_ok=True)
        spec.output_path.write_text(
            json.dumps(results[spec.key], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(json.dumps({"common_result": str(COMMON_RESULT_PATH.relative_to(ROOT)), "comparison": comparison}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
