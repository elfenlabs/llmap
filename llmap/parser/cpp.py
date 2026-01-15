"""C++ parser using tree-sitter."""

from pathlib import Path

import tree_sitter_cpp as tscpp
from tree_sitter import Language, Parser

from .base import (
    BaseParser,
    ClassInfo,
    FileStructure,
    FunctionInfo,
    ImportInfo,
)


class CppParser(BaseParser):
    """Parser for C/C++ source files using tree-sitter."""
    
    def __init__(self):
        self._parser = Parser(Language(tscpp.language()))
    
    @property
    def language(self) -> str:
        return "cpp"
    
    @property
    def extensions(self) -> list[str]:
        return [".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".hxx"]
    
    def parse(self, path: Path) -> FileStructure:
        """Parse a C++ file and extract its structure."""
        content = path.read_bytes()
        tree = self._parser.parse(content)
        
        structure = FileStructure(path=path, language=self.language)
        
        self._extract_includes(tree.root_node, content, structure)
        self._extract_classes(tree.root_node, content, structure)
        self._extract_functions(tree.root_node, content, structure)
        
        return structure
    
    def _get_text(self, node, content: bytes) -> str:
        """Extract text from a node."""
        return content[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
    
    def _extract_includes(self, root, content: bytes, structure: FileStructure):
        """Extract #include directives."""
        for node in self._find_nodes(root, "preproc_include"):
            path_node = node.child_by_field_name("path")
            if path_node:
                path_text = self._get_text(path_node, content)
                is_system = path_text.startswith("<")
                # Strip quotes/brackets
                name = path_text.strip('<>"')
                structure.imports.append(ImportInfo(name=name, is_system=is_system))
    
    def _extract_classes(self, root, content: bytes, structure: FileStructure):
        """Extract class/struct definitions."""
        for node_type in ["class_specifier", "struct_specifier"]:
            for node in self._find_nodes(root, node_type):
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = self._get_text(name_node, content)
                    
                    class_info = ClassInfo(
                        name=name,
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                    )
                    
                    # Extract methods
                    body_node = node.child_by_field_name("body")
                    if body_node:
                        for method in self._find_nodes(body_node, "function_definition"):
                            method_info = self._extract_function_info(method, content)
                            if method_info:
                                class_info.methods.append(method_info)
                    
                    structure.classes.append(class_info)
    
    def _extract_functions(self, root, content: bytes, structure: FileStructure):
        """Extract top-level function definitions."""
        for node in self._find_nodes(root, "function_definition"):
            # Skip if inside a class
            parent = node.parent
            while parent:
                if parent.type in ["class_specifier", "struct_specifier"]:
                    break
                parent = parent.parent
            else:
                func_info = self._extract_function_info(node, content)
                if func_info:
                    structure.functions.append(func_info)
    
    def _extract_function_info(self, node, content: bytes) -> FunctionInfo | None:
        """Extract function information from a function_definition node."""
        declarator = node.child_by_field_name("declarator")
        if not declarator:
            return None
        
        # Find the function name
        name = self._find_function_name(declarator, content)
        if not name:
            return None
        
        # Build signature from return type + declarator
        type_node = node.child_by_field_name("type")
        if type_node:
            signature = f"{self._get_text(type_node, content)} {self._get_text(declarator, content)}"
        else:
            signature = self._get_text(declarator, content)
        
        return FunctionInfo(
            name=name,
            signature=signature.strip(),
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )
    
    def _find_function_name(self, declarator, content: bytes) -> str | None:
        """Recursively find function name in declarator."""
        if declarator.type == "identifier":
            return self._get_text(declarator, content)
        
        if declarator.type == "qualified_identifier":
            # Get the last part (actual name)
            name_node = declarator.child_by_field_name("name")
            if name_node:
                return self._get_text(name_node, content)
        
        if declarator.type == "function_declarator":
            inner = declarator.child_by_field_name("declarator")
            if inner:
                return self._find_function_name(inner, content)
        
        # Check children
        for child in declarator.children:
            result = self._find_function_name(child, content)
            if result:
                return result
        
        return None
    
    def _find_nodes(self, root, node_type: str):
        """Find all nodes of a given type."""
        nodes = []
        
        def visit(node):
            if node.type == node_type:
                nodes.append(node)
            for child in node.children:
                visit(child)
        
        visit(root)
        return nodes
