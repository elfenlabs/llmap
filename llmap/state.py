"""State file management for incremental updates."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class FileState:
    hash: str
    module: str


@dataclass
class ModuleState:
    generated_at: str
    source_hashes: list[str]


@dataclass
class State:
    version: int = 1
    last_run: Optional[str] = None
    files: dict[str, FileState] = field(default_factory=dict)
    modules: dict[str, ModuleState] = field(default_factory=dict)


class StateManager:
    """Manages the .codemap/state.json file."""
    
    def __init__(self, path: Path):
        self.path = path
        self.state = self._load()
    
    def _load(self) -> State:
        """Load state from file, or return empty state."""
        if not self.path.exists():
            return State()
        
        try:
            with open(self.path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return State()
        
        state = State(
            version=data.get("version", 1),
            last_run=data.get("last_run"),
        )
        
        for filepath, file_data in data.get("files", {}).items():
            state.files[filepath] = FileState(
                hash=file_data["hash"],
                module=file_data["module"],
            )
        
        for module_name, module_data in data.get("modules", {}).items():
            state.modules[module_name] = ModuleState(
                generated_at=module_data["generated_at"],
                source_hashes=module_data["source_hashes"],
            )
        
        return state
    
    def get_file_hash(self, filepath: str) -> Optional[str]:
        """Get the stored hash for a file."""
        if filepath in self.state.files:
            return self.state.files[filepath].hash
        return None
    
    def update(self, files: list[tuple[str, str, str]]):
        """Update state with new file hashes.
        
        Args:
            files: List of (filepath, hash, module_name) tuples
        """
        now = datetime.utcnow().isoformat() + "Z"
        self.state.last_run = now
        
        # Group by module
        module_hashes: dict[str, list[str]] = {}
        
        for filepath, file_hash, module_name in files:
            self.state.files[filepath] = FileState(hash=file_hash, module=module_name)
            
            if module_name not in module_hashes:
                module_hashes[module_name] = []
            module_hashes[module_name].append(file_hash)
        
        # Update module states
        for module_name, hashes in module_hashes.items():
            self.state.modules[module_name] = ModuleState(
                generated_at=now,
                source_hashes=hashes,
            )
    
    def save(self):
        """Save state to file."""
        data = {
            "version": self.state.version,
            "last_run": self.state.last_run,
            "files": {
                filepath: {"hash": fs.hash, "module": fs.module}
                for filepath, fs in self.state.files.items()
            },
            "modules": {
                name: {"generated_at": ms.generated_at, "source_hashes": ms.source_hashes}
                for name, ms in self.state.modules.items()
            },
        }
        
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)
