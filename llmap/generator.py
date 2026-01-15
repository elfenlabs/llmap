"""Markdown generation for codemap output."""

import hashlib
from datetime import datetime
from pathlib import Path

from . import __version__
from .config import Config
from .modules import Module
from .parser import get_parser_for_file, FileStructure
from .llm import LLMClient


def _format_metadata_footer(
    generated_at: datetime,
    source_hash: str | None = None,
) -> str:
    """Generate metadata footer for codemap documents.
    
    Args:
        generated_at: Timestamp of generation
        source_hash: Combined hash of source files (optional)
    
    Returns:
        Formatted metadata footer string
    """
    timestamp = generated_at.strftime("%Y-%m-%dT%H:%M:%S")
    parts = [f"Generated: {timestamp}"]
    
    if source_hash:
        parts.append(f"Source hash: {source_hash[:7]}")
    
    parts.append(f"llmap v{__version__}")
    
    return f"\n---\n*{' | '.join(parts)}*\n"


def _compute_combined_hash(hashes: list[str]) -> str:
    """Compute a combined hash from a list of file hashes."""
    combined = "".join(sorted(hashes))
    return hashlib.sha256(combined.encode()).hexdigest()


class MapGenerator:
    """Generates markdown documentation for modules."""
    
    def __init__(self, config: Config, codemap_path: Path):
        self.config = config
        self.codemap_path = codemap_path
        self.modules_path = codemap_path / "modules"
        self.llm = LLMClient(config)
    
    def _module_name_to_filename(self, module_name: str) -> str:
        """Convert module name to markdown filename."""
        return module_name.replace("/", "_").replace("\\", "_") + ".md"
    
    def generate_module(self, module: Module) -> tuple[Path, list[FileStructure]]:
        """Generate markdown documentation for a module.
        
        Returns:
            Tuple of (path to generated markdown file, list of parsed structures)
        """
        # Parse all files in the module
        structures: list[FileStructure] = []
        for path, _ in module.files:
            parser = get_parser_for_file(path)
            if parser:
                try:
                    structure = parser.parse(path)
                    structures.append(structure)
                except Exception:
                    # Skip files that fail to parse
                    pass
        
        # Generate summary using LLM
        content = self.llm.summarize_module(module, structures)
        
        # Write to file
        filename = self._module_name_to_filename(module.name)
        output_path = self.modules_path / filename
        
        self.modules_path.mkdir(parents=True, exist_ok=True)
        
        # Compute combined source hash and append metadata
        source_hashes = [h for _, h in module.files]
        combined_hash = _compute_combined_hash(source_hashes)
        content += _format_metadata_footer(datetime.utcnow(), combined_hash)
        
        output_path.write_text(content)
        
        return output_path, structures
    
    def add_related_modules_section(self, module: Module) -> None:
        """Append a Related Modules section to an existing module file.
        
        This adds navigable links to modules that this module depends on
        and modules that depend on this module.
        """
        filename = self._module_name_to_filename(module.name)
        output_path = self.modules_path / filename
        
        if not output_path.exists():
            return
        
        # Build the related modules section
        lines = [
            "",
            "---",
            "",
            "## Related Modules",
            "",
        ]
        
        if module.dependencies:
            lines.append("**Depends on**:")
            for dep_name in sorted(module.dependencies):
                dep_filename = self._module_name_to_filename(dep_name)
                lines.append(f"- [{dep_name}](./{dep_filename})")
            lines.append("")
        
        if module.dependents:
            lines.append("**Depended by**:")
            for dep_name in sorted(module.dependents):
                dep_filename = self._module_name_to_filename(dep_name)
                lines.append(f"- [{dep_name}](./{dep_filename})")
            lines.append("")
        
        if not module.dependencies and not module.dependents:
            lines.append("*No direct module dependencies detected.*")
            lines.append("")
        
        # Append to existing content
        existing_content = output_path.read_text()
        output_path.write_text(existing_content + "\n".join(lines))
    
    def generate_overview(self) -> Path:
        """Generate overview.md that indexes all modules.
        
        Returns:
            Path to the generated overview file.
        """
        overview_path = self.codemap_path / "overview.md"
        
        # Collect all module files
        module_files = sorted(self.modules_path.glob("*.md"))
        
        # Extract module info (name, purpose, consumes, produces)
        modules_info = []
        for module_file in module_files:
            content = module_file.read_text()
            lines = content.split("\n")
            name = module_file.stem.replace("_", "/")
            
            purpose = ""
            consumes = ""
            produces = ""
            
            for line in lines:
                if line.startswith("**Purpose**:"):
                    purpose = line.replace("**Purpose**:", "").strip()
                elif line.startswith("**Consumes**:"):
                    consumes = line.replace("**Consumes**:", "").strip()
                elif line.startswith("**Produces**:"):
                    produces = line.replace("**Produces**:", "").strip()
            
            modules_info.append({
                "name": name,
                "file": module_file.name,
                "purpose": purpose,
                "consumes": consumes,
                "produces": produces,
            })
        
        # Group modules by category (first path component)
        categories: dict[str, list[dict]] = {}
        for info in modules_info:
            parts = info["name"].split("/")
            category = parts[0].title() if len(parts) > 1 else "Core"
            if category not in categories:
                categories[category] = []
            categories[category].append(info)
        
        # Build output
        lines = [
            "# Code Map Overview",
            "",
            "This document provides a high-level overview of the codebase architecture.",
            "",
            "## Module Dependency Graph",
            "",
        ]
        
        # Generate dependency graph grouped by category
        for category, mods in sorted(categories.items()):
            lines.append(f"### {category}")
            lines.append("")
            for mod in mods:
                parts = []
                if mod["consumes"]:
                    parts.append(f"consumes: {mod['consumes']}")
                if mod["produces"]:
                    parts.append(f"produces: {mod['produces']}")
                
                if parts:
                    lines.append(f"- `{mod['name']}` → {' | '.join(parts)}")
                else:
                    lines.append(f"- `{mod['name']}`")
            lines.append("")
        
        # Module list section
        lines.append("## Modules")
        lines.append("")
        
        for info in modules_info:
            rel_path = f"modules/{info['file']}"
            lines.append(f"- [{info['name']}]({rel_path}) – {info['purpose']}")
        
        # Append metadata footer
        content = "\n".join(lines)
        content += _format_metadata_footer(datetime.utcnow())
        
        overview_path.write_text(content)
        return overview_path
