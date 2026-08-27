from __future__ import annotations
from typing import Optional
try:
    from rdkit import Chem
except ImportError:
    Chem = None

def canonicalize_smiles(smiles: str) -> Optional[str]:
    if not smiles or Chem is None:
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return Chem.MolToSmiles(mol, canonical=True)

def is_probable_smiles(value: str) -> bool:
    s = str(value or "").strip()
    return bool(s) and len(s) > 2 and any(ch in s for ch in ("=", "#", "[", "]", "(", ")"))
