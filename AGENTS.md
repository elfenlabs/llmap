# llmap

**A CLI tool that generates navigable "code maps" to help LLMs understand project architecture.**

## Problem Statement

LLM-based coding agents struggle with large codebases because they lack "the big picture." Vector embeddings help find specific code, but don't capture:
- How modules relate to each other
- The overall flow through the system
- Design rationale and invariants
- Dependency relationships

llmap solves this by generating a structured, markdown-based "map" of the codebase that LLMs can easily ingest and reason about.

---

## Core Concept

Generate a `.codemap/` directory containing:
- **Per-module markdown files** describing purpose, dependencies, key components
- **Overview document** showing high-level architecture
- **Patterns document** for cross-cutting design patterns

The output is:
- **Text-based** – git-trackable, diffable, merge-friendly
- **Incremental** – only regenerates when source files change
- **LLM-generated** – uses an LLM to produce meaningful summaries, not just AST dumps

---

## CLI Interface

```bash
# Initialize a new codemap in the current project
llmap init

# Incrementally update (only changed files since last run)
llmap update

# Force full rebuild
llmap update --full

# Check if map is up-to-date (useful for CI)
llmap status

# Show what would be updated without doing it
llmap update --dry-run
```

---

## Configuration

File: `.codemap/config.yaml`

```yaml
# LLM provider configuration
llm:
  provider: anthropic  # Options: anthropic, openai, ollama
  model: claude-sonnet-4-20250514
  # API key read from environment: ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.

# What files to analyze
include:
  - "src/**/*.cpp"
  - "src/**/*.h"
  - "src/**/*.py"
  - "lib/**/*.rs"

# What to exclude
exclude:
  - "**/test/**"
  - "**/tests/**"
  - "**/vendor/**"
  - "**/node_modules/**"
  - "**/*.generated.*"

# Module detection strategy
modules:
  # How to identify module boundaries
  strategy: directory  # Options: directory, file, custom
  
  # For 'directory' strategy: which level defines a module
  depth: 2  # src/parser/ is one module, src/codegen/ is another
  
  # Optional: explicit module definitions
  # explicit:
  #   - name: "Parser"
  #     paths: ["src/parser/**", "include/parser.h"]
  #   - name: "CodeGen"  
  #     paths: ["src/codegen/**"]

# Output customization
output:
  # Generate a mermaid diagram in overview.md
  include_diagrams: true
  
  # Maximum detail level (brief, standard, detailed)
  detail_level: standard
```

---

## Output Structure

```
.codemap/
├── config.yaml          # Configuration (user-edited)
├── state.json           # Internal: tracks file hashes for incremental updates
├── overview.md          # High-level architecture, module diagram
├── patterns.md          # Cross-cutting design patterns
└── modules/
    ├── parser.md
    ├── semantic.md
    ├── codegen.md
    └── ...
```

### Module File Format

Each module file follows this structure:

```markdown
# Module: parser

**Purpose**: Transforms source text into an Abstract Syntax Tree (AST).

**Location**: `src/parser/`

## Dependencies

**Depends on**:
- [lexer](./lexer.md) – token stream input

**Depended by**:
- [semantic](./semantic.md) – consumes AST for analysis
- [formatter](./formatter.md) – consumes AST for pretty-printing

## Key Components

- `Parser` – Main recursive-descent parser class
- `parse_expression()` – Expression parsing with precedence climbing
- `parse_statement()` – Statement parsing, handles control flow

## Public Interface

- `parse(tokens: TokenStream) -> AST` – Main entry point
- `parse_expression(tokens: TokenStream) -> Expression` – Parse single expression

## Invariants & Design Notes

- Parser never allocates; all AST nodes use arena allocation from caller
- Error recovery uses synchronization tokens (`;`, `}`, `fn`)

## File List

- `parser.cpp` – Main implementation
- `parser.h` – Public interface
- `expression_parser.cpp` – Expression-specific logic
- `precedence.h` – Operator precedence table
```

---

## Implementation Architecture

### Core Pipeline

```
┌─────────────────┐
│  Change Detect  │  ← Git diff or content hash comparison
└────────┬────────┘
         │ List of changed files
         ▼
┌─────────────────┐
│ Module Grouping │  ← Group files into logical modules
└────────┬────────┘
         │ Modules needing update
         ▼
┌─────────────────┐
│ Structure Parse │  ← Extract AST: functions, classes, imports
└────────┬────────┘
         │ Structured data per module
         ▼
┌─────────────────┐
│  LLM Summarize  │  ← Generate human-readable descriptions
└────────┬────────┘
         │ Markdown content
         ▼
┌─────────────────┐
│  Write Output   │  ← Update .codemap/ files
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Update State   │  ← Save hashes to .state.json
└─────────────────┘
```

### Language Support

Use tree-sitter for AST parsing. Start with:
- C/C++ (`tree-sitter-cpp`)
- Python (`tree-sitter-python`)
- Rust (`tree-sitter-rust`)
- TypeScript/JavaScript (`tree-sitter-typescript`)

Each language needs:
1. **Parser binding** – extract functions, classes, imports
2. **Module heuristics** – how to group files into modules (may be language-specific)

### Change Detection

Store in `.codemap/state.json`:
```json
{
  "version": 1,
  "last_run": "2024-01-14T12:00:00Z",
  "files": {
    "src/parser/parser.cpp": {
      "hash": "sha256:abc123...",
      "module": "parser"
    },
    "src/parser/parser.h": {
      "hash": "sha256:def456...",
      "module": "parser"
    }
  },
  "modules": {
    "parser": {
      "generated_at": "2024-01-14T12:00:00Z",
      "source_hashes": ["sha256:abc123...", "sha256:def456..."]
    }
  }
}
```

On `update`:
1. Hash all included files
2. Compare to stored hashes
3. Identify which modules have changed files
4. Regenerate only those module docs

### LLM Prompting Strategy

For each module, send a prompt like:

```
You are generating documentation for a code module to help other LLMs understand the codebase architecture.

## Module: {module_name}
## Files:
{file_list_with_contents}

## Extracted Structure:
{ast_summary: functions, classes, imports, exports}

Generate a markdown document following this template:
[template here]

Focus on:
- The module's PURPOSE (what problem it solves)
- Its DEPENDENCIES (what it needs, what needs it)
- KEY COMPONENTS (most important functions/classes)
- INVARIANTS (important rules/assumptions)

Be concise. Avoid restating obvious code. Focus on architectural understanding.
```

---

## Technology Choices

### Recommended Stack

- **Language**: Python or Rust – Python is faster to prototype with good LLM libs; Rust offers single binary distribution
- **CLI framework**: Click (Python) or Clap (Rust) – both mature, well-documented
- **AST parsing**: tree-sitter – multi-language, fast, well-maintained
- **LLM client**: litellm (Python) – unified API for OpenAI, Anthropic, Ollama, etc.
- **Config parsing**: PyYAML / serde_yaml – standard YAML parsers
- **Hashing**: hashlib / sha2 – for content-based change detection

### Python-Specific

```
llmap/
├── __init__.py
├── cli.py              # Click-based CLI
├── config.py           # Config loading/validation
├── detector.py         # Change detection logic
├── parser/
│   ├── __init__.py
│   ├── base.py         # Abstract parser interface
│   ├── cpp.py          # C++ tree-sitter parser
│   ├── python.py       # Python tree-sitter parser
│   └── rust.py         # Rust tree-sitter parser
├── modules.py          # Module grouping logic
├── llm.py              # LLM client abstraction
├── generator.py        # Markdown generation
└── state.py            # State file management
```

---

## Future Enhancements

### Phase 2
- **Watch mode**: `llmap watch` – auto-update on file save
- **Git hooks**: Pre-commit hook to warn if map is stale
- **CI integration**: GitHub Action to validate map freshness

### Phase 3
- **Cross-references**: Auto-link between module docs based on imports
- **Dependency graph**: Generate visual dependency diagram
- **Search index**: Optional vector embeddings for semantic search

### Phase 4
- **IDE plugins**: VS Code extension to show map inline
- **MCP server**: Expose map via Model Context Protocol for agent consumption

---

## Success Criteria

1. **Correctness**: Generated maps accurately reflect code structure
2. **Usefulness**: An LLM reading the map can answer "where is X?" and "how does Y work?"
3. **Performance**: Incremental updates complete in seconds, not minutes
4. **Simplicity**: Setup is `pip install llmap && llmap init`

---

## Getting Started (For Implementing Agent)

1. Start with Python + Click for rapid prototyping
2. Implement `init` command first (create config, empty .codemap/)
3. Implement basic change detection (file hashing)
4. Add tree-sitter parsing for one language (start with C++ for your project)
5. Integrate LLM summarization (use litellm for provider flexibility)
6. Implement `update` command
7. Add more language parsers incrementally
8. Add `status` and `--dry-run` commands
9. Write tests using a sample project

The MVP should work on a single C++ project before expanding to multi-language support.