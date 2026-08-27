from pathlib import Path
import shutil
import json
import asyncio

from lightrag_wrapper import get_lightrag, cleanup_lightrag

from state import RAGIngestionState

from scripts.util import utc_now
from scripts.run import run_prompt, run_ingest


def init(state: RAGIngestionState):
    # Load config
    artifact_dir = Path(state["config"]["artifacts"])

    state_updates = {}

    # Create necessary artifact directories, add all paths to run manifest
    n_runs = sum(1 for item in (artifact_dir / "runs").iterdir() if item.is_dir())
    run_id = f"{n_runs}_{utc_now()}"
    state_updates["run_id"] = run_id

    state_updates["manifest"] = {**state["manifest"]}

    run_dir = artifact_dir / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    state_updates["manifest"]["run_dir"] = str(run_dir.resolve())

    jsonl_processed_path = (run_dir / "ingestion_stream.jsonl")
    state_updates["manifest"]["processed_jsonl"] = str(jsonl_processed_path.resolve())
    
    jsonl_final_path = (run_dir / "RAG_stream.jsonl")
    state_updates["manifest"]["final_jsonl"] = str(jsonl_final_path.resolve())

    jsonl_quarantine_path = (run_dir / "quarantine_stream.jsonl")
    state_updates["manifest"]["quarantined_jsonl"] = str(jsonl_quarantine_path.resolve())

    jsonl_raw_path = (run_dir / "raw_stream.jsonl")
    state_updates["manifest"]["raw_jsonl"] = str(jsonl_raw_path.resolve())

    md_path = (run_dir / "md")
    md_path.mkdir(parents=True, exist_ok=True)
    state_updates["manifest"]["md_dir"] = str(md_path.resolve())

    txt_path = (run_dir / "txt")
    txt_path.mkdir(parents=True, exist_ok=True)
    state_updates["manifest"]["txt_dir"] = str(txt_path.resolve())

    log_path = (run_dir / "logs")
    log_path.mkdir(parents=True, exist_ok=True)
    state_updates["manifest"]["log_folder"] = str(log_path.resolve())

    report_path = (run_dir / "reports")
    report_path.mkdir(parents=True, exist_ok=True)
    state_updates["manifest"]["report_folder"] = str(report_path.resolve())

    qa_report_path = report_path / "ingestion_qa_report.json"
    state_updates["manifest"]["qa_report"] = str(qa_report_path.resolve())

    major_change_report_path = report_path / "major_change_report.json"
    state_updates["manifest"]["major_change_report"] = str(major_change_report_path.resolve())

    preparation_report_path = report_path / "preparation_report.json"
    state_updates["manifest"]["preparation_report"] = str(preparation_report_path.resolve())
    return state_updates
    

def pdf2jsonl(state: RAGIngestionState):
    run_ingest(state["config"]["pdfs"], state["manifest"])

def reset(state: RAGIngestionState):
    state_updates = {
        "try_number": state["try_number"]
    }
    state_updates["try_number"] += 1

    # Delete most recent artifact files, maintain directory structure
    dirs = [
         Path(state["manifest"]["md_dir"]),
         Path(state["manifest"]["txt_dir"]),
         Path(state["manifest"]["log_folder"]),
         Path(state["manifest"]["report_folder"]),
    ]

    for dir in dirs:
        for file in dir.iterdir():
            if file.is_file():
                file.unlink()

    files = [
        Path(state["manifest"]["processed_jsonl"]),
        Path(state["manifest"]["final_jsonl"]),
        Path(state["manifest"]["quarantined_jsonl"]),
        Path(state["manifest"]["raw_jsonl"]),
        Path(state["manifest"]["qa_report"]),
        Path(state["manifest"]["major_change_report"]),
        Path(state["manifest"]["preparation_report"]),
    ]

    for file in files:
        if file.is_file():
            file.unlink()

    return state_updates

def fail_jsonl_verification(state: RAGIngestionState):
    shutil.rmtree(state["manifest"]["run_dir"], ignore_errors=True)
    print("JSONL verification failed -- unrecoverable error.")

def jsonl_cleanup(state: RAGIngestionState):
    refs =  (
        f"- First-pass JSONL stream: {state['manifest']['processed_jsonl']}\n"
        f"- Quarantined chunks: {state['manifest']['quarantined_jsonl']}\n"
        f"- Run logs: {state['manifest']['log_folder']}\n"
        f"- QA Report: {state['manifest']['qa_report']}\n"
        f"- Major changes during cleanup step: {state['manifest']['major_change_report']}\n"
    )

    if state['manifest']['full_text'] is not None:
        refs += f"- Full-text export: {state['manifest']['full_text']}\n"

    prompt = (
        "Find the first pass at a cleanup of the JSONL stream in the reference files. Produce the artifacts on disk at the following locations:\n"
        f"- `final_jsonl_path`: {state['manifest']['final_jsonl']}\n"
        f"- `report_filepath`: {state['manifest']['preparation_report']}\n\n"
        "Reference Files:\n"
        f"{refs}"
    )

    run_prompt(prompt, agent="jsonl-cleaner", skill="jsonl-to-rag", run_id=state["run_id"])


def fail_jsonl_cleanup(state: RAGIngestionState):
    shutil.rmtree(state["manifest"]["run_dir"], ignore_errors=True)
    print("JSONL cleanup failed -- unrecoverable error.")

def ragchunk_verify(state: RAGIngestionState):
    # QA report pass
    pass

def branch_lightrag_wiki(state: RAGIngestionState):
    doc_queue = set()

    state_updates = {}

    with open(state["manifest"]["final_jsonl"], "r") as ingestion_stream:
        for line in ingestion_stream:
            doc_queue.add(json.loads(line.strip())["source_document_name"])

    state_updates["wiki_doc_queue"] = list(doc_queue)
    state_updates["lightrag_doc_queue"] = list(doc_queue)

    return state_updates

def empty(state: RAGIngestionState):
    pass

def batch_chunks_by_document__lightrag(state: RAGIngestionState):
    state_updates = {
        "lightrag_doc_queue": state["lightrag_doc_queue"].copy(),
        "manifest": {**state["manifest"]},
    }

    doc_name = state_updates["lightrag_doc_queue"].pop(0)

    full_text_file = Path(state["manifest"]["md_dir"]) / f"{Path(doc_name).stem}.md"
    if not full_text_file.exists():
        full_text_file = Path(state["manifest"]["txt_dir"]) / f"{Path(doc_name).stem}.txt"
    if full_text_file.exists():
        full_text_file = full_text_file.resolve()
    else:
        full_text_file = None
    
    state_updates["manifest"]["full_text"] = full_text_file
    return state_updates

def batch_chunks_by_document__wiki(state: RAGIngestionState): 
    state_updates = {
        "wiki_doc_queue": state["wiki_doc_queue"].copy(),
        "manifest": {**state["manifest"]},
    }

    doc_name = state_updates["lightrag_doc_queue"].pop(0)

    chunks = []
    with open(state["manifest"]["final_jsonl"], "r") as ingestion_stream:
        for line in ingestion_stream:
            record = json.loads(line.strip())
            if record["source_document_name"] == doc_name:
                chunks.append(line)

    state_updates["current_wiki_doc"] = chunks
    return state_updates

def wiki_ingest(state: RAGIngestionState):
    doc_stream = "\n".join(state["current_wiki_doc"])

    prompt = f"Prepare the following JSONL stream for ingestion into the wiki: \n\n{doc_stream}"
    response = run_prompt(prompt, agent="wiki-expert", skill="wiki-ingest", run_id=state["run_id"])

    ingestion_report = Path(state["manifest"]["report_folder"]) / "wiki_ingest_report.md"
    ingestion_report.write_text(response, encoding="utf-8")

    return {"wiki_ingest_output": str(ingestion_report.resolve())}

def wiki_write(state: RAGIngestionState):
    report = state["wiki_ingest_output"]
    prompt = (
        "A document has just been ingested for insertion into the wiki. "
        "Edit the relevant wiki pages to add the new information. "
        "Create new pages only as needed. "
        f"Find the ingestion report at: {report}"
    )

    response = run_prompt(prompt, agent="wiki-expert", skill="wiki-write", run_id=state["run_id"])
    insertion_report = Path(state["manifest"]["report_folder"]) / "wiki_insert_report.md"
    insertion_report.write_text(response, encoding="utf-8")

    return {"wiki_write_output": str(insertion_report.resolve())}

def wiki_verify(state: RAGIngestionState):
    report = state["wiki_write_output"]
    prompt = (
        "A series of changes has just been made to the wiki. "
        "Verify all newly inserted information, newly created page, and new claims. "
        "Make sure you check for contradictions across the affected pages as well as the wiki as a whole. "
        f"Find the insertion report at: {report}"
    )
    response = run_prompt(prompt, agent="wiki-expert", skill="wiki-verify", run_id=state["run_id"])
    new_summaries = state["summaries"]["wiki"].copy()
    new_summaries.append(response)
    return {"summaries": {"lightrag": state["summaries"]["lightrag"].copy(), "wiki": new_summaries}}

def prepare_lightrag(state: RAGIngestionState):
    print("WARNING: lightrag preparation is a stub, just passing full text + YAML frontmatter")

def insert_into_lightrag(state: RAGIngestionState):
    new_summaries = state["summaries"]["wiki"].copy()
    response = asyncio.run(ainsert_into_lightrag(state["manifest"]["full_text"]))
    new_summaries.append(response)
    return {"summaries": {"lightrag": new_summaries, "wiki": state["summaries"]["wiki"].copy()}}

async def ainsert_into_lightrag(filen: str):
    try:
        with open(filen) as full_text_file:
            full_text = full_text_file.read()
            rag = await get_lightrag()
            await rag.ainsert(full_text)
    except Exception as e:
        return f"Error inserting into lightrag: {e}"
