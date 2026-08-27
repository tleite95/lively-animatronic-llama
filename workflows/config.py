# Configuration for AOP workflow
import os
from typing import Dict, Any

class WorkflowConfig:
    """Configuration class for AOP workflow parameters"""
    
    def __init__(self):
        self.similarity_threshold = float(os.environ.get("SIMILARITY_THRESHOLD", "0.3"))
        self.max_iterations = int(os.environ.get("MAX_ITERATIONS", "10"))
        self.stagnation_threshold = int(os.environ.get("STAGNATION_THRESHOLD", "3"))
        self.debug_mode = os.environ.get("DEBUG_MODE", "false").lower() == "true"
        self.save_snapshots = os.environ.get("SAVE_SNAPSHOTS", "false").lower() == "true"
        self.snapshot_dir = os.environ.get("SNAPSHOT_DIR", "./snapshots")
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate configuration parameters"""
        if not (0.0 <= self.similarity_threshold <= 1.0):
            raise ValueError(f"similarity_threshold must be between 0.0 and 1.0, got {self.similarity_threshold}")
        
        if self.max_iterations <= 0:
            raise ValueError(f"max_iterations must be positive, got {self.max_iterations}")
        
        if self.stagnation_threshold <= 0:
            raise ValueError(f"stagnation_threshold must be positive, got {self.stagnation_threshold}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "similarity_threshold": self.similarity_threshold,
            "max_iterations": self.max_iterations,
            "stagnation_threshold": self.stagnation_threshold,
            "debug_mode": self.debug_mode,
            "save_snapshots": self.save_snapshots,
            "snapshot_dir": self.snapshot_dir
        }
    
    def __str__(self) -> str:
        """String representation of configuration"""
        return str(self.to_dict())

# Global configuration instance
config = WorkflowConfig()