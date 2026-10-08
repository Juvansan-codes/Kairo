from typing import Dict, Any
from .interface import ReconstructionBaseline

class StubBaseline(ReconstructionBaseline):
    def __init__(self, name: str):
        self._name = name
        
    def reconstruct(self, input_path: str) -> Dict[str, Any]:
        return {}
        
    @property
    def name(self) -> str:
        return self._name

class UnavailableBaseline(ReconstructionBaseline):
    def __init__(self, name: str):
        self._name = name
        
    def reconstruct(self, input_path: str) -> Dict[str, Any]:
        raise NotImplementedError("METHOD_UNAVAILABLE")
        
    @property
    def name(self) -> str:
        return self._name
