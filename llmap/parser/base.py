"""Abstract parser interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Visibility(Enum):
    """Visibility level for functions and classes."""
    PUBLIC = "public"
    PROTECTED = "protected"
    PRIVATE = "private"
    UNKNOWN = "unknown"  # For languages without explicit visibility


@dataclass
class FunctionInfo:
    """Information about a function/method."""
    name: str
    signature: str
    line_start: int
    line_end: int
    docstring: str | None = None
    visibility: Visibility = Visibility.UNKNOWN


@dataclass 
class ClassInfo:
    """Information about a class/struct."""
    name: str
    line_start: int
    line_end: int
    methods: list[FunctionInfo] = field(default_factory=list)
    docstring: str | None = None
    visibility: Visibility = Visibility.UNKNOWN


@dataclass
class ImportInfo:
    """Information about an import/include."""
    name: str
    is_system: bool = False


@dataclass
class FileStructure:
    """Extracted structure from a source file."""
    path: Path
    language: str
    imports: list[ImportInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)


class BaseParser(ABC):
    """Abstract base class for language-specific parsers."""
    
    @property
    @abstractmethod
    def language(self) -> str:
        """Return the language this parser handles."""
        pass
    
    @property
    @abstractmethod
    def extensions(self) -> list[str]:
        """Return file extensions this parser handles."""
        pass
    
    @abstractmethod
    def parse(self, path: Path) -> FileStructure:
        """Parse a source file and extract its structure."""
        pass
    
    def can_parse(self, path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return path.suffix.lower() in self.extensions
