import os
import argparse

import scripts.opencode2_client as opencode2
import scripts.ingest as ingest

def run_prompt(prompt: str, agent: str, skill: str | None = None, model: str = "devstral-small", run_id: str | None = None):
    args = {
        "base_url": "http://127.0.0.1:4096",
        "username": "opencode",
        "password": "alpine",
        "directory": os.getcwd(),
        "agent": agent,
        "skill": skill,
        "provider": "ssec-litellm",
        "model": model,
        "variant": None,
        "prompt": prompt,
        "title": run_id,
        "timeout": 600.0,
        "quiet": False,
        "log_file": None,
    }

    return opencode2.chat(argparse.Namespace(**args))

def run_ingest(pdf_folder: str, manifest: any):
    args = {
        "pdf_folder": pdf_folder,
        "pdf_glob": "**/*.pdf",
        "md_folder": manifest["md_dir"],
        "txt_folder": manifest["txt_dir"],
        "output_jsonl": manifest["processed_jsonl"],
        "quarantined_jsonl": manifest["quarantined_jsonl"],
        "raw_jsonl": manifest["raw_jsonl"],
        "qa_report": manifest["qa_report"],
        "major_change_report": manifest["major_change_report"],
        "log_folder": manifest["log_folder"],
        "no_crossref": False,
        "crossref_mailto": None,
        "min_merge_tokens": 80,
        "max_merge_tokens": 340,
        "limit": None,
    }
    
    return ingest.run_pipeline(argparse.Namespace(**args))