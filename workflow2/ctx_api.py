from __future__ import annotations

import os
import re
import urllib.parse
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

try:
    from rdkit import Chem
except Exception:  # pragma: no cover
    Chem = None  # type: ignore

try:  # preferred interface from ctx-python README
    import ctxpy as ctx
except Exception:  # pragma: no cover
    ctx = None  # type: ignore

load_dotenv()

CTX_BASE_URL = os.environ.get("CTX_BASE_URL", os.environ.get("ctx_api_host", "https://api.epa.gov/comptox-ptc/")).rstrip("/")
CTX_API_KEY = os.environ.get("CTX_API_KEY", os.environ.get("ctx_x_api_key", "")).strip()
CTX_TIMEOUT = float(os.environ.get("CTX_TIMEOUT", "30"))
CTX_ACCEPT = os.environ.get("CTX_ACCEPT", os.environ.get("ctx_api_accept", "application/json"))

CTX_PATHS = {
    "chemical_search_exact": os.environ.get("CTX_CHEMICAL_SEARCH_EXACT", "chemical/search/exact"),
    "chemical_search_substring": os.environ.get("CTX_CHEMICAL_SEARCH_SUBSTRING", "chemical/search/substring"),
    "chemical_details_dtxsid": os.environ.get("CTX_CHEMICAL_DETAILS_DTXSID", "chemical/details/{dtxsid}"),
    "chemical_details_dtxcid": os.environ.get("CTX_CHEMICAL_DETAILS_DTXCID", "chemical/details/cid/{dtxcid}"),
    "chemical_details_smiles": os.environ.get("CTX_CHEMICAL_DETAILS_SMILES", "chemical/details/smiles"),
    "bioactivity_summary": os.environ.get("CTX_BIOACTIVITY_SUMMARY", "bioactivity/data/{dtxsid}"),
    "bioactivity_data": os.environ.get("CTX_BIOACTIVITY_DATA", "bioactivity/data/{dtxsid}"),
    "exposure_functional_use": os.environ.get("CTX_EXPOSURE_FUNCTIONAL_USE", "exposure/functional-use/{dtxsid}"),
    "exposure_product_data": os.environ.get("CTX_EXPOSURE_PRODUCT_DATA", "exposure/product-data/{dtxsid}"),
    "exposure_list_presence": os.environ.get("CTX_EXPOSURE_LIST_PRESENCE", "exposure/list-presence/{dtxsid}"),
    "exposure_httk": os.environ.get("CTX_EXPOSURE_HTTK", "exposure/httk/{dtxsid}"),
    "exposure_seem_general": os.environ.get("CTX_EXPOSURE_SEEM_GENERAL", "exposure/seem-general/{dtxsid}"),
    "exposure_seem_demographic": os.environ.get("CTX_EXPOSURE_SEEM_DEMO", "exposure/seem-demographic/{dtxsid}"),
    "hazard_toxvaldb": os.environ.get("CTX_HAZARD_TOXVALDB", "hazard/toxvaldb/{dtxsid}"),
    "hazard_toxvaldb_cancer": os.environ.get("CTX_HAZARD_TOXVALDB_CANCER", "hazard/toxvaldb/cancer/{dtxsid}"),
    "hazard_toxvaldb_genetox": os.environ.get("CTX_HAZARD_TOXVALDB_GENETOX", "hazard/toxvaldb/genetox/{dtxsid}"),
    "hazard_toxvaldb_skin_eye": os.environ.get("CTX_HAZARD_TOXVALDB_SKIN_EYE", "hazard/toxvaldb/skin-eye/{dtxsid}"),
    "hazard_toxrefdb_summary": os.environ.get("CTX_HAZARD_TOXREFDB_SUMMARY", "hazard/toxrefdb/summary/{dtxsid}"),
    "hazard_adme_ivive": os.environ.get("CTX_HAZARD_ADME_IVIVE", "hazard/adme-ivive/{dtxsid}"),
    "hazard_iris": os.environ.get("CTX_HAZARD_IRIS", "hazard/iris/{dtxsid}"),
    "hazard_pprtv": os.environ.get("CTX_HAZARD_PPRTV", "hazard/pprtv/{dtxsid}"),
}


@dataclass
class CTXChemical:
    query: str
    status: str = "not_found"
    name: str = ""
    dtxsid: str = ""
    dtxcid: str = ""
    smiles: str = ""
    inchikey: str = ""
    formula: str = ""
    raw: Dict[str, Any] = None  # type: ignore[assignment]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "status": self.status,
            "name": self.name or self.query,
            "dtxsid": self.dtxsid,
            "dtxcid": self.dtxcid,
            "smiles": self.smiles,
            "inchikey": self.inchikey,
            "formula": self.formula,
            "raw": self.raw or {},
        }


# -------------------------
# low-level HTTP helpers
# -------------------------


def _headers() -> Dict[str, str]:
    h = {"Accept": CTX_ACCEPT}
    if CTX_API_KEY:
        h["X-Api-Key"] = CTX_API_KEY
    return h


def _request(method: str, path: str, params: Optional[Dict[str, Any]] = None, json_body: Any = None) -> Any:
    url = f"{CTX_BASE_URL}/{path.lstrip('/')}"
    r = requests.request(method.upper(), url, params=params, json=json_body, headers=_headers(), timeout=CTX_TIMEOUT)
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return r.text


def get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    return _request("GET", path, params=params)


def post(path: str, payload: Any) -> Any:
    return _request("POST", path, json_body=payload)


# -------------------------
# parsing helpers
# -------------------------


def _canonicalize_smiles(smiles: str) -> Optional[str]:
    if not smiles or Chem is None:
        return None
    mol = Chem.MolFromSmiles(smiles)
    return Chem.MolToSmiles(mol, canonical=True) if mol else None


def _is_probable_smiles(value: str) -> bool:
    s = str(value or "").strip()
    return bool(s) and len(s) > 2 and any(ch in s for ch in ("=", "#", "[", "]", "(", ")"))


def _first_dict(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, dict):
        for key in ("results", "data", "items", "records", "chemicals", "compounds", "hits"):
            v = obj.get(key)
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        return item
            if isinstance(v, dict):
                return v
        return obj
    if isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                return item
    return {}


def _records(obj: Any) -> List[Dict[str, Any]]:
    if isinstance(obj, dict):
        for key in ("results", "data", "items", "records", "chemicals", "compounds", "hits"):
            v = obj.get(key)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
        if obj:
            return [obj]
        return []
    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    return []


def _maybe_dataframe_rows(obj: Any) -> List[Dict[str, Any]]:
    if obj is None:
        return []
    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    if isinstance(obj, dict):
        if any(isinstance(v, list) for v in obj.values()):
            return _records(obj)
        return [obj]
    try:
        to_dict = getattr(obj, "to_dict", None)
        if callable(to_dict):
            d = to_dict(orient="records")
            if isinstance(d, list):
                return [x for x in d if isinstance(x, dict)]
    except Exception:
        pass
    try:
        if hasattr(obj, "to_json"):
            import json as _json

            txt = obj.to_json(orient="records")
            parsed = _json.loads(txt)
            if isinstance(parsed, list):
                return [x for x in parsed if isinstance(x, dict)]
    except Exception:
        pass
    return []


def _normalize_chemical_details(query: str, item: Dict[str, Any], source: str = "ctx") -> Dict[str, Any]:
    dtxsid = str(item.get("dtxsid") or item.get("DTXSID") or item.get("substance_id") or item.get("substanceId") or "").strip()
    dtxcid = str(item.get("dtxcid") or item.get("DTXCID") or item.get("cid") or item.get("CID") or "").strip()
    name = str(item.get("name") or item.get("chemical_name") or item.get("title") or item.get("preferred_name") or query).strip()
    smiles = str(
        item.get("smiles")
        or item.get("CanonicalSMILES")
        or item.get("canonical_smiles")
        or item.get("IsomericSMILES")
        or item.get("isomeric_smiles")
        or ""
    ).strip()
    if smiles:
        smiles = _canonicalize_smiles(smiles) or smiles
    inchikey = str(item.get("inchikey") or item.get("InChIKey") or item.get("inchi_key") or "").strip()
    formula = str(item.get("formula") or item.get("MolecularFormula") or item.get("molecular_formula") or "").strip()
    return CTXChemical(
        query=query,
        status="ok",
        name=name,
        dtxsid=dtxsid,
        dtxcid=dtxcid,
        smiles=smiles,
        inchikey=inchikey,
        formula=formula,
        raw={"source": source, "item": item},
    ).as_dict()


# -------------------------
# ctxpy helpers (preferred)
# -------------------------


def _ctx_chemical():
    if ctx is None:
        return None
    try:
        return ctx.Chemical(x_api_key=CTX_API_KEY) if CTX_API_KEY else ctx.Chemical()
    except Exception:
        return None


def _ctx_exposure():
    if ctx is None:
        return None
    try:
        return ctx.Exposure(x_api_key=CTX_API_KEY) if CTX_API_KEY else ctx.Exposure()
    except Exception:
        return None


def _ctx_hazard():
    if ctx is None:
        return None
    try:
        return ctx.Hazard(x_api_key=CTX_API_KEY) if CTX_API_KEY else ctx.Hazard()
    except Exception:
        return None


def _ctx_search(query: str) -> List[Dict[str, Any]]:
    chem = _ctx_chemical()
    if chem is None:
        return []
    rows: List[Dict[str, Any]] = []
    for by in ("equals", "starts-with", "contains"):
        try:
            result = chem.search(by=by, query=query)
            rows = _maybe_dataframe_rows(result)
            if rows:
                break
        except Exception:
            continue
    return rows


def _ctx_details(by: str, value: str) -> Dict[str, Any]:
    chem = _ctx_chemical()
    if chem is None or not value:
        return {}
    try:
        result = chem.details(by=by, query=value)
        if isinstance(result, dict):
            return _first_dict(result)
        rows = _maybe_dataframe_rows(result)
        return rows[0] if rows else {}
    except Exception:
        return {}


def _ctx_msready(by: str, value: str) -> Any:
    chem = _ctx_chemical()
    if chem is None or not value:
        return {}
    try:
        result = chem.msready(by=by, query=value)
        rows = _maybe_dataframe_rows(result)
        return rows if rows else result
    except Exception:
        return {}


# -------------------------
# public chemical API
# -------------------------


def resolve_chemical(query: str) -> Dict[str, Any]:
    """Resolve a chemical name, identifier, or SMILES using ctxpy Chemical first, then raw HTTP fallback."""
    q = str(query or "").strip()
    if not q:
        return CTXChemical(query="", status="empty_query").as_dict()

    if _is_probable_smiles(q):
        canon = _canonicalize_smiles(q)
        if canon:
            return CTXChemical(query=q, status="ok", name=q, smiles=canon, raw={"source": "direct_smiles"}).as_dict()

    # 1) ctxpy Chemical search (preferred)
    rows = _ctx_search(q)
    if rows:
        item = rows[0]
        resolved = _normalize_chemical_details(q, item, source="ctxpy_search")
        if not resolved.get("smiles"):
            dtxsid = str(resolved.get("dtxsid") or "").strip()
            dtxcid = str(resolved.get("dtxcid") or "").strip()
            if dtxsid:
                details = _ctx_details("dtxsid", dtxsid)
                if details:
                    resolved = _normalize_chemical_details(q, details, source="ctxpy_details_dtxsid")
            elif dtxcid:
                details = _ctx_details("dtxcid", dtxcid)
                if details:
                    resolved = _normalize_chemical_details(q, details, source="ctxpy_details_dtxcid")
        if resolved.get("smiles") or resolved.get("dtxsid") or resolved.get("dtxcid"):
            return resolved

    # 2) direct details lookup if the query already looks like a DTX identifier
    if q.upper().startswith("DTX"):
        for key, path_key in (("dtxsid", "chemical_details_dtxsid"), ("dtxcid", "chemical_details_dtxcid")):
            try:
                data = get(CTX_PATHS[path_key].format(**{key: q}))
                item = _first_dict(data)
                if item:
                    return _normalize_chemical_details(q, item, source="raw_details_lookup")
            except Exception:
                pass

    # 3) raw HTTP fallback using CTX chemical search endpoints
    search_paths = (CTX_PATHS["chemical_search_exact"], CTX_PATHS["chemical_search_substring"])
    search_param_sets = (
        {"query": q, "exact": "true"},
        {"query": q},
        {"value": q},
        {"name": q},
        {"search": q},
        {"q": q},
    )
    for path in search_paths:
        for params in search_param_sets:
            try:
                data = get(path, params=params)
            except Exception:
                continue
            rows = _records(data)
            if rows:
                item = rows[0]
                resolved = _normalize_chemical_details(q, item, source="raw_search")
                if resolved.get("smiles") or resolved.get("dtxsid") or resolved.get("dtxcid"):
                    return resolved

    return CTXChemical(query=q).as_dict()


def resolve_query_chemical(query: str) -> Dict[str, Any]:
    return resolve_chemical(query)


def fetch_chemical_details(dtxsid: str) -> Dict[str, Any]:
    if not dtxsid:
        return {}
    chem = _ctx_chemical()
    if chem is not None:
        try:
            result = chem.details(by="dtxsid", query=dtxsid)
            if isinstance(result, dict):
                return _first_dict(result)
            rows = _maybe_dataframe_rows(result)
            if rows:
                return rows[0]
        except Exception:
            pass
    try:
        data = get(CTX_PATHS["chemical_details_dtxsid"].format(dtxsid=dtxsid))
        return _first_dict(data)
    except Exception:
        return {}


def fetch_chemical_details_by_dtxcid(dtxcid: str) -> Dict[str, Any]:
    if not dtxcid:
        return {}
    chem = _ctx_chemical()
    if chem is not None:
        try:
            result = chem.details(by="dtxcid", query=dtxcid)
            if isinstance(result, dict):
                return _first_dict(result)
            rows = _maybe_dataframe_rows(result)
            if rows:
                return rows[0]
        except Exception:
            pass
    try:
        data = get(CTX_PATHS["chemical_details_dtxcid"].format(dtxcid=dtxcid))
        return _first_dict(data)
    except Exception:
        return {}


def fetch_chemical_details_by_smiles(smiles: str) -> Dict[str, Any]:
    if not smiles:
        return {}
    chem = _ctx_chemical()
    if chem is not None:
        try:
            result = chem.details(by="smiles", query=smiles)
            if isinstance(result, dict):
                return _first_dict(result)
            rows = _maybe_dataframe_rows(result)
            if rows:
                return rows[0]
        except Exception:
            pass
    try:
        data = get(CTX_PATHS["chemical_details_smiles"], params={"query": smiles})
        return _first_dict(data)
    except Exception:
        return {}


def search_chemical(query: str, by: str = "equals") -> List[Dict[str, Any]]:
    chem = _ctx_chemical()
    if chem is not None:
        try:
            result = chem.search(by=by, query=query)
            rows = _maybe_dataframe_rows(result)
            if rows:
                return rows
        except Exception:
            pass
    path = CTX_PATHS["chemical_search_exact"] if by == "equals" else CTX_PATHS["chemical_search_substring"]
    try:
        data = get(path, params={"query": query, "exact": "true"} if by == "equals" else {"query": query})
        return _records(data)
    except Exception:
        return []


def fetch_bioactivity(dtxsid: str) -> Any:
    if not dtxsid:
        return {}
    # ctxpy README does not document Bioactivity, so use raw HTTP as the stable fallback.
    try:
        result = get(CTX_PATHS["bioactivity_data"].format(dtxsid=dtxsid))
        return _maybe_dataframe_rows(result) if result else {}
    except Exception:
        return {}


def fetch_exposure(dtxsid: str) -> Dict[str, Any]:
    if not dtxsid:
        return {}
    expo = _ctx_exposure()
    out: Dict[str, Any] = {}
    if expo is not None:
        calls = {
            "functional_use": ("search_cpdat", {"vocab_name": "fc", "dtxsid": dtxsid}),
            "product_data": ("search_cpdat", {"vocab_name": "puc", "dtxsid": dtxsid}),
            "list_presence": ("search_cpdat", {"vocab_name": "lpk", "dtxsid": dtxsid}),
            "httk": ("search_httk", {"dtxsid": dtxsid}),
            "seem_general": ("search_exposures", {"by": "seem", "dtxsid": dtxsid}),
            "seem_demographic": ("search_exposures", {"by": "seem", "dtxsid": dtxsid}),
        }
        for key, (method_name, kwargs) in calls.items():
            try:
                method = getattr(expo, method_name, None)
                if callable(method):
                    result = method(**kwargs)
                    out[key] = _maybe_dataframe_rows(result) if result else None
                    continue
            except Exception:
                pass
            out[key] = None
        return out

    paths = {
        "functional_use": CTX_PATHS["exposure_functional_use"],
        "product_data": CTX_PATHS["exposure_product_data"],
        "list_presence": CTX_PATHS["exposure_list_presence"],
        "httk": CTX_PATHS["exposure_httk"],
        "seem_general": CTX_PATHS["exposure_seem_general"],
        "seem_demographic": CTX_PATHS["exposure_seem_demographic"],
    }
    for key, path in paths.items():
        try:
            result = get(path.format(dtxsid=dtxsid))
            out[key] = _maybe_dataframe_rows(result) if result else None
        except Exception:
            out[key] = None
    return out


def fetch_hazard(dtxsid: str) -> Dict[str, Any]:
    if not dtxsid:
        return {}
    haz = _ctx_hazard()
    out: Dict[str, Any] = {}
    if haz is not None:
        calls = {
            "toxvaldb": ("search_toxvaldb", {"by": "human", "dtxsid": dtxsid}),
            "toxvaldb_cancer": ("search_toxvaldb", {"by": "cancer", "dtxsid": dtxsid}),
            "toxvaldb_genetox": ("search_toxvaldb", {"by": "genetox", "dtxsid": dtxsid}),
            "toxvaldb_skin_eye": ("search_toxvaldb", {"by": "skin-eye", "dtxsid": dtxsid}),
            "toxrefdb_summary": ("search", {"by": "human", "dtxsid": dtxsid}),
            "adme_ivive": ("search", {"by": "human", "dtxsid": dtxsid}),
            "iris": ("search", {"by": "human", "dtxsid": dtxsid}),
            "pprtv": ("search", {"by": "human", "dtxsid": dtxsid}),
        }
        for key, (method_name, kwargs) in calls.items():
            try:
                method = getattr(haz, method_name, None)
                if callable(method):
                    result = method(**kwargs)
                    out[key] = _maybe_dataframe_rows(result) if result else None
                    continue
            except Exception:
                pass
            out[key] = None
        return out

    paths = {
        "toxvaldb": CTX_PATHS["hazard_toxvaldb"],
        "toxvaldb_cancer": CTX_PATHS["hazard_toxvaldb_cancer"],
        "toxvaldb_genetox": CTX_PATHS["hazard_toxvaldb_genetox"],
        "toxvaldb_skin_eye": CTX_PATHS["hazard_toxvaldb_skin_eye"],
        "toxrefdb_summary": CTX_PATHS["hazard_toxrefdb_summary"],
        "adme_ivive": CTX_PATHS["hazard_adme_ivive"],
        "iris": CTX_PATHS["hazard_iris"],
        "pprtv": CTX_PATHS["hazard_pprtv"],
    }
    for key, path in paths.items():
        try:
            result = get(path.format(dtxsid=dtxsid))
            out[key] = _maybe_dataframe_rows(result) if result else None
        except Exception:
            out[key] = None
    return out


def fetch_compound_bundle(query: str) -> Dict[str, Any]:
    chem = resolve_chemical(query)
    dtxsid = str(chem.get("dtxsid") or "").strip()
    bundle: Dict[str, Any] = {"chemical": chem, "chemical_details": {}, "bioactivity": None, "exposure": None, "hazard": None}
    if dtxsid:
        try:
            bundle["chemical_details"] = fetch_chemical_details(dtxsid)
        except Exception:
            bundle["chemical_details"] = {}
        try:
            bundle["bioactivity"] = fetch_bioactivity(dtxsid)
        except Exception:
            bundle["bioactivity"] = None
        try:
            bundle["exposure"] = fetch_exposure(dtxsid)
        except Exception:
            bundle["exposure"] = None
        try:
            bundle["hazard"] = fetch_hazard(dtxsid)
        except Exception:
            bundle["hazard"] = None
    return bundle


def batch_resolve(queries: List[str]) -> List[Dict[str, Any]]:
    return [resolve_chemical(q) for q in queries if str(q or "").strip()]


# Backwards-compatible aliases some workflow files import
Chemical = getattr(ctx, "Chemical", None) if ctx is not None else None
Exposure = getattr(ctx, "Exposure", None) if ctx is not None else None
Hazard = getattr(ctx, "Hazard", None) if ctx is not None else None


__all__ = [
    "Chemical",
    "CTXChemical",
    "Exposure",
    "Hazard",
    "batch_resolve",
    "fetch_bioactivity",
    "fetch_chemical_details",
    "fetch_chemical_details_by_dtxcid",
    "fetch_chemical_details_by_smiles",
    "fetch_compound_bundle",
    "fetch_exposure",
    "fetch_hazard",
    "get",
    "post",
    "resolve_chemical",
    "resolve_query_chemical",
    "search_chemical",
]