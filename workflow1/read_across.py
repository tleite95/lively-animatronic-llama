from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Sequence

import numpy as np

try:
    from rdkit import Chem, DataStructs
    from rdkit.Chem import AllChem
except Exception as e:  # pragma: no cover
    raise RuntimeError("RDKit is required for read_across.py.") from e

try:
    from ctx_api import fetch_chemical_details, fetch_compound_bundle, resolve_chemical, resolve_query_chemical
except Exception:  # pragma: no cover
    fetch_compound_bundle = None  # type: ignore
    resolve_chemical = None  # type: ignore
    resolve_query_chemical = None  # type: ignore

# -------------------------
# Configuration
# -------------------------

READ_ACROSS_REFERENCE_FILE = Path(os.environ.get("READ_ACROSS_REFERENCE_FILE", "reference_library.json"))
READ_ACROSS_CACHE_FILE = Path(os.environ.get("READ_ACROSS_CACHE_FILE", "read_across_cache.json"))
READ_ACROSS_TOP_K = int(os.environ.get("READ_ACROSS_TOP_K", "5"))
READ_ACROSS_MIN_SIMILARITY = float(os.environ.get("READ_ACROSS_MIN_SIMILARITY", "0.25"))
READ_ACROSS_ALLOW_REMOTE_RESOLUTION = os.environ.get("READ_ACROSS_ALLOW_REMOTE_RESOLUTION", "true").lower() == "true"
READ_ACROSS_REMOTE_CACHE = os.environ.get("READ_ACROSS_REMOTE_CACHE", "true").lower() == "true"
FP_RADIUS = int(os.environ.get("READ_ACROSS_FP_RADIUS", "2"))
FP_NBITS = int(os.environ.get("READ_ACROSS_FP_NBITS", "2048"))

#So generic terms don't affect scoring
STOPWORDS = {
    "a", "an", "and", "of", "the", "to", "in", "for", "with", "via", "by", "from",
    "is", "are", "be", "as", "at", "or", "this", "that", "these", "those", "on",
    "chemical", "compound", "target", "profile", "assay", "endpoint", "effect", "data",
    "study", "result", "results", "source", "evidence", "summary", "reference",
}
# Evidence fields that are considered for scoring and enrichment
TEXT_FIELDS = (
    "name", "chemical_name", "compound", "cas", "inchikey", "smiles",
    "target_class", "mechanism_of_action", "endpoint", "assay", "assay_name",
    "summary", "evidence", "reasoning", "source", "study", "notes",
    "label", "labels", "tags", "stressor", "aop", "liabilities", "endpoints",
)


# -------------------------
# Resolution helpers
# -------------------------
def _merge_nonempty_dict(base: Dict[str, Any], extra: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(base, dict):
        base = {}
    if not isinstance(extra, dict):
        return base
    merged = dict(base)
    for key, value in extra.items():
        if value not in (None, "", [], {}, ()):
            merged[key] = value
    return merged


def _resolve_query_structure(chemical: str, *, prefer_ctx: bool = True) -> Dict[str, Any]:
    query = str(chemical or "").strip()
    resolved: Dict[str, Any] = {"query": query, "status": "not_found", "name": query, "smiles": ""}

    # Validate chemical name format before processing
    if not _is_valid_chemical_name(query):
        resolved["status"] = "invalid_name_format"
        resolved["error"] = "Chemical name format is invalid"
        return resolved

    if prefer_ctx:
        for resolver in (resolve_query_chemical, resolve_chemical):
            if resolver is None:
                continue
            try:
                candidate = resolver(query)
                if isinstance(candidate, dict):
                    resolved = _merge_nonempty_dict(resolved, candidate)
                    if resolved.get("smiles"):
                        break
            except Exception:
                continue

    if not resolved.get("smiles") and fetch_chemical_details is not None:
        ident = str(resolved.get("dtxsid") or resolved.get("dtxcid") or "").strip()
        if ident:
            try:
                details = fetch_chemical_details(ident)
                if isinstance(details, dict):
                    resolved = _merge_nonempty_dict(resolved, details)
                    if not resolved.get("name"):
                        resolved["name"] = query
            except Exception:
                pass

    if not resolved.get("smiles") and is_probable_smiles(query):
        canon = _canonicalize_smiles(query)
        if canon:
            resolved = _merge_nonempty_dict(
                resolved,
                {"query": query, "status": "ok", "name": query, "smiles": canon, "source": "direct_smiles"},
            )

    return resolved


# -------------------------
# Cache helpers
# -------------------------

#Pulls possible names from the target profile and similar chemicals, reference chemicals, analog chemicals, and seed chemicals
def _ctx_seed_names(target_profile: Optional[Dict[str, Any]], mies: Optional[Sequence[Dict[str, Any]]] = None) -> List[str]:
    """Collect candidate analog names from the ADMET target profile."""
    if not isinstance(target_profile, dict):
        return []

    names: List[str] = []
    props = target_profile.get("properties", {}) if isinstance(target_profile.get("properties", {}), dict) else {}

    for key in ("similar_chemicals", "reference_chemicals", "analog_chemicals", "seed_chemicals"):
        names.extend(_as_list(target_profile.get(key)))
        names.extend(_as_list(props.get(key)))

    if mies:
        for mie in mies:
            if isinstance(mie, dict):
                for key in ("similar_chemicals", "reference_chemicals", "analog_chemicals"):
                    names.extend(_as_list(mie.get(key)))

    return [n for n in dict.fromkeys(str(n).strip() for n in names if str(n).strip())]


def _ctx_seed_reference_records(
    target_profile: Optional[Dict[str, Any]],
    mies: Optional[Sequence[Dict[str, Any]]] = None,
    *,
    max_seeds: int = 8,
) -> List[Dict[str, Any]]:
    """Build lightweight reference records from CTX-resolved analogous chemicals."""
    seed_names = _ctx_seed_names(target_profile, mies)
    if not seed_names:
        return []

    records: List[Dict[str, Any]] = []
    for seed in seed_names[:max_seeds]:
        try:
            bundle: Dict[str, Any] = fetch_compound_bundle(seed) if fetch_compound_bundle is not None else {}
        except Exception:
            bundle = {}

        try:
            resolved = resolve_chemical(seed) if resolve_chemical is not None else {}
        except Exception:
            resolved = {}

        chem: Dict[str, Any] = {}
        if isinstance(bundle.get("chemical"), dict):
            chem = dict(bundle["chemical"])
        if isinstance(bundle.get("chemical_details"), dict):
            chem = _merge_nonempty_dict(chem, bundle["chemical_details"])
        if isinstance(resolved, dict):
            chem = _merge_nonempty_dict(chem, resolved)

        smiles = str(
            chem.get("smiles")
            or chem.get("CanonicalSMILES")
            or chem.get("canonical_smiles")
            or chem.get("IsomericSMILES")
            or chem.get("isomeric_smiles")
            or ""
        ).strip()
        if not smiles:
            continue

        labels: List[str] = []
        if isinstance(target_profile, dict):
            labels.extend(_as_list(target_profile.get("liabilities", [])))
            labels.extend(_as_list(target_profile.get("known_targets", [])))
            props = target_profile.get("properties", {}) if isinstance(target_profile.get("properties", {}), dict) else {}
            labels.extend(_as_list(props.get("known_targets", [])))
        labels.append(seed)

        summary = f"CTX seed record for {seed}"
        if isinstance(bundle.get("chemical_details"), dict):
            details = bundle["chemical_details"]
            summary = str(details.get("title") or details.get("name") or details.get("preferred_name") or summary)

        record = normalize_reference_record(
            {
                "name": str(chem.get("name") or seed).strip() or seed,
                "chemical_name": str(chem.get("name") or seed).strip() or seed,
                "smiles": smiles,
                "endpoint": ", ".join(
                    v for v in [
                        str(bundle.get("bioactivity") and "bioactivity" or "").strip(),
                        str(bundle.get("exposure") and "exposure" or "").strip(),
                        str(bundle.get("hazard") and "hazard" or "").strip(),
                    ] if v
                ),
                "labels": list(dict.fromkeys(v for v in labels if v)),
                "source": "ctx_seed",
                "summary": summary,
                "raw": {
                    "ctx_bundle": bundle,
                    "resolved": resolved,
                },
            }
        )
        if record:
            records.append(record)

    return _dedupe_reference_records(records)


# -------------------------
# Cache helpers
# -------------------------

def _read_json_file(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None

def _write_json_file(path: Path, data: Any) -> None:
    try:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        pass


def _load_cache() -> Dict[str, Any]:
    data = _read_json_file(READ_ACROSS_CACHE_FILE)
    return data if isinstance(data, dict) else {}


def _save_cache(cache: Dict[str, Any]) -> None:
    if READ_ACROSS_REMOTE_CACHE:
        _write_json_file(READ_ACROSS_CACHE_FILE, cache)


def _normalize_text(value: Any) -> str:
    text = str(value or "").lower().strip()
    remove_pattern = os.environ.get("READ_ACROSS_REMOVE_PATTERN", r"[^a-z0-9]+")
    whitespace_pattern = os.environ.get("READ_ACROSS_WHITESPACE_PATTERN", r"\s+")
    text = re.sub(remove_pattern, " ", text)
    return re.sub(whitespace_pattern, " ", text).strip()

def _tokens(value: Any) -> set[str]:
    return {t for t in _normalize_text(value).split() if t and t not in STOPWORDS}

def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, tuple):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, set):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(v).strip() for v in parsed if str(v).strip()]
            except Exception:
                pass
        return [p.strip() for p in re.split(r"[|;,]\s*", s) if p.strip()]
    return [str(value).strip()] if str(value).strip() else []


def _cache_key(kind: str, value: str) -> str:
    return _normalize_text(f"{kind}:{value}")


def _cache_get(kind: str, value: str) -> Optional[Any]:
    cache = _load_cache()
    return cache.get(_cache_key(kind, value)) if isinstance(cache, dict) else None


def _cache_set(kind: str, value: str, data: Any) -> None:
    cache = _load_cache()
    if not isinstance(cache, dict):
        cache = {}
    cache[_cache_key(kind, value)] = data
    _save_cache(cache)


# -------------------------
# Chemistry helpers
# -------------------------


def _canonicalize_smiles(smiles: str) -> Optional[str]:
    if not smiles:
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return Chem.MolToSmiles(mol, canonical=True)


def fingerprint_from_smiles(smiles: str):
    mol = Chem.MolFromSmiles(smiles or "")
    if mol is None:
        return None
    return AllChem.GetMorganFingerprintAsBitVect(mol, radius=FP_RADIUS, nBits=FP_NBITS)


def tanimoto_from_smiles(smiles_a: str, smiles_b: str) -> float:
    fp_a = fingerprint_from_smiles(smiles_a)
    fp_b = fingerprint_from_smiles(smiles_b)
    if fp_a is None or fp_b is None:
        return 0.0
    return float(DataStructs.TanimotoSimilarity(fp_a, fp_b))


def is_probable_smiles(value: str) -> bool:
    s = str(value or "").strip()
    return bool(s) and len(s) > 2 and any(ch in s for ch in ("=", "#", "[", "]", "(", ")"))


def _is_valid_chemical_name(name: str) -> bool:
    """Check if a chemical name has a valid format."""
    if not name or not isinstance(name, str):
        return False
    
    name = name.strip()
    if not name:
        return False
    
    # Basic validation: name should contain at least some alphabetic characters
    # and not be just numbers or special characters
    if not any(c.isalpha() for c in name):
        return False
    
    # Check for common patterns that indicate invalid input
    invalid_patterns = [
        r'^\s*$',  # empty or whitespace only
        r'^\d+$',  # numbers only
        r'^[^a-zA-Z0-9\s\-\.\,\(\)\/]+$',  # mostly special characters
    ]
    
    for pattern in invalid_patterns:
        if re.match(pattern, name):
            return False
    
    return True


# -------------------------
# File loading
# -------------------------


def _read_table_file(path: Path) -> List[Dict[str, Any]]:
    delim = "\t" if path.suffix.lower() in {".tsv", ".tab"} else ","
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter=delim)
            return [dict(row) for row in reader]
    except Exception:
        return []


def _read_jsonl_file(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except Exception:
                    continue
                if isinstance(item, dict):
                    normalized = normalize_reference_record(item)
                    if normalized:
                        rows.append(normalized)
    except Exception:
        pass
    return rows


def _coerce_records(obj: Any) -> List[Dict[str, Any]]:
    if obj is None:
        return []
    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    if isinstance(obj, dict):
        if isinstance(obj.get("records"), list):
            return [x for x in obj["records"] if isinstance(x, dict)]
        return [obj]
    return []

#Converts raw input into standard read-across format
def normalize_reference_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(rec, dict):
        return {}
    rec = dict(rec)

    name = (
        rec.get("name") or rec.get("chemical_name") or rec.get("compound") or rec.get("sample_name") or
        rec.get("preferred_name") or rec.get("title") or rec.get("tox21_id") or rec.get("record_id") or "unknown"
    )
    name = str(name).strip()

    smiles = str(rec.get("smiles") or rec.get("canonical_smiles") or rec.get("isomeric_smiles") or "").strip()
    if smiles:
        canon = _canonicalize_smiles(smiles)
        if canon:
            smiles = canon

    aliases: List[str] = []
    for key in ("aliases", "alias", "synonyms", "names", "sample_name", "cas", "pubchem_cid", "pubchem_sid", "tox21_id"):
        aliases.extend(_as_list(rec.get(key)))
    aliases = list(dict.fromkeys(v for v in aliases if v))

    assays = rec.get("assays") or []
    normalized_assays = []
    endpoints = []
    labels = []
    if isinstance(assays, list):
        for a in assays:
            if not isinstance(a, dict):
                continue
            assay = {
                "protocol_name": str(a.get("protocol_name") or a.get("assay_name") or a.get("name") or "").strip(),
                "assay_outcome": str(a.get("assay_outcome") or a.get("outcome") or a.get("result") or "").strip().lower(),
                "sample_name": str(a.get("sample_name") or a.get("name") or "").strip(),
                "tox21_id": str(a.get("tox21_id") or a.get("TOX21_ID") or "").strip(),
            }
            if assay["protocol_name"]:
                endpoints.append(assay["protocol_name"])
            if assay["assay_outcome"]:
                endpoints.append(assay["assay_outcome"])
            if assay["sample_name"]:
                labels.append(assay["sample_name"])
            if assay["tox21_id"]:
                labels.append(assay["tox21_id"])
            for key in ("ac50", "efficacy", "reproducibility", "curve_rank", "flag"):
                if a.get(key) is not None:
                    assay[key] = a.get(key)
            if any(assay.values()):
                normalized_assays.append(assay)

    record = {
        "record_id": str(rec.get("record_id") or rec.get("tox21_id") or rec.get("sample_id") or rec.get("pubchem_cid") or "unknown").strip(),
        "tox21_id": str(rec.get("tox21_id") or rec.get("TOX21_ID") or rec.get("TOX21ID") or "").strip(),
        "name": name,
        "sample_name": str(rec.get("sample_name") or rec.get("NAME") or rec.get("SAMPLE_NAME") or name).strip(),
        "cas": str(rec.get("cas") or rec.get("CAS") or "").strip(),
        "pubchem_cid": str(rec.get("pubchem_cid") or rec.get("PUBCHEM_CID") or "").strip(),
        "pubchem_sid": str(rec.get("pubchem_sid") or rec.get("PUBCHEM_SID") or "").strip(),
        "smiles": smiles,
        "endpoint": ", ".join(dict.fromkeys(endpoints)),
        "labels": list(dict.fromkeys(labels + aliases + _as_list(rec.get("labels")) + _as_list(rec.get("tags")) + _as_list(rec.get("liabilities")))),
        "source": "; ".join(_as_list(rec.get("source_files")) or ["library_builder"]),
        "summary": rec.get("assay_summary") or rec.get("summary") or {},
        "assays": normalized_assays,
        "aliases": aliases,
        "raw": rec,
    }

    if not record["name"] or record["name"] == "unknown":
        return {}
    if not record["smiles"] and not record["tox21_id"] and not record["cas"] and not record["pubchem_cid"]:
        return {}
    return record

#Removes duplicate records
def _dedupe_reference_records(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduped: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        candidate = normalize_reference_record(row)
        if not candidate:
            continue
        key = candidate.get("smiles") or candidate.get("tox21_id") or candidate.get("cas") or candidate.get("pubchem_cid") or candidate.get("record_id") or candidate.get("name")
        if not key:
            continue
        key = str(key).strip().lower()
        if key not in deduped:
            deduped[key] = candidate
            continue
        existing = deduped[key]
        for field in ("name", "tox21_id", "sample_name", "cas", "pubchem_cid", "pubchem_sid", "record_id"):
            if not existing.get(field) and candidate.get(field):
                existing[field] = candidate[field]
        if not existing.get("smiles") and candidate.get("smiles"):
            existing["smiles"] = candidate["smiles"]
        if not existing.get("source") and candidate.get("source"):
            existing["source"] = candidate["source"]
        if not existing.get("summary") and candidate.get("summary"):
            existing["summary"] = candidate["summary"]
        existing["assays"] = (existing.get("assays") or []) + (candidate.get("assays") or [])
        existing["labels"] = list(dict.fromkeys((existing.get("labels") or []) + (candidate.get("labels") or [])))
        existing["aliases"] = list(dict.fromkeys((existing.get("aliases") or []) + (candidate.get("aliases") or [])))
        if candidate.get("raw"):
            existing["raw"] = {**candidate.get("raw", {}), **(existing.get("raw") or {})}
    return list(deduped.values())

#Load local library
def load_reference_library(source: Optional[Any] = None) -> List[Dict[str, Any]]:
    if source is None:
        source = READ_ACROSS_REFERENCE_FILE

    if isinstance(source, (list, tuple)):
        return _dedupe_reference_records(x for x in source if isinstance(x, dict))
    if isinstance(source, dict):
        return _dedupe_reference_records(_coerce_records(source))

    path = Path(source)
    if not path.exists():
        return []

    if path.is_dir():
        rows: List[Dict[str, Any]] = []
        for p in sorted(path.iterdir()):
            suffix = p.suffix.lower()
            if suffix in {".csv", ".tsv", ".tab"}:
                rows.extend(_read_table_file(p))
            elif suffix == ".jsonl":
                rows.extend(_read_jsonl_file(p))
            elif suffix == ".json":
                rows.extend(_coerce_records(_read_json_file(p)))
        return _dedupe_reference_records(rows)

    suffix = path.suffix.lower()
    if suffix in {".csv", ".tsv", ".tab"}:
        return _dedupe_reference_records(_read_table_file(path))
    if suffix == ".jsonl":
        return _dedupe_reference_records(_read_jsonl_file(path))
    if suffix == ".json":
        raw = _coerce_records(_read_json_file(path))
        normalized = [normalize_reference_record(r) for r in raw]
        normalized = [r for r in normalized if r]
        return _dedupe_reference_records(normalized)
    return []


# -------------------------
# Scoring / enrichment
# -------------------------


def _record_name(record: Dict[str, Any]) -> str:
    for key in ("name", "chemical_name", "compound", "preferred_name", "title", "sample_name", "stressor"):
        value = str(record.get(key, "")).strip()
        if value:
            return value
    return "unknown"


def _record_smiles(record: Dict[str, Any]) -> str:
    for key in ("smiles", "canonical_smiles", "isomeric_smiles", "SMILES"):
        value = str(record.get(key, "")).strip()
        if value:
            canon = _canonicalize_smiles(value)
            return canon or value
    return ""


def _record_endpoints(record: Dict[str, Any]) -> List[str]:
    vals: List[str] = []
    for key in ("endpoint", "endpoint_name", "endpoints", "assay", "assay_name", "protocol_name", "effect"):
        vals.extend(_as_list(record.get(key)))
    return [v for v in dict.fromkeys(v.strip() for v in vals if v.strip())]


def _record_labels(record: Dict[str, Any]) -> List[str]:
    vals: List[str] = []
    for key in ("labels", "tags", "liabilities", "target_class", "mechanism_of_action", "stressor", "aop"):
        vals.extend(_as_list(record.get(key)))
    return [v for v in dict.fromkeys(v.strip() for v in vals if v.strip())]


def _reference_annotation_text(record: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key in ("name", "target_class", "mechanism_of_action", "endpoint", "assay_name", "summary", "evidence", "reasoning", "source", "stressor", "aop", "liabilities", "labels", "tags"):
        if record.get(key):
            val = record.get(key)
            if isinstance(val, (list, tuple, set)):
                parts.extend(map(str, val))
            else:
                parts.append(str(val))
    return _normalize_text(" ".join(parts))


def _score_single_reference(query_smiles: str, query_labels: set[str], record: Dict[str, Any], allow_remote_resolution: bool = True) -> Dict[str, Any]:
    name = _record_name(record)
    record_smiles = _record_smiles(record)

    if not record_smiles and allow_remote_resolution and resolve_chemical is not None:
        cached = _cache_get("record_smiles", name)
        if isinstance(cached, str) and cached:
            record_smiles = cached
        else:
            try:
                resolved = resolve_chemical(name)
                record_smiles = str(resolved.get("smiles") or "")
                if not record_smiles and fetch_chemical_details is not None:
                    ident = str(resolved.get("dtxsid") or resolved.get("dtxcid") or "").strip()
                    if ident:
                        details = fetch_chemical_details(ident)
                        if isinstance(details, dict):
                            record_smiles = str(
                                details.get("smiles")
                                or details.get("CanonicalSMILES")
                                or details.get("canonical_smiles")
                                or details.get("IsomericSMILES")
                                or ""
                            ).strip()
                if record_smiles:
                    _cache_set("record_smiles", name, record_smiles)
            except Exception:
                record_smiles = ""

    sim = tanimoto_from_smiles(query_smiles, record_smiles) if query_smiles and record_smiles else 0.0
    record_text = _reference_annotation_text(record)
    record_labels = set(_tokens(_record_labels(record)))
    label_overlap = len(query_labels & record_labels)

    structural_weight = float(os.environ.get("READ_ACROSS_STRUCTURAL_WEIGHT", "0.90"))
    max_bonus = float(os.environ.get("READ_ACROSS_MAX_BONUS", "0.10"))
    bonus_per_overlap = float(os.environ.get("READ_ACROSS_BONUS_PER_OVERLAP", "0.05"))
    bonus = min(max_bonus, bonus_per_overlap * label_overlap)
    score = float(np.clip(structural_weight * sim + bonus, 0.0, 1.0))

    reasons: List[str] = []
    if sim:
        reasons.append("fingerprint similarity")
    if label_overlap:
        reasons.append("shared annotation terms")
    if record_text and not reasons:
        reasons.append("local similarity score from structure and annotation overlap")
    if not reasons:
        reasons.append("local similarity score from structure and annotation overlap")

    return {
        "name": name,
        "score": score,
        "similarity": score,
        "raw_similarity": sim,
        "reasoning": "; ".join(reasons),
        "smiles": record_smiles,
        "endpoint": ", ".join(_record_endpoints(record)),
        "source": record.get("source") or record.get("dataset") or "local_reference",
        "labels": sorted(record_labels),
        "raw": record,
    }


# Main READ ACROSS function that compares a query chemical against a reference library
def score_against_reference_library(
    query_smiles: str,
    target_profile: Optional[Dict[str, Any]] = None,
    mies: Optional[Sequence[Dict[str, Any]]] = None,
    reference_library: Optional[Sequence[Dict[str, Any]]] = None,
    top_k: Optional[int] = None,
    min_similarity: Optional[float] = None,
    allow_remote_resolution: Optional[bool] = None,
) -> Dict[str, Any]:
    """Score a query structure against a local reference library using RDKit fingerprints."""
    query_smiles = _canonicalize_smiles(query_smiles or "") or (query_smiles or "")
    target_profile = target_profile or {}
    mies = mies or []

    reference_library = list(reference_library) if reference_library is not None else load_reference_library()
    ctx_seed_records = _ctx_seed_reference_records(target_profile, mies)
    if ctx_seed_records:
        reference_library = _dedupe_reference_records(list(reference_library) + list(ctx_seed_records))

    top_k = int(top_k if top_k is not None else READ_ACROSS_TOP_K)
    min_similarity = float(min_similarity if min_similarity is not None else READ_ACROSS_MIN_SIMILARITY)
    allow_remote_resolution = bool(READ_ACROSS_ALLOW_REMOTE_RESOLUTION if allow_remote_resolution is None else allow_remote_resolution)

    query_text = _profile_text(target_profile, mies)
    query_labels = _tokens(query_text)

    scored = [
        _score_single_reference(query_smiles=query_smiles, query_labels=query_labels, record=record, allow_remote_resolution=allow_remote_resolution)
        for record in reference_library
        if isinstance(record, dict)
    ]
    scored.sort(key=lambda x: float(x.get("score") or 0.0), reverse=True)
    top = [x for x in scored if float(x.get("score") or 0.0) >= min_similarity][:top_k]

    supporting_evidence: List[str] = []
    matched_endpoints: List[str] = []
    analogs: List[Dict[str, Any]] = []
    for item in top:
        analogs.append({
            "name": item.get("name"),
            "score": float(item.get("score") or 0.0),
            "similarity": float(item.get("similarity") or 0.0),
            "raw_similarity": float(item.get("raw_similarity") or 0.0),
            "endpoint": item.get("endpoint", ""),
            "source": item.get("source", ""),
            "labels": item.get("labels", []),
            "reasoning": item.get("reasoning", ""),
        })
        if item.get("endpoint"):
            matched_endpoints.extend([e.strip() for e in str(item.get("endpoint")).split(",") if e.strip()])
        if item.get("reasoning"):
            supporting_evidence.append(f"{item.get('name')}: {item.get('reasoning')}")

    avg_score = float(mean([a["score"] for a in analogs])) if analogs else 0.0
    confidence = float(np.clip(avg_score, 0.0, 1.0))

    summary = summarize_read_across(
        {
            "status": "ok" if analogs else "no_analogs",
            "query": query_smiles,
            "analogs": analogs,
            "matched_endpoints": sorted(dict.fromkeys(matched_endpoints)),
            "supporting_evidence": supporting_evidence,
            "confidence": confidence,
        }
    )

    return {
        "status": "ok" if analogs else "no_analogs",
        "query": query_smiles,
        "analogs": analogs,
        "matched_endpoints": sorted(dict.fromkeys(matched_endpoints)),
        "supporting_evidence": supporting_evidence,
        "confidence": confidence,
        "summary": summary,
        "library_size": len(reference_library),
        "scored_count": len(scored),
        "top_k": top_k,
        "min_similarity": min_similarity,
        "ctx_seed_records": ctx_seed_records,
        "ctx_seed_count": len(ctx_seed_records),
    }

#Langgraph integration, resolves chemical to a structure and scores against reference library
def enrich_read_across(
    chemical: str,
    target_profile: Optional[Dict[str, Any]] = None,
    mies: Optional[Sequence[Dict[str, Any]]] = None,
    reference_source: Optional[Any] = None,
    top_k: Optional[int] = None,
    min_similarity: Optional[float] = None,
    allow_remote_resolution: Optional[bool] = None,
    use_ctx: bool = False,
    source: Optional[Any] = None,
) -> Dict[str, Any]:
    if source is not None:
        reference_source = source

    chemical = str(chemical or "").strip()
    if not chemical:
        return {"status": "empty_query", "query": "", "analogs": [], "matched_endpoints": [], "supporting_evidence": [], "confidence": 0.0, "summary": "No query chemical provided."}

    # Validate chemical name format before processing
    if not _is_valid_chemical_name(chemical):
        return {
            "status": "invalid_name_format",
            "query": chemical,
            "analogs": [],
            "matched_endpoints": [],
            "supporting_evidence": [],
            "confidence": 0.0,
            "summary": f"Invalid chemical name format: {chemical}",
            "error": "Chemical name does not meet validation criteria"
        }

    # Always try CTX resolution first; use_ctx controls extra bundle enrichment only.
    query = _resolve_query_structure(chemical, prefer_ctx=True)

    query_smiles = str(query.get("smiles") or "")
    if not query_smiles:
        result = {
            "status": query.get("status", "not_found"),
            "query": chemical,
            "chemical": query,
            "analogs": [],
            "matched_endpoints": [],
            "supporting_evidence": [],
            "confidence": 0.0,
            "summary": f"Unable to resolve {chemical} to a structure.",
        }
        if use_ctx and fetch_compound_bundle is not None:
            try:
                result["ctx_bundle"] = fetch_compound_bundle(chemical)
            except Exception:
                result["ctx_bundle"] = {}
        return result

    library = load_reference_library(reference_source)
    result = score_against_reference_library(
        query_smiles=query_smiles,
        target_profile=target_profile,
        mies=mies,
        reference_library=library,
        top_k=top_k,
        min_similarity=min_similarity,
        allow_remote_resolution=allow_remote_resolution,
    )
    result["chemical"] = query
    result["query_name"] = chemical

    if use_ctx and fetch_compound_bundle is not None:
        try:
            result["ctx_bundle"] = fetch_compound_bundle(chemical)
        except Exception:
            result["ctx_bundle"] = {}
    return result


def enrich_read_across_state(state: Dict[str, Any], reference_source: Optional[Any] = None, use_ctx: bool = False) -> Dict[str, Any]:
    data = state.setdefault("data", {})
    if not isinstance(data, dict):
        data = {}
        state["data"] = data

    # Enforce one-shot read-across: once attempted, reuse the stored result
    # and do not recalculate it again later in the workflow.
    if data.get("read_across_attempted", False):
        return state

    data["read_across_attempted"] = True

    chemical = str(state.get("chemical", "")).strip()
    
    # Validate chemical name before proceeding
    if chemical and not _is_valid_chemical_name(chemical):
        result = {
            "status": "invalid_name_format",
            "query": chemical,
            "analogs": [],
            "matched_endpoints": [],
            "supporting_evidence": [],
            "confidence": 0.0,
            "summary": f"Invalid chemical name format: {chemical}",
            "error": "Chemical name does not meet validation criteria"
        }
        data["read_across"] = result
        return state

    target_profile = data.get("target_profile", {}) if isinstance(data.get("target_profile", {}), dict) else {}
    mies = state.get("MIEs", [])
    result = enrich_read_across(
        chemical=chemical,
        target_profile=target_profile,
        mies=mies,
        reference_source=reference_source,
        use_ctx=use_ctx,
    )
    data["read_across"] = result
    return state


# -------------------------
# Summarization
# -------------------------

# Combine the target profile and MIEs into a single text string for scoring
def _profile_text(target_profile: Dict[str, Any], mies: Sequence[Dict[str, Any]] | None = None) -> str:
    if not isinstance(target_profile, dict):
        return ""
    parts: List[str] = []
    props = target_profile.get("properties", {}) if isinstance(target_profile.get("properties", {}), dict) else {}
    for k, v in props.items():
        parts.append(str(k))
        if isinstance(v, (list, tuple, set)):
            parts.extend(map(str, v))
        else:
            parts.append(str(v))
    parts.extend(_as_list(target_profile.get("liabilities", [])))
    if mies:
        for mie in mies:
            if isinstance(mie, dict):
                parts.append(str(mie.get("name", "")))
                parts.append(str(mie.get("reasoning", "")))
    return _normalize_text(" ".join(parts))

# Human readable summary of the read-across results
def summarize_read_across(result: Dict[str, Any]) -> str:
    if not isinstance(result, dict):
        return ""
    if result.get("status") in {"empty_query", "not_found"}:
        return str(result.get("summary", ""))

    analogs = result.get("analogs", []) if isinstance(result.get("analogs", []), list) else []
    if not analogs:
        return result.get("summary", "No read-across analogs found.")

    top = analogs[:3]
    parts = [f"{a.get('name', 'unknown')} (sim {float(a.get('score') or 0.0):.2f})" for a in top]
    endpoints = result.get("matched_endpoints", [])
    endpoint_text = f"; endpoints: {', '.join(endpoints[:5])}" if endpoints else ""
    return f"Top analogs: {', '.join(parts)}{endpoint_text}."


def evaluate_candidates_read_across(*args, **kwargs):
    return score_against_reference_library(*args, **kwargs)

# Expose the main functions for import
__all__ = [
    "enrich_read_across",
    "enrich_read_across_state",
    "load_reference_library",
    "normalize_reference_record",
    "score_against_reference_library",
    "summarize_read_across",
    "evaluate_candidates_read_across",
]
