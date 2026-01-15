"""Parser package."""

from .base import BaseParser, FileStructure, FunctionInfo, ClassInfo, ImportInfo
from .cpp import CppParser

__all__ = [
    "BaseParser",
    "FileStructure", 
    "FunctionInfo",
    "ClassInfo",
    "ImportInfo",
    "CppParser",
]


def get_parser_for_file(path) -> BaseParser | None:
    """Get appropriate parser for a file based on extension."""
    parsers = [CppParser()]
    
    for parser in parsers:
        if parser.can_parse(path):
            return parser
    
    return None
