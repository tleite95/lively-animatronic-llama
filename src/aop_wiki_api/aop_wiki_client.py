"""
AOP Wiki API Client
===================

A client for interacting with the AOP Wiki to retrieve Adverse Outcome Pathway (AOP) data,
including Molecular Initiating Events (MIEs) and associated chemical information.
"""

import requests
import json
from typing import List, Dict, Optional
from .models import AOP, KeyEvent, MolecularInitiatingEvent


class AOPWikiClient:
    """
    Client for interacting with the AOP Wiki API.
    
    The AOP Wiki (https://aopwiki.org/) provides comprehensive information about
    Adverse Outcome Pathways, including Molecular Initiating Events (MIEs),
    Key Events (KEs), and their relationships.
    """
    
    BASE_URL = "https://aopwiki.org/aops"
    
    def __init__(self, base_url: str = None, timeout: int = 30):
        """
        Initialize the AOP Wiki client.
        
        Args:
            base_url: Base URL for the AOP Wiki API. Defaults to "https://aopwiki.org/aops".
            timeout: Request timeout in seconds. Defaults to 30.
        """
        self.base_url = base_url or self.BASE_URL
        self.timeout = timeout
        self.session = requests.Session()
        
    def get_all_aops(self) -> List[AOP]:
        """
        Retrieve all Adverse Outcome Pathways from the AOP Wiki.
        
        Returns:
            List of AOP objects.
            
        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        url = f"{self.base_url}/json"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        return [self._parse_aop(aop_data) for aop_data in data.get('aops', [])]
    
    def get_aop_by_id(self, aop_id: int) -> Optional[AOP]:
        """
        Retrieve a specific Adverse Outcome Pathway by its ID.
        
        Args:
            aop_id: The ID of the AOP to retrieve.
            
        Returns:
            AOP object if found, None otherwise.
            
        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        url = f"{self.base_url}/{aop_id}/json"
        response = self.session.get(url, timeout=self.timeout)
        
        if response.status_code == 404:
            return None
            
        response.raise_for_status()
        
        aop_data = response.json()
        return self._parse_aop(aop_data)
    
    def search_miess(self, query: str = None, **filters) -> List[MolecularInitiatingEvent]:
        """
        Search for Molecular Initiating Events (MIEs) in the AOP Wiki.
        
        Args:
            query: Search query string.
            **filters: Additional filter parameters (e.g., chemical_name, cas_rn).
            
        Returns:
            List of MolecularInitiatingEvent objects.
            
        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        # Note: This is a placeholder implementation
        # The actual AOP Wiki API may have different endpoints for MIE search
        aops = self.get_all_aops()
        
        miess = []
        for aop in aops:
            for mie in aop.molecular_initiating_events:
                if query and query.lower() not in mie.name.lower():
                    continue
                if filters:
                    match = True
                    for key, value in filters.items():
                        if hasattr(mie, key) and getattr(mie, key) != value:
                            match = False
                            break
                    if not match:
                        continue
                miess.append(mie)
        
        return miess
    
    def get_miess_for_chemical(self, chemical_name: str = None, cas_rn: str = None) -> List[MolecularInitiatingEvent]:
        """
        Retrieve Molecular Initiating Events associated with a specific chemical.
        
        Args:
            chemical_name: Name of the chemical.
            cas_rn: CAS registry number of the chemical.
            
        Returns:
            List of MolecularInitiatingEvent objects.
            
        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        filters = {}
        if chemical_name:
            filters['chemical_name'] = chemical_name
        if cas_rn:
            filters['cas_rn'] = cas_rn
        
        return self.search_miess(**filters)
    
    def _parse_aop(self, aop_data: Dict) -> AOP:
        """
        Parse AOP data from JSON response.
        
        Args:
            aop_data: Raw AOP data from API.
            
        Returns:
            Parsed AOP object.
        """
        # Extract key events
        key_events = []
        if 'events' in aop_data:
            for event_data in aop_data['events']:
                if event_data.get('event_type') == 'Molecular Initiating Event':
                    key_events.append(MolecularInitiatingEvent.from_dict(event_data))
                else:
                    key_events.append(KeyEvent.from_dict(event_data))
        
        return AOP(
            id=aop_data.get('id'),
            title=aop_data.get('title'),
            description=aop_data.get('description'),
            key_events=key_events
        )
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()