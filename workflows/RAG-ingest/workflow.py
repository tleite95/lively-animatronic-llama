from __future__ import annotations

from state import RAGIngestionState, make_initial_state

from langgraph.graph import StateGraph, START, END

import nodes
import routers

def build_graph():
    g = StateGraph(RAGIngestionState)
    g.add_node("init", nodes.init)

    g.add_node("pdf2jsonl", nodes.pdf2jsonl)
    g.add_node("reset", nodes.reset)
    g.add_node("fail_jsonl-verify", nodes.fail_jsonl_verification)
    g.add_node("jsonl-cleanup", nodes.jsonl_cleanup)
    g.add_node("fail_jsonl-cleanup", nodes.fail_jsonl_cleanup)
    g.add_node("ragchunk-verify", nodes.ragchunk_verify)
    g.add_node("branch", nodes.branch_lightrag_wiki)
    g.add_node("wiki-branch-start", nodes.empty)
    g.add_node("lightrag-branch-start", nodes.empty)
    g.add_node("doc-batch-wiki", nodes.batch_chunks_by_documents__wiki)
    g.add_node("wiki-ingest", nodes.wiki_ingest)
    g.add_node("wiki-write", nodes.wiki_write)
    g.add_node("wiki-verify", nodes.wiki_verify)
    g.add_node("doc-batch-lightrag", nodes.batch_chunks_by_documents__lightrag)
    g.add_node("lightrag-prep", nodes.prepare_lightrag)
    g.add_node("lightrag-insert", nodes.insert_into_lightrag)

    g.add_edge(START, "init")
    g.add_edge("init", "pdf2jsonl")
    g.add_conditional_edges(
        "pdf2jsonl",
        routers.jsonl_verify,
        {
            "continue": "jsonl-cleanup",
            "retry": "reset",
            "abort": "fail_jsonl-verify",
        }
    )
    g.add_node("reset", "init")
    g.add_conditional_edges(
        "jsonl-cleanup",
        routers.rag_verify,
        {
            "overpruned": "init",
            "underpruned": "jsonl-cleanup",
            "valid": "branch",
            "failed": "fail_jsonl-cleanup",
        }
    )

    g.add_edge("branch", ["wiki-branch-start", "lightrag-branch-start"])

    g.add_conditional_edges(
        "lightrag-branch-start",
        routers.check_lightrag_done_ingesting,
        {
            True: END,
            False: "doc-batch-lightrag",
        }
    )
    g.add_edge("doc-batch-wiki", "lightrag-prep")
    g.add_edge("lightrag-prep", "lightrag-insert")
    g.add_edge("lightrag-insert", "lightrag-branch-start")

    g.add_conditional_edges(
        "wiki-branch-start",
        routers.check_wiki_done_ingesting,
        {
            True: END,
            False: "doc-batch-wiki",
        }
    )
    g.add_edge("doc-batch-wiki", "wiki-ingest")
    g.add_edge("wiki-ingest", "wiki-write")
    g.add_edge("wiki-write", "wiki-verify")
    g.add_edge("wiki-verify", "wiki-branch-start")

if __name__ == "__main__":
    app = build_graph()
    summaries = app.invoke(make_initial_state("./config.yaml"))["summaries"]
    
    print(summaries["wiki"])
    print(summaries["lightrag"])