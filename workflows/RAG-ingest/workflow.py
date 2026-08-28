from __future__ import annotations

import warnings

from state import RAGIngestionState, make_initial_state

from langgraph.graph import StateGraph, START, END

import nodes
import routers

# PyTorch warning generated because Docling uses "torch_dtype" instead of "dtype"
warnings.filterwarnings("ignore", message=".*W0808.*")

# Verification needs to be 1. implemented but also 2. the scope needs to be expanded and 3. the checks need to be made more robust
# There should be verification of correct and complete output at every (non-verifier) node
# If verification fails, it should go to the reset node and then retry
# There should be some logic so that the workflow can retry in a smart way
# - Maybe agentic? Show error from console and ask it to come up with a new prompt to fix the issue
# The main issues that come up are infinite looping and context overflow
# - Infinite looping is a softlock and there should be a way to detect it, like periodic audits checking for cycles and then an orchestrator which can interrupt and inject new commands
# - Context overflow crashes a node and then the future nodes don't have the inputs / state they expect
# -- Those should be hardcoded checks to trigger a jump to the retry node but also there should be some way to recover when context is too big
# -- Opencode has automatic compaction, so the issue is when a given prompt is too large. This is somewhat mitigated by manually changing nodes to pass files around
# -- Could it be a good idea to catch the overflow error and just write the problematic prompt to a file, then pass a message like "Read this file and respond to it: `$FILE`"
# Progressive upgrading might also help: if there is a failure state, try a bigger model (specifically one with more context), or maybe a subagent
# There could also be fallbacks that are more problem-solving oriented e.g. if the verification node doesn't see an insertion report, it could check for recently created / edited files instead

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
