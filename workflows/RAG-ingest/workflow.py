from __future__ import annotations

from state import RAGIngestionState, make_initial_state

from langgraph.graph import StateGraph, START, END

import nodes
import routers

def build_graph():
    builder = StateGraph(RAGIngestionState)
    builder.add_node("init", nodes.init)

    builder.add_node("pdf2jsonl", nodes.pdf2jsonl)
    builder.add_node("reset", nodes.reset)
    builder.add_node("fail_jsonl-verify", nodes.fail_jsonl_verification)
    builder.add_node("jsonl-cleanup", nodes.jsonl_cleanup)
    builder.add_node("fail_jsonl-cleanup", nodes.fail_jsonl_cleanup)
    # builder.add_node("ragchunk-verify", nodes.ragchunk_verify)
    builder.add_node("branch", nodes.branch_lightrag_wiki)
    builder.add_node("wiki-branch-start", nodes.empty)
    builder.add_node("lightrag-branch-start", nodes.empty)
    builder.add_node("doc-batch-wiki", nodes.batch_chunks_by_document__wiki)
    builder.add_node("wiki-ingest", nodes.wiki_ingest)
    builder.add_node("wiki-write", nodes.wiki_write)
    builder.add_node("wiki-verify", nodes.wiki_verify)
    builder.add_node("doc-batch-lightrag", nodes.batch_chunks_by_document__lightrag)
    builder.add_node("lightrag-prep", nodes.prepare_lightrag)
    builder.add_node("lightrag-insert", nodes.insert_into_lightrag)

    builder.add_edge(START, "init")
    builder.add_edge("init", "pdf2jsonl")
    builder.add_conditional_edges(
        "pdf2jsonl",
        routers.jsonl_verify,
        {
            "continue": "jsonl-cleanup",
            "retry": "reset",
            "abort": "fail_jsonl-verify",
        }
    )
    builder.add_edge("reset", "init")
    builder.add_conditional_edges(
        "jsonl-cleanup",
        routers.rag_verify,
        {
            "overpruned": "init",
            "underpruned": "jsonl-cleanup",
            "valid": "branch",
            "failed": "fail_jsonl-cleanup",
        }
    )

    builder.add_edge("branch", "lightrag-branch-start")
    builder.add_edge("branch", "wiki-branch-start")

    builder.add_conditional_edges(
        "lightrag-branch-start",
        routers.check_lightrag_done_ingesting,
        {
            True: END,
            False: "doc-batch-lightrag",
        }
    )
    builder.add_edge("doc-batch-lightrag", "lightrag-prep")
    builder.add_edge("lightrag-prep", "lightrag-insert")
    builder.add_edge("lightrag-insert", "lightrag-branch-start")

    builder.add_conditional_edges(
        "wiki-branch-start",
        routers.check_wiki_done_ingesting,
        {
            True: END,
            False: "doc-batch-wiki",
        }
    )
    builder.add_edge("doc-batch-wiki", "wiki-ingest")
    builder.add_edge("wiki-ingest", "wiki-write")
    builder.add_edge("wiki-write", "wiki-verify")
    builder.add_edge("wiki-verify", "wiki-branch-start")

    return builder.compile()

if __name__ == "__main__":
    app = build_graph()
    summaries = app.invoke(make_initial_state("./config.yaml"))["summaries"]
    
    print(summaries["wiki"])
    print(summaries["lightrag"])
