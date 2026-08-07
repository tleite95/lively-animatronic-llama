from pathlib import Path
import shutil
import json

from state import RAGIngestionState

from scripts.util import utc_now, run_prompt, run_ingest
from scripts.ingest import run


def init(state: RAGIngestionState):
    # Load config
    artifact_dir = Path(state["config"]["artifacts"])

    # Create necessary artifact directories, add all paths to run manifest
    n_runs = sum(1 for item in (artifact_dir / "runs").iterdir() if item.is_dir())
    run_id = f"{n_runs}_{utc_now()}"
    state["run_id"] = run_id

    run_dir = artifact_dir / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    state["manifest"]["run_dir"] = run_dir.resolve()

    jsonl_processed_path = (run_dir / "ingestion_stream.jsonl")
    state["manifest"]["processed_jsonl"] = jsonl_processed_path.resolve()
    
    jsonl_final_path = (run_dir / "RAG_stream.jsonl")
    state["manifest"]["final_jsonl"] = jsonl_final_path.resolve()

    jsonl_quarantine_path = (run_dir / "quarantine_stream.jsonl")
    state["manifest"]["quarantined_jsonl"] = jsonl_quarantine_path.resolve()

    jsonl_raw_path = (run_dir / "raw_stream.jsonl")
    state["manifest"]["raw_jsonl"] = jsonl_raw_path.resolve()

    md_path = (run_dir / "md")
    md_path.mkdir(parents=True, exists_ok=True)
    state["manifest"]["md_dir"] = md_path.resolve()

    txt_path = (run_dir / "txt")
    txt_path.mkdir(parents=True, exists_ok=True)
    state["manifest"]["txt_dir"] = txt_path.resolve()

    log_path = (run_dir / "logs")
    log_path.mkdir(parents=True, exists_ok=True)
    state["manifest"]["log_folder"] = log_path.resolve()

    report_path = (run_dir / "reports")
    report_path.mkdir(parents=True, exists_ok=True)
    state["manifest"]["report_folder"] = report_path.resolve()

    qa_report_path = report_path / "ingestion_qa_report.json"
    state["manifest"]["qa_report"] = qa_report_path.resolve()

    major_change_report_path = report_path / "major_change_report.json"
    state["manifest"]["major_change_report"] = major_change_report_path.resolve()

    preparation_report_path = report_path / "preparation_report.json"
    state["manifest"]["preparation_report"] = preparation_report_path.resolve()
    

def pdf2jsonl(state: RAGIngestionState):
    run_ingest(state["config"]["pdf_folder"], state["manifest"])

def reset(state: RAGIngestionState):
    state["try_number"] += 1

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
                file.unlink
    
    Path(state["manifest"]["processed_jsonl"]).unlink()
    Path(state["manifest"]["final_jsonl"]).unlink()
    Path(state["manifest"]["quarantined_jsonl"]).unlink()
    Path(state["manifest"]["raw_jsonl"]).unlink()
    Path(state["manifest"]["qa_report"]).unlink()
    Path(state["manifest"]["major_change_report"]).unlink()
    Path(state["manifest"]["preparation_report"]).unlink()

def fail_jsonl_verification(state: RAGIngestionState):
    shutil.rmtree(state["manifest"]["run_dir"], ignore_errors=True)
    print("JSONL verification failed -- unrecoverable error.")

def jsonl_cleanup(state: RAGIngestionState):
    refs =  (
        f"- First-pass JSONL stream: {state['manifest']['clean_jsonl']}\n"
        f"- Quarantined chunks: {state['manifest']['quarantined_jsonl']}\n"
        f"- Run logs: {state['manifest']['log_folder']}\n"
        f"- QA Report: {state['manifest']['qa_report']}\n"
        f"- Major changes during cleanup step: {state['manifest']['major_change_report']}\n"
    )

    if state['manifest']['full_text'] is not None:
        refs += f"- Full-text export: {state['manifest']['full_text']}\n"

    prompt = (
        "Find the first pass at a cleanup of the JSONL stream in the reference files. Produce the artifacts on disk at the following locations:\n"
        f"- `final_jsonl_path`: {state['anifest']['final_jsonl']}\n"
        f"- `report_filepath`: {state['anifest']['preparation_report']}\n\n"
        "Reference Files:\n"
        f"{refs}"
    )

    run_prompt(prompt, agent="json-cleaner", skill="jsonl-to-rag", run_id=state["run_id"])


def fail_jsonl_cleanup(state: RAGIngestionState):
    shutil.rmtree(state["manifest"]["run_dir"], ignore_errors=True)
    print("JSONL cleanup failed -- unrecoverable error.")

def ragchunk_verify(state: RAGIngestionState):
    # QA report pass
    pass

def branch_lightrag_wiki(state: RAGIngestionState):
    doc_queue = set()

    with open(state["manifest"]["final_jsonl"], "r") as ingestion_stream:
        for line in ingestion_stream:
            doc_queue.add(json.loads(line.strip())["document_name"])

    state["wiki_doc_queue"] = list(doc_queue)
    state["lightrag_doc_queue"] = list(doc_queue)

def empty(state: RAGIngestionState):
    pass

def batch_chunks_by_document__lightrag(state: RAGIngestionState):
    return _batch_chunks_by_documents(state, "lightrag")

def batch_chunks_by_document__wiki(state: RAGIngestionState):
    return _batch_chunks_by_documents(state, "wiki")

# TODO: might want to have some failsafe in here in case the queue is empty
def _batch_chunks_by_documents(state: RAGIngestionState, branch: str):
    doc_q = f"{branch}_doc_queue"
    cur_doc = f"current_{branch}_doc"

    doc_name = state[doc_q].pop(0)

    chunks = []
    with open(state["manifest"]["final_jsonl"], "r") as ingestion_stream:
        for line in ingestion_stream:
            record = json.loads(line.strip())
            if record["document_name"] == doc_name:
                chunks.append(record)
    state[cur_doc] = chunks

    full_text_file = Path(state["manifest"]["md_folder"]) / f"{Path(doc_name).stem}.md"
    if not full_text_file.exists():
        full_text_file = Path(state["manifest"]["txt_folder"]) / f"{Path(doc_name).stem}.txt"
    if full_text_file.exists():
        full_text_file = full_text_file.resolve()
    else:
        full_text_file = None
    state["manifest"]["full_text"] = full_text_file

def wiki_ingest(state: RAGIngestionState):
    doc_stream = "\n".join(state["current_wiki_doc"])

    prompt = f"Prepare the following JSONL stream for ingestion into the wiki: \n\n{doc_stream}"
    response = run_prompt(prompt, agent="wiki-agent", skill="wiki-ingest", run_id=state["run_id"])
    state["wiki_ingest_output"] = response

def wiki_write(state: RAGIngestionState):
    report = state["wiki_ingest_output"]
    prompt = (
        "A document has just been ingested for insertion into the wiki. "
        "Edit the relevant wiki pages to add the new information. "
        "Create new pages only as needed. "
        f"Here is the ingestion report:\n\n{report}"
    )
    response = run_prompt(prompt, agent="wiki-agent", skill="wiki-write", run_id=state["run_id"])
    state["wiki_write_output"] = response

def wiki_verify(state: RAGIngestionState):
    report = state["wiki_write_output"]
    prompt = (
        "A series of changes has just been made to the wiki. "
        "Verify all newly inserted information, newly created page, and new claims. "
        "Make sure you check for contradictions across the affected pages as well as the wiki as a whole. "
        f"Here is the insertion report:\n\n{report}"
    )
    response = run_prompt(prompt, agent="wiki-agent", skill="wiki-verify", run_id=state["run_id"])
    state["summaries"]["wiki"].append(response)


def prepare_lightrag(state: RAGIngestionState):
    # append citation metadata to text
    print("WARNING: lightrag branch is a stub")

def insert_into_lightrag(state: RAGIngestionState):
    # async bulk import of text chunks
    print("WARNING: lightrag branch is a stub")