#!/usr/bin/env python3
"""
Tox21 API wrapper module for read-across workflow.

This module provides web access to Tox21 data while maintaining
compatibility with the offline read_across.py module.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests
import hashlib

# API Configuration
TOX21_API_URL = os.environ.get("TOX21_API_URL", "https://api.tox21.gov/v1")
TOX21_API_KEY = os.environ.get("TOX21_API_KEY", None)
API_TIMEOUT = int(os.environ.get("TOX21_API_TIMEOUT", "30"))
API_CACHE_DIR = Path(os.environ.get("TOX21_CACHE_DIR", ".tox21_cache"))
API_RATE_LIMIT = float(os.environ.get("TOX21_RATE_LIMIT", "10.0"))  # requests per minute


class Tox21APIError(Exception):
    """Custom exception for Tox21 API errors."""
    pass


class Tox21API:
    """Wrapper for Tox21 web API with caching and rate limiting."""
    
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
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an authenticated request to the Tox21 API."""
        self._enforce_rate_limit()
        
        url = f"{TOX21_API_URL}/{endpoint}"
        headers = {}
        if TOX21_API_KEY:
            headers["Authorization"] = f"Bearer {TOX21_API_KEY}"
        
        try:
            response = requests.get(
                url,
                params=params or {},
                headers=headers,
                timeout=API_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Tox21APIError(f"API request failed: {e}")
    
    def get_chemical_records(self, chemical_id: str, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Get Tox21 records for a specific chemical."""
        params = {"chemical_id": chemical_id}
        cache_key = self._get_cache_key("records", params)
        
        if use_cache:
            cached = self._read_cache(cache_key)
            if cached:
                return cached.get("records", [])
        
        try:
            data = self._make_request("records", params)
            records = data.get("records", [])
            
            if use_cache:
                self._write_cache(cache_key, data)
            
            return records
        except Tox21APIError:
            return []
    
    def search_chemicals(self, query: str, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Search for chemicals by name, CAS, or InChI."""
        params = {"q": query}
        cache_key = self._get_cache_key("search", params)
        
        if use_cache:
            cached = self._read_cache(cache_key)
            if cached:
                return cached.get("results", [])
        
        try:
            data = self._make_request("search", params)
            results = data.get("results", [])
            
            if use_cache:
                self._write_cache(cache_key, data)
            
            return results
        except Tox21APIError:
            return []
    
    def get_endpoint_info(self, endpoint_id: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific endpoint."""
        params = {"endpoint_id": endpoint_id}
        cache_key = self._get_cache_key("endpoint", params)
        
        if use_cache:
            cached = self._read_cache(cache_key)
            if cached:
                return cached
        
        try:
            data = self._make_request("endpoint", params)
            
            if use_cache:
                self._write_cache(cache_key, data)
            
            return data
        except Tox21APIError:
            return None


def load_tox21_records_from_api(
    chemical_id: str,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    cache_dir: Optional[Path] = None,
    use_cache: bool = True
) -> List[Dict[str, Any]]:
    """
    Load Tox21 records from the web API.
    
    Args:
        chemical_id: Chemical identifier (CAS, name, or InChI)
        api_url: Override the default API URL
        api_key: API authentication key
        cache_dir: Directory for caching API responses
        use_cache: Whether to use cached responses
    
    Returns:
        List of Tox21 records as dictionaries
    """
    # Temporarily override environment variables
    original_url = TOX21_API_URL
    original_key = TOX21_API_KEY
    original_cache = API_CACHE_DIR
    
    if api_url:
        os.environ["TOX21_API_URL"] = api_url
    if api_key:
        os.environ["TOX21_API_KEY"] = api_key
    if cache_dir:
        os.environ["TOX21_CACHE_DIR"] = str(cache_dir)
    
    try:
        api = Tox21API(cache_dir)
        return api.get_chemical_records(chemical_id, use_cache)
    finally:
        # Restore original values
        os.environ["TOX21_API_URL"] = original_url
        os.environ["TOX21_API_KEY"] = original_key
        os.environ["TOX21_CACHE_DIR"] = str(original_cache)


__all__ = [
    "Tox21API",
    "Tox21APIError",
    "load_tox21_records_from_api",
    "TOX21_API_URL",
    "TOX21_API_KEY",
    "API_TIMEOUT",
    "API_CACHE_DIR",
    "API_RATE_LIMIT",
]
