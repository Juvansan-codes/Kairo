import abc
from typing import Dict, Any

class ReconstructionBaseline(abc.ABC):
    """
    Interface for any reconstruction model (baseline or our pipeline).
    """
    
    @abc.abstractmethod
    def reconstruct(self, input_path: str) -> Dict[str, Any]:
        """
        Process the image and return a raw result dictionary.
        This dict should be parseable into a `Prediction` schema.
        """
        pass
        
    @property
    @abc.abstractmethod
    def name(self) -> str:
        return "Baseline"
