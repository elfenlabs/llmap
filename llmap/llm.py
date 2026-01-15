"""LLM client abstraction using litellm."""

from .config import Config
from .modules import Module
from .parser import FileStructure, FunctionInfo, Visibility


# LLM prompt template for module summarization
MODULE_PROMPT = """\
You are generating documentation for a code module to help other LLMs understand the codebase architecture.

## Module: {module_name}

## Files:
{file_list}

## Extracted Structure:
{structure_summary}

Generate a markdown document following this template:

```markdown
# Module: {module_name}

**Purpose**: [One sentence describing what this module does]

**Location**: `{module_path}`

## Dependencies

**Depends on**:
- [List modules/libraries this depends on, with brief explanation]

**Depended by**:
- [List modules that depend on this, or "Unknown" if cannot determine]

## Key Components

- `ComponentName` – Brief description
- [List most important classes/functions]

## Public Interface

- `function_signature` – What it does
- [List main public APIs]

## Invariants & Design Notes

- [Important rules, assumptions, or design decisions]

## File List

- `filename.cpp` – Brief purpose
- [List all files with one-line descriptions]
```

Focus on:
- The module's PURPOSE (what problem it solves)
- Its DEPENDENCIES (what it needs, what needs it)
- KEY COMPONENTS (most important functions/classes)
- INVARIANTS (important rules/assumptions)

Be concise. Avoid restating obvious code. Focus on architectural understanding.
"""


def _partition_by_visibility(
    items: list[FunctionInfo],
) -> tuple[list[FunctionInfo], list[FunctionInfo], list[FunctionInfo]]:
    """Partition functions/methods by visibility: public, protected, private."""
    public = []
    protected = []
    private = []
    
    for item in items:
        if item.visibility == Visibility.PUBLIC:
            public.append(item)
        elif item.visibility == Visibility.PROTECTED:
            protected.append(item)
        else:  # PRIVATE or UNKNOWN treated as internal
            private.append(item)
    
    return public, protected, private


def _format_internal_summary(
    protected: list[FunctionInfo], 
    private: list[FunctionInfo],
) -> list[str]:
    """Format a compact summary of internal (non-public) items."""
    lines = []
    
    total_internal = len(protected) + len(private)
    if total_internal == 0:
        return lines
    
    # Collect all internal names
    internal_names = [f.name for f in protected] + [f.name for f in private]
    
    # Show first few names, then "..." 
    max_preview = 6
    if len(internal_names) <= max_preview:
        names_str = ", ".join(internal_names)
    else:
        names_str = ", ".join(internal_names[:max_preview]) + ", ..."
    
    lines.append(f"    Internal ({total_internal} total): {names_str}")
    
    return lines


def _format_structure(structures: list[FileStructure]) -> str:
    """Format extracted structures for the LLM prompt.
    
    Uses a tiered approach to balance completeness with token limits:
    - Public API: Full signatures always included
    - Internal symbols: Summarized with counts and names
    """
    lines = []
    
    for struct in structures:
        lines.append(f"\n### {struct.path.name}")
        
        # Format imports - group by system vs local
        if struct.imports:
            system_imports = [i for i in struct.imports if i.is_system]
            local_imports = [i for i in struct.imports if not i.is_system]
            
            lines.append("\nDependencies:")
            if system_imports:
                lines.append(f"  System ({len(system_imports)}): " + 
                           ", ".join(i.name for i in system_imports[:8]) +
                           ("..." if len(system_imports) > 8 else ""))
            if local_imports:
                lines.append(f"  Local ({len(local_imports)}): " + 
                           ", ".join(i.name for i in local_imports[:10]) +
                           ("..." if len(local_imports) > 10 else ""))
        
        # Format classes with tiered method display
        if struct.classes:
            lines.append("\nClasses/Structs:")
            for cls in struct.classes:
                lines.append(f"  **{cls.name}** (lines {cls.line_start}-{cls.line_end})")
                
                if cls.methods:
                    public, protected, private = _partition_by_visibility(cls.methods)
                    
                    # Public methods: full signatures
                    if public:
                        lines.append("    Public API:")
                        for method in public:
                            lines.append(f"      - {method.signature}")
                    
                    # Internal methods: summarized
                    lines.extend(_format_internal_summary(protected, private))
        
        # Format top-level functions with tiered display
        if struct.functions:
            public, protected, private = _partition_by_visibility(struct.functions)
            
            if public:
                lines.append("\nPublic Functions:")
                for func in public:
                    lines.append(f"  - {func.signature}")
            
            # Internal functions summary
            if protected or private:
                internal_lines = _format_internal_summary(protected, private)
                if internal_lines:
                    lines.append("\nInternal Functions:")
                    lines.extend(internal_lines)
    
    return "\n".join(lines)


def _format_file_list(module: Module) -> str:
    """Format file list for prompt."""
    lines = []
    for path, _ in module.files:
        lines.append(f"- {path.name}")
    return "\n".join(lines)


class LLMClient:
    """Wrapper around litellm for LLM interactions."""
    
    def __init__(self, config: Config):
        self.config = config
        self.model = f"{config.llm.provider}/{config.llm.model}"
    
    def summarize_module(
        self,
        module: Module,
        structures: list[FileStructure],
    ) -> str:
        """Generate a markdown summary for a module."""
        import os
        import litellm
        
        # Set Ollama base URL if configured
        if self.config.llm.provider == "ollama" and self.config.llm.api_base:
            os.environ["OLLAMA_API_BASE"] = self.config.llm.api_base
        
        prompt = MODULE_PROMPT.format(
            module_name=module.name,
            module_path=module.path,
            file_list=_format_file_list(module),
            structure_summary=_format_structure(structures),
        )
        
        response = litellm.completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Lower temperature for more consistent output
        )
        
        content = response.choices[0].message.content
        
        # Strip markdown code fences if present
        if content.startswith("```markdown"):
            content = content[len("```markdown"):].strip()
        if content.startswith("```"):
            content = content[3:].strip()
        if content.endswith("```"):
            content = content[:-3].strip()
        
        return content
