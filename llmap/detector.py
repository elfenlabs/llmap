"""Change detection using content hashing."""

import hashlib
from fnmatch import fnmatch
from pathlib import Path

from .config import Config
from .state import StateManager


class ChangeDetector:
    """Detects file changes using content hashing."""
    
    def __init__(self, config: Config, state: StateManager):
        self.config = config
        self.state = state
        self.root = Path.cwd()
    
    def _hash_file(self, path: Path) -> str:
        """Compute SHA-256 hash of file content."""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return f"sha256:{hasher.hexdigest()}"
    
    def _matches_pattern(self, path: Path, pattern: str) -> bool:
        """Check if path matches a glob pattern."""
        rel_path = str(path.relative_to(self.root))
        # Handle ** patterns
        if "**" in pattern:
            parts = pattern.split("**")
            if len(parts) == 2:
                prefix, suffix = parts
                prefix = prefix.rstrip("/")
                suffix = suffix.lstrip("/")
                
                # Check if path starts with prefix (if any)
                if prefix and not rel_path.startswith(prefix):
                    return False
                
                # Check if path ends with suffix pattern
                if suffix:
                    return fnmatch(rel_path, f"*{suffix}")
                return True
        return fnmatch(rel_path, pattern)
    
    def _should_include(self, path: Path) -> bool:
        """Check if file should be included based on config patterns."""
        # Check excludes first
        for pattern in self.config.exclude:
            if self._matches_pattern(path, pattern):
                return False
        
        # Check includes
        for pattern in self.config.include:
            if self._matches_pattern(path, pattern):
                return True
        
        return False
    
    def get_all_files(self) -> list[tuple[Path, str]]:
        """Get all files matching include patterns with their hashes."""
        files = []
        
        for path in self.root.rglob("*"):
            if path.is_file() and self._should_include(path):
                file_hash = self._hash_file(path)
                files.append((path, file_hash))
        
        return files
    
    def get_changed_files(self) -> list[tuple[Path, str]]:
        """Get files that have changed since last run."""
        changed = []
        
        for path, file_hash in self.get_all_files():
            rel_path = str(path.relative_to(self.root))
            stored_hash = self.state.get_file_hash(rel_path)
            
            if stored_hash != file_hash:
                changed.append((path, file_hash))
        
        return changed
