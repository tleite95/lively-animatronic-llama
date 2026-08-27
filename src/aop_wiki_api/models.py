"""
AOP Wiki Data Models
====================

Data models for representing Adverse Outcome Pathway (AOP) data retrieved from the AOP Wiki.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class KeyEvent:
    """
    Represents a Key Event in an Adverse Outcome Pathway.
    
    Attributes:
        id: Unique identifier for the key event.
        name: Name of the key event.
        description: Description of the key event.
        event_type: Type of key event (e.g., "Molecular Initiating Event", "Intermediate Event").
        evidence: Evidence supporting the key event.
        references: List of references.
    """
    
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    evidence: Optional[str] = None
    references: Optional[List[str]] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'KeyEvent':
        """
        Create a KeyEvent instance from a dictionary.
        
        Args:
            data: Dictionary containing key event data.
            
        Returns:
            KeyEvent instance.
        """
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            description=data.get('description'),
            event_type=data.get('event_type'),
            evidence=data.get('evidence'),
            references=data.get('references')
        )


@dataclass
class MolecularInitiatingEvent(KeyEvent):
    """
    Represents a Molecular Initiating Event (MIE), a specific type of Key Event.
    
    Attributes:
        chemical_name: Name of the chemical associated with the MIE.
        cas_rn: CAS registry number of the chemical.
        smiles: SMILES representation of the chemical.
        inchi: InChI representation of the chemical.
        inchi_key: InChI key of the chemical.
        target: Molecular target of the MIE.
    """
    
    chemical_name: Optional[str] = None
    cas_rn: Optional[str] = None
    smiles: Optional[str] = None
    inchi: Optional[str] = None
    inchi_key: Optional[str] = None
    target: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MolecularInitiatingEvent':
        """
        Create a MolecularInitiatingEvent instance from a dictionary.
        
        Args:
            data: Dictionary containing MIE data.
            
        Returns:
            MolecularInitiatingEvent instance.
        """
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            description=data.get('description'),
            event_type=data.get('event_type'),
            evidence=data.get('evidence'),
            references=data.get('references'),
            chemical_name=data.get('chemical_name'),
            cas_rn=data.get('cas_rn'),
            smiles=data.get('smiles'),
            inchi=data.get('inchi'),
            inchi_key=data.get('inchi_key'),
            target=data.get('target')
        )


@dataclass
class AOP:
    """
    Represents an Adverse Outcome Pathway.
    
    Attributes:
        id: Unique identifier for the AOP.
        title: Title of the AOP.
        description: Description of the AOP.
        key_events: List of key events in the AOP.
        molecular_initiating_events: List of molecular initiating events in the AOP.
    """
    
    id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    key_events: Optional[List[KeyEvent]] = None
    
    @property
    def molecular_initiating_events(self) -> List[MolecularInitiatingEvent]:
        """
        Get all molecular initiating events in this AOP.
        
        Returns:
            List of MolecularInitiatingEvent objects.
        """
        if self.key_events is None:
            return []
        return [event for event in self.key_events if isinstance(event, MolecularInitiatingEvent)]
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AOP':
        """
        Create an AOP instance from a dictionary.
        
        Args:
            data: Dictionary containing AOP data.
            
        Returns:
            AOP instance.
        """
        key_events = []
        if 'events' in data:
            for event_data in data['events']:
                if event_data.get('event_type') == 'Molecular Initiating Event':
                    key_events.append(MolecularInitiatingEvent.from_dict(event_data))
                else:
                    key_events.append(KeyEvent.from_dict(event_data))
        
        return cls(
            id=data.get('id'),
            title=data.get('title'),
            description=data.get('description'),
            key_events=key_events
        )