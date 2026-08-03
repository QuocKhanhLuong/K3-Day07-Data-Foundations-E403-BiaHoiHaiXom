from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from ingest import build_knowledge_base
from src.agent import KnowledgeBaseAgent
from src.chunking import RecursiveChunker
from src.embeddings import EMBEDDING_PROVIDER_ENV, LocalEmbedder, MockEmbedder


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def check_evidence_hit(chunk_content: str, evidence_phrase: str) -> bool:
    if not evidence_phrase:
        return False
    norm_content = normalize_text(chunk_content)
    norm_evidence = normalize_text(evidence_phrase)
    if norm_evidence in norm_content:
        return True
    words = [w for w in norm_evidence.split() if len(w) > 3]
    if len(words) >= 4:
        match_count = sum(1 for w in words if w in norm_content)
        return (match_count / len(words)) >= 0.85
    return False


def run_benchmark():
    os.environ["EMBEDDING_PROVIDER"] = "local"
    
    limitation_msg = None
    try:
        embedder = LocalEmbedder()
        backend_name = getattr(embedder, "_backend_name", "local")
        model_name = getattr(embedder, "model_name", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    except Exception as e:
        limitation_msg = f"LocalEmbedder unavailable ({e}). Fallback to MockEmbedder for technical smoke test."
        print(f"Warning: {limitation_msg}")
        embedder = MockEmbedder()
        backend_name = "mock"
        model_name = "mock-embeddings-fallback"

    chunk_size = 400
    chunker = RecursiveChunker(chunk_size=chunk_size)
    corpus_dir = "data/k3_university_services"

    print("==================================================")
    print("RUNNING BENCHMARK EVALUATION")
    print("Student: Nguyễn Thu Huyền (2A20261027)")
    print(f"Strategy: RecursiveChunker(chunk_size={chunk_size})")
    print(f"Backend: {backend_name}")
    print(f"Model: {model_name}")
    print("==================================================")

    store = build_knowledge_base(corpus_dir, embedding_fn=embedder, chunker=chunker)
    total_chunks = store.get_collection_size()
    print(f"Total chunks indexed: {total_chunks}\n")

    benchmarks_path = Path("data/k3_university_services/benchmarks.json")
    with open(benchmarks_path, "r", encoding="utf-8") as f:
        benchmarks = json.load(f)

    agent = KnowledgeBaseAgent(store=store)

    results_data = {
        "student_name": "Nguyễn Thu Huyền",
        "student_id": "2A20261027",
        "strategy": "RecursiveChunker",
        "parameters": {"chunk_size": chunk_size},
        "embedding_backend": backend_name,
        "embedding_model": model_name,
        "limitation": limitation_msg,
        "total_chunks": total_chunks,
        "queries": [],
        "total_score": 0
    }

    total_score = 0

    for item in benchmarks:
        q_id = item["query_id"]
        query = item["query"]
        gold_answer = item["gold_answer"]
        gold_doc_id = item["gold_doc_id"]
        expected_section = item["expected_section"]
        evidence_phrase = item["evidence_phrase"]
        metadata_filter = item.get("metadata_filter")

        print(f"--- [Query {q_id}] ---")
        print(f"Query: {query}")
        print(f"Gold Doc: {gold_doc_id}")
        print(f"Metadata Filter: {metadata_filter}")

        # Search with filter if applicable
        if metadata_filter:
            top3_filtered = store.search_with_filter(query, top_k=3, metadata_filter=metadata_filter)
            top3_unfiltered = store.search(query, top_k=3)
        else:
            top3_filtered = store.search(query, top_k=3)
            top3_unfiltered = top3_filtered

        top3_eval = []
        any_evidence_hit = False

        for rank, res in enumerate(top3_filtered, start=1):
            content = res.get("content", "")
            meta = res.get("metadata", {})
            score = res.get("score", 0.0)
            doc_id = meta.get("doc_id", res.get("id", ""))
            hit = check_evidence_hit(content, evidence_phrase)
            if hit:
                any_evidence_hit = True

            top3_eval.append({
                "rank": rank,
                "score": round(score, 4),
                "doc_id": doc_id,
                "metadata": meta,
                "content_preview": content[:350],
                "evidence_hit": hit
            })
            print(f"  Rank {rank} | Score: {score:.4f} | Doc: {doc_id} | Evidence Hit: {hit}")

        # A/B Filter Analysis
        filter_ab_res = None
        if metadata_filter:
            unfiltered_docs = [r.get("metadata", {}).get("doc_id", r.get("id")) for r in top3_unfiltered]
            filtered_docs = [r.get("metadata", {}).get("doc_id", r.get("id")) for r in top3_filtered]
            filter_ab_res = {
                "without_filter_top3_docs": unfiltered_docs,
                "with_filter_top3_docs": filtered_docs,
                "excluded_wrong_audience": any(meta_aud != metadata_filter.get("audience") for meta_aud in [r.get("metadata", {}).get("audience") for r in top3_unfiltered])
            }

        # LLM / Agent Answer
        agent_ans = agent.answer(query, top_k=3)
        print(f"Agent Answer Preview: {agent_ans[:150]}...")

        # Scoring
        score_0_1_2 = 0
        if any_evidence_hit:
            score_0_1_2 = 2
        elif any(res["doc_id"] == gold_doc_id for res in top3_eval):
            score_0_1_2 = 1
        else:
            score_0_1_2 = 0

        total_score += score_0_1_2
        print(f"Score (0/1/2): {score_0_1_2}/2\n")

        results_data["queries"].append({
            "query_id": q_id,
            "query": query,
            "gold_answer": gold_answer,
            "gold_doc_id": gold_doc_id,
            "expected_section": expected_section,
            "evidence_phrase": evidence_phrase,
            "metadata_filter": metadata_filter,
            "top3": top3_eval,
            "evidence_hit": any_evidence_hit,
            "agent_answer": agent_ans,
            "score_0_1_2": score_0_1_2,
            "filter_ab": filter_ab_res
        })

    results_data["total_score"] = total_score
    print("==================================================")
    print(f"FINAL BENCHMARK SCORE: {total_score} / 10")
    print("==================================================")

    # Save JSON results
    out_dir = Path("2A20261027/benchmark")
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "recursive_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results_data, f, ensure_ascii=False, indent=2)
    print(f"Saved results to {json_path}")

    # Also save to 2A202601027/benchmark/
    alt_dir = Path("2A202601027/benchmark")
    alt_dir.mkdir(parents=True, exist_ok=True)
    with open(alt_dir / "recursive_results.json", "w", encoding="utf-8") as f:
        json.dump(results_data, f, ensure_ascii=False, indent=2)

    return results_data

if __name__ == "__main__":
    run_benchmark()
