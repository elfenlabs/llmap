"""LLM client abstraction using litellm."""

from .config import Config
from .modules import Module
from .parser import FileStructure


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

**Consumes**: [What data/artifacts this module takes as input, e.g., "Source files", "Token stream", "AST"]

**Produces**: [What data/artifacts this module outputs, e.g., "Token stream", "AST", "Bytecode"]

## Dependencies

**Depends on**:
- `module_name` – [Brief explanation of what is used from this module]
- [List modules/libraries this depends on]

**Depended by**:
- `module_name` – [Brief explanation of how this module is used]
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
- What it CONSUMES and PRODUCES (data flow)
- KEY COMPONENTS (most important functions/classes)
- INVARIANTS (important rules/assumptions)

Be concise. Avoid restating obvious code. Focus on architectural understanding.
"""


def _format_structure(structures: list[FileStructure]) -> str:
    """Format extracted structures for the LLM prompt."""
    lines = []
    
    for struct in structures:
        lines.append(f"\n### {struct.path.name}")
        
        if struct.imports:
            lines.append("\nIncludes:")
            for imp in struct.imports[:10]:  # Limit to 10
                prefix = "<system>" if imp.is_system else "<local>"
                lines.append(f"  - {prefix} {imp.name}")
            if len(struct.imports) > 10:
                lines.append(f"  ... and {len(struct.imports) - 10} more")
        
        if struct.classes:
            lines.append("\nClasses/Structs:")
            for cls in struct.classes:
                lines.append(f"  - {cls.name} (lines {cls.line_start}-{cls.line_end})")
                for method in cls.methods[:5]:  # Limit methods
                    lines.append(f"    - {method.name}()")
                if len(cls.methods) > 5:
                    lines.append(f"    ... and {len(cls.methods) - 5} more methods")
        
        if struct.functions:
            lines.append("\nFunctions:")
            for func in struct.functions[:15]:  # Limit to 15
                lines.append(f"  - {func.signature}")
            if len(struct.functions) > 15:
                lines.append(f"  ... and {len(struct.functions) - 15} more")
    
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
