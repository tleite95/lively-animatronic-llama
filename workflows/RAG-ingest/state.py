from typing import TypedDict

import yaml

from scripts.util import utc_now

class RagIngestionRunManifest(TypedDict):
    run_dir: str
    md_dir: str
    txt_dir: str
    full_text: str
    final_jsonl: str
    processed_jsonl: str
    raw_jsonl: str
    quarantined_jsonl: str
    log_folder: str
    report_folder: str
    qa_report: str
    major_change_report: str
    preparation_report: str


class RagIngestionConfig(TypedDict):
    artifacts: str
    pdfs: str


# note: per-document summaries
class RagIngestionOutputSummaries(TypedDict):
    wiki: list[str]
    lightrag: list[str]


class RAGIngestionState(TypedDict, total=False):
    run_id: str
    try_number: int
    creation_time: str
    config: RagIngestionConfig
    manifest: RagIngestionRunManifest


    wiki_doc_queue: list[str]
    current_wiki_doc: list[str]

    lightrag_doc_queue: list[str]
    current_lightrag_doc: list[str]

    wiki_ingest_output: str
    wiki_write_output: str
    summaries: RagIngestionOutputSummaries


def make_initial_state(config_file: str) -> RAGIngestionState:
    try:
        with open(config_file, "r") as cfg:
            config_data = yaml.safe_load(cfg) or {}
    except:
        config_data = {}

    now = utc_now()

    return {
        "run_id": "unset",
        "try_number": 1,
        "creation_time": now,
        "config": config_data,
        "manifest": {
            "run_dir": "",
            "md_dir": "",
            "txt_dir": "",
            "full_text": "",
            "final_jsonl": "",
            "processed_jsonl": "",
            "raw_jsonl": "",
            "quarantined_jsonl": "",
            "log_folder": "",
            "report_folder": "",
            "qa_report": "",
            "major_change_report": "",
            "preparation_report": "",
        },
        "wiki_doc_queue": [],
        "current_doc": [],
        "lightrag_doc_queue": [],
        "current_lightrag_doc": [],
        "wiki_ingest_output": "",
        "wiki_write_output": "",
        "summaries": {
            "wiki": [],
            "lightrag": [],
        }
    }