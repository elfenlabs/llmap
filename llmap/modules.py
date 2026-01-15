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
    dependencies: set[str] = field(default_factory=set)  # Module names this depends on
    dependents: set[str] = field(default_factory=set)  # Module names that depend on this
    
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


class DependencyResolver:
    """Resolves dependencies between modules based on import analysis."""
    
    def __init__(self, modules: list[Module]):
        self.modules = modules
        self.root = Path.cwd()
        # Map from file path (relative) to module name
        self._file_to_module: dict[str, str] = {}
        for module in modules:
            for path, _ in module.files:
                rel_path = str(path.relative_to(self.root))
                self._file_to_module[rel_path] = module.name
                # Also map by filename for simple includes
                self._file_to_module[path.name] = module.name
    
    def resolve_import(self, importing_file: Path, import_name: str) -> str | None:
        """Resolve an import to a module name.
        
        Args:
            importing_file: The file containing the import
            import_name: The import path (e.g., "../lexer/token.h" or "semantic.h")
            
        Returns:
            Module name if resolved, None otherwise
        """
        # Try direct filename match first
        if import_name in self._file_to_module:
            return self._file_to_module[import_name]
        
        # Try resolving relative path from importing file's directory
        try:
            import_path = (importing_file.parent / import_name).resolve()
            rel_path = str(import_path.relative_to(self.root))
            if rel_path in self._file_to_module:
                return self._file_to_module[rel_path]
        except (ValueError, OSError):
            pass
        
        return None
    
    def build_dependency_graph(
        self,
        module_structures: dict[str, list["FileStructure"]]
    ) -> None:
        """Build bidirectional dependency graph for all modules.
        
        Args:
            module_structures: Map from module name to list of parsed FileStructures
        """
        from .parser import FileStructure  # Import here to avoid circular import
        
        module_by_name = {m.name: m for m in self.modules}
        
        for module in self.modules:
            structures = module_structures.get(module.name, [])
            
            for structure in structures:
                for imp in structure.imports:
                    # Skip system imports
                    if imp.is_system:
                        continue
                    
                    target_module = self.resolve_import(structure.path, imp.name)
                    if target_module and target_module != module.name:
                        # Add dependency: this module depends on target
                        module.dependencies.add(target_module)
                        # Add reverse: target is depended on by this module
                        if target_module in module_by_name:
                            module_by_name[target_module].dependents.add(module.name)

