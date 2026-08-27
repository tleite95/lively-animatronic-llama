#!/usr/bin/env python3
"""
PubChem API wrapper module for read-across workflow.

This module provides web access to PubChem data while maintaining
compatibility with the read_across.py module interface.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# API Configuration
API_CACHE_DIR = Path(os.environ.get("PUBCHEM_CACHE_DIR", ".pubchem_cache"))
API_RATE_LIMIT = float(os.environ.get("PUBCHEM_RATE_LIMIT", "10.0"))  # requests per minute

# Path to the pubchem-database skill scripts
SKILL_SCRIPTS_PATH = Path("/home/avam11/lively-animatronic-llama/.agents/skills/pubchem-database/scripts")


class PubChemAPIError(Exception):
    """Custom exception for PubChem API errors."""
    pass


class PubChemAPI:
    """Wrapper for PubChem web API using the pubchem-database skill."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or API_CACHE_DIR
        self.cache_dir.mkdir(exist_ok=True)
        self.last_request_time = 0.0
        self.request_count = 0
    
    def _get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate a cache key from endpoint and parameters."""
        param_str = json.dumps(params, sort_keys=True)
        combined = f"{endpoint}?{param_str}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _read_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Read cached response."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text())
            except Exception:
                return None
        return None
    
    def _write_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Write response to cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            cache_file.write_text(json.dumps(data, indent=2))
        except Exception:
            pass
    
    def _enforce_rate_limit(self) -> None:
        """Enforce API rate limiting."""
        now = time.time()
        time_since_last = now - self.last_request_time
        
        if time_since_last < 60.0:  # Within the last minute
            if self.request_count >= API_RATE_LIMIT:
                sleep_time = 60.0 - time_since_last
                time.sleep(sleep_time)
                self.request_count = 0
                self.last_request_time = time.time()
            self.request_count += 1
        else:
            self.request_count = 1
            self.last_request_time = now
    
    def _call_skill_script(self, command: str, args: List[str]) -> Dict[str, Any]:
        """Call the pubchem-database skill script and return parsed JSON."""
        self._enforce_rate_limit()
        
        script_path = SKILL_SCRIPTS_PATH / "pubchem_api.py"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            cmd = ["python", str(script_path), command] + args + ["--output", output_path]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.returncode != 0:
                raise PubChemAPIError(f"Skill script failed: {result.stderr}")
            
            with open(output_path, 'r') as f:
                return json.load(f)
                
        except subprocess.CalledProcessError as e:
            raise PubChemAPIError(f"Failed to execute skill script: {e}")
        except json.JSONDecodeError as e:
            raise PubChemAPIError(f"Failed to parse JSON output: {e}")
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def get_compound_records(self, compound_id: str, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Get PubChem records for a specific compound using the pubchem-database skill."""
        # Convert compound_id to CID if needed
        if not compound_id.startswith("CID") and compound_id.isdigit():
            compound_id = f"CID{compound_id}"
        
        # Extract CID number
        cid = compound_id.replace("CID", "")
        
        params = {"response_type": "json"}
        cache_key = self._get_cache_key(f"compound/{compound_id}", params)
        
        if use_cache:
            cached = self._read_cache(cache_key)
            if cached:
                return cached.get("records", [])
        
        try:
            # Use the pubchem-database skill to get assay data
            assay_data = self._call_skill_script("assays", ["--cid", cid])
            
            # Use the pubchem-database skill to get properties
            props_data = self._call_skill_script("properties", ["--cid", cid])
            
            # Use the pubchem-database skill to get pharmacology data
            pharmacology_data = self._call_skill_script("pharmacology", ["--cid", cid])
            
            # Convert to Tox21-like format
            records = self._convert_to_tox21_format(assay_data, props_data, pharmacology_data)
            
            if use_cache:
                self._write_cache(cache_key, {"records": records})
            
            return records
        except PubChemAPIError:
            return []
    
    def _convert_to_tox21_format(self, assays: Dict[str, Any], props: Dict[str, Any], pharmacology: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert PubChem data to Tox21-like format for compatibility."""
        records = []
        
        # Extract compound name from properties
        compound_name = "Unknown"
        if isinstance(props, dict) and "Properties" in props:
            for prop in props.get("Properties", []):
                if prop.get("Name") == "CanonicalSMILES":
                    compound_name = f"Compound with SMILES: {prop.get('Value', {})}"
                    break
        
        # Process assay data from the pubchem-database skill
        if isinstance(assays, dict) and "Table" in assays:
            table = assays["Table"]
            columns = table.get("Columns", {}).get("Column", [])
            rows = table.get("Row", [])
            
            # Find relevant column indices based on actual assay data structure
            assay_name_idx = None
            outcome_idx = None
            target_accession_idx = None
            
            for i, col_name in enumerate(columns):
                if col_name == "Assay Name":
                    assay_name_idx = i
                elif col_name == "Activity Outcome":
                    outcome_idx = i
                elif col_name == "Target Accession":
                    target_accession_idx = i
            
            for row in rows:
                cells = row.get("Cell", [])
                
                # Only process if we have enough cells for the indices we need
                if len(cells) > max([i for i in [assay_name_idx, outcome_idx, target_accession_idx] if i is not None]):
                    assay_name = cells[assay_name_idx] if assay_name_idx is not None else "Unknown"
                    activity_outcome = cells[outcome_idx] if outcome_idx is not None else None
                    target_accession = cells[target_accession_idx] if target_accession_idx is not None else ""
                    
                    record = {
                        "chemical_name": compound_name,
                        "compound": compound_name,
                        "endpoint": assay_name,  # Use assay name as endpoint
                        "assay_name": assay_name,
                        "active": self._map_activity(activity_outcome),
                        "source": "PubChem",
                        "study": assay_name,
                        "evidence": f"PubChem assay: {assay_name}",
                        "target_class": target_accession,  # Use target accession as target class
                        "mechanism_of_action": "",
                    }
                    records.append(record)
        
        # Process pharmacology data for additional information
        if isinstance(pharmacology, dict) and "Record" in pharmacology:
            record = pharmacology["Record"]
            if "Section" in record:
                for section in record["Section"]:
                    if section.get("TOCHeading") == "Pharmacology and Biochemistry":
                        if "Section" in section:
                            for sub_section in section["Section"]:
                                if "Information" in sub_section:
                                    info = sub_section["Information"]
                                    if isinstance(info, list):
                                        for item in info:
                                            if isinstance(item, dict) and "Value" in item:
                                                value = item["Value"]
                                                if isinstance(value, dict):
                                                    if "StringWithMarkup" in value:
                                                        string_with_markup = value["StringWithMarkup"]
                                                        if isinstance(string_with_markup, dict):
                                                            text = string_with_markup.get("String", "")
                                                            # Add as additional evidence
                                                            records.append({
                                                                "chemical_name": compound_name,
                                                                "compound": compound_name,
                                                                "endpoint": "Pharmacology",
                                                                "assay_name": sub_section.get("TOCHeading", ""),
                                                                "active": None,
                                                                "source": "PubChem",
                                                                "study": "Pharmacology",
                                                                "evidence": f"Pharmacology: {text}",
                                                                "mechanism_of_action": text,
                                                            })
        
        return records
    
    def _map_activity(self, activity_data: Any) -> Optional[bool]:
        """Map PubChem activity data to Tox21 active/inactive format."""
        if not activity_data:
            return None
            
        if isinstance(activity_data, dict):
            outcome = activity_data.get("activity_outcome", "").lower()
            if outcome in ["active", "positive", "yes"]:
                return True
            elif outcome in ["inactive", "negative", "no"]:
                return False
        
        if isinstance(activity_data, str):
            outcome = activity_data.lower()
            if outcome in ["active", "positive", "yes"]:
                return True
            elif outcome in ["inactive", "negative", "no"]:
                return False
        
        return None


def load_tox21_records_from_api(
    chemical_id: str,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    cache_dir: Optional[Path] = None,
    use_cache: bool = True
) -> List[Dict[str, Any]]:
    """
    Load Tox21-compatible records from PubChem API using the pubchem-database skill.
    
    Args:
        chemical_id: Chemical identifier (CID, name, or InChI)
        api_url: Override the default API URL (not used when calling skill)
        api_key: API authentication key (not used when calling skill)
        cache_dir: Directory for caching API responses
        use_cache: Whether to use cached responses
    
    Returns:
        List of Tox21-compatible records as dictionaries
    """
    # Temporarily override environment variables
    original_cache = API_CACHE_DIR
    
    if cache_dir:
        os.environ["PUBCHEM_CACHE_DIR"] = str(cache_dir)
    
    try:
        api = PubChemAPI(cache_dir)
        return api.get_compound_records(chemical_id, use_cache)
    finally:
        # Restore original values
        os.environ["PUBCHEM_CACHE_DIR"] = str(original_cache)


__all__ = [
    "PubChemAPI",
    "PubChemAPIError",
    "load_tox21_records_from_api",
    "API_CACHE_DIR",
    "API_RATE_LIMIT",
]