from pathlib import Path
import json

def jsonl_verify(state) -> str:
    stream_path = Path(state["manifest"]["processed_jsonl"])
    if stream_path.is_file() and stream_path.stat().st_size > 0:
        valid = True

        with stream_path.open("r", encoding="utf-8") as file:
            for line in file:
                if not (stripped := line.strip()):
                    continue

                try:
                    json.loads(stripped)
                except:
                    valid = False
                    break

        if valid:
            return "continue"

    if state["try_number"] > 3:
        return "abort"

    return "retry"

def rag_verify(state) -> str:
    print("WARNING: RAG verification is a stub")
    return "valid"

def check_wiki_done_ingesting(state) -> bool:
    return len(state["wiki_doc_queue"]) == 0

def check_lightrag_done_ingesting(state) -> bool:
    return len(state["lightrag_doc_queue"]) == 0