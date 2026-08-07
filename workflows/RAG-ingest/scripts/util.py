import os
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict

import opencode2_client as opencode2
import ingest

type JsonValue = None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
type JsonDict = dict[str, JsonValue]

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

class AllowExtraPydanticModel(BaseModel):
    model_config = ConfigDict(extra="allow")

def run_prompt(prompt: str, agent: str, skill: str | None = None, model: str = "devstral-small", run_id: str | None = None):
    args = {
        "base_url": "127.0.0.1:4096",
        "directory": os.getcwd(),
        "agent": agent,
        "skill": skill,
        "provider": "ssec-litellm",
        "model": model,
        "variant": None,
        "prompt": prompt,
        "title": run_id,
        "timeout": 600.0,
        "quiet": True,
        "password": "alpine"
    }

    opencode2.chat(args)

def run_ingest(pdf_folder: str, manifest: any):
    args = {
        "pdf_folder": pdf_folder,
        "md_folder": manifest["md_dir"],
        "txt_folder": manifest["txt_dir"],
        "output_jsonl": manifest["processed_jsonl"],
        "raw_jsonl": manifest["raw_jsonl"],
        "quarantined_jsonl": manifest["quarantined_jsonl"],
        "log_folder": manifest["log_folder"],
        "qa_report": manifest["qa_report"],
        "major_change_report": manifest["major_change_report"],
    }
    
    ingest.run_pipeline(args)