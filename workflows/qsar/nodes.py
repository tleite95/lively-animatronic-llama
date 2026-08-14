from pathlib import Path
import shutil
import json

from state import RAGIngestionState

from scripts.util import utc_now
from scripts.run import run_prompt, run_ingest


def init(state: RAGIngestionState):
    # Load config
    # Create necessary artifact directories, add all paths to run manifest
    pass

