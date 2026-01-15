"""Parser package for code structure extraction."""

from .base import BaseParser, FileStructure, FunctionInfo, ClassInfo, ImportInfo, Visibility
from .cpp import CppParser

__all__ = [
    "BaseParser",
    "FileStructure",
    "FunctionInfo",
    "ClassInfo",
    "ImportInfo",
    "Visibility",
    "CppParser",
    "get_parser_for_file",
]


def get_parser_for_file(path) -> BaseParser | None:
    """Get appropriate parser for a file based on extension."""
    parsers = [CppParser()]
    
    for parser in parsers:
        if parser.can_parse(path):
            return parser
    
    return None
