"""Module grouping logic."""

from dataclasses import dataclass, field
from pathlib import Path

from .config import Config


@dataclass
class Module:
    """Represents a logical module grouping."""
    name: str
    path: Path
    files: list[tuple[Path, str]] = field(default_factory=list)  # (path, hash)
    
    def add_file(self, path: Path, file_hash: str):
        self.files.append((path, file_hash))


class ModuleGrouper:
    """Groups files into logical modules based on directory structure."""
    
    def __init__(self, config: Config):
        self.config = config
        self.root = Path.cwd()
    
    def _get_module_name(self, path: Path) -> str:
        """Determine module name for a file based on strategy."""
        rel_path = path.relative_to(self.root)
        parts = rel_path.parts
        
        if self.config.modules.strategy == "directory":
            # Use directory at configured depth as module name
            depth = self.config.modules.depth
            if len(parts) > depth:
                return "/".join(parts[:depth])
            elif len(parts) > 1:
                return "/".join(parts[:-1])  # All but filename
            else:
                return "root"
        
        elif self.config.modules.strategy == "file":
            # Each file is its own module
            return str(rel_path.with_suffix(""))
        
        else:
            # Default: use parent directory
            if len(parts) > 1:
                return str(rel_path.parent)
            return "root"
    
    def group_files(self, files: list[tuple[Path, str]]) -> list[Module]:
        """Group files into modules.
        
        Args:
            files: List of (path, hash) tuples
            
        Returns:
            List of Module objects
        """
        modules: dict[str, Module] = {}
        
        for path, file_hash in files:
            module_name = self._get_module_name(path)
            
            if module_name not in modules:
                # Determine module path (directory containing the module)
                rel_path = path.relative_to(self.root)
                parts = rel_path.parts
                
                if self.config.modules.strategy == "directory":
                    depth = self.config.modules.depth
                    if len(parts) > depth:
                        module_path = self.root / Path(*parts[:depth])
                    else:
                        module_path = path.parent
                else:
                    module_path = path.parent
                
                modules[module_name] = Module(name=module_name, path=module_path)
            
            modules[module_name].add_file(path, file_hash)
        
        return list(modules.values())
