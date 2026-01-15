"""Markdown generation for codemap output."""

from pathlib import Path

from .config import Config
from .modules import Module
from .parser import get_parser_for_file, FileStructure
from .llm import LLMClient


class MapGenerator:
    """Generates markdown documentation for modules."""
    
    def __init__(self, config: Config, codemap_path: Path):
        self.config = config
        self.codemap_path = codemap_path
        self.modules_path = codemap_path / "modules"
        self.llm = LLMClient(config)
    
    def generate_module(self, module: Module) -> Path:
        """Generate markdown documentation for a module.
        
        Returns:
            Path to the generated markdown file.
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
        # Convert module name to filename (e.g., "src/parser" -> "src_parser.md")
        filename = module.name.replace("/", "_").replace("\\", "_") + ".md"
        output_path = self.modules_path / filename
        
        self.modules_path.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
        
        return output_path
    
    def generate_overview(self) -> Path:
        """Generate overview.md that indexes all modules.
        
        Returns:
            Path to the generated overview file.
        """
        overview_path = self.codemap_path / "overview.md"
        
        # Collect all module files
        module_files = sorted(self.modules_path.glob("*.md"))
        
        # Extract module info (name, purpose, consumes, produces, depends_on)
        modules_info = []
        for module_file in module_files:
            content = module_file.read_text()
            name = module_file.stem.replace("_", "/")
            
            # Extract purpose
            purpose = ""
            for line in content.split("\n"):
                if line.startswith("**Purpose**:"):
                    purpose = line.replace("**Purpose**:", "").strip()
                    break
            
            # Extract consumes
            consumes = ""
            for line in content.split("\n"):
                if line.startswith("**Consumes**:"):
                    consumes = line.replace("**Consumes**:", "").strip()
                    break
            
            # Extract produces
            produces = ""
            for line in content.split("\n"):
                if line.startswith("**Produces**:"):
                    produces = line.replace("**Produces**:", "").strip()
                    break
            
            # Extract depends_on list
            depends_on = []
            in_depends_section = False
            for line in content.split("\n"):
                if line.startswith("**Depends on**:"):
                    in_depends_section = True
                    continue
                if in_depends_section:
                    if line.startswith("**") or (line.strip() and not line.startswith("-")):
                        break
                    if line.strip().startswith("- `"):
                        # Extract module name from "- `module_name` – description"
                        dep = line.strip()[3:]  # Remove "- `"
                        if "`" in dep:
                            dep = dep.split("`")[0]
                            depends_on.append(dep)
            
            modules_info.append({
                "name": name,
                "file": module_file.name,
                "purpose": purpose,
                "consumes": consumes,
                "produces": produces,
                "depends_on": depends_on,
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
        
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("*Generated by llmap*")
        
        overview_path.write_text("\n".join(lines))
        return overview_path
