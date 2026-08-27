#!/usr/bin/env python3
"""Configuration and helper functions for ADMET secondary bucket mapping."""

import json
from pathlib import Path


def load_config():
    """Load the ADMET secondary bucket mapping configuration."""
    config_path = Path(__file__).parent / "admet_secondary_bucket_mapping.json"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_json(path):
    """Load JSON from a file path."""
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


if __name__ == "__main__":
    # Test the configuration loading
    config = load_config()
    print("Configuration loaded successfully")
    print(f"Families: {list(config['families'].keys())}")
    print(f"Buckets: {list(config['annotation_groups'].keys())}")