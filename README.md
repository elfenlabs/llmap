# llmap

**Generate navigable "code maps" to help LLMs understand project architecture.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## The Problem

Traditional Code RAG uses vector embeddings to find specific code snippets—great for *"Where is the code that does X?"* But LLMs struggle with the **Big Picture**:

- How do modules interact?
- What is the overall system flow?
- Why was a component designed this way?
- What are the architectural invariants?

**llmap provides the Map**—high-level structural context that helps LLMs orient themselves, navigate dependencies, and reason about architecture.

## Key Features

- 📝 **Text-Based Architecture** — Markdown output is git-friendly, diffable, and readable by humans and LLMs alike
- ⚡ **Incremental Updates** — Content hashing detects changes; only regenerates affected module docs
- 🌳 **Structural Intelligence** — Tree-sitter extracts precise AST data (functions, classes, dependencies)
- 🤖 **LLM-Powered Summarization** — Claude, GPT, Gemini, or local Ollama models generate meaningful descriptions
- 🔄 **Multi-Language Support** — C++ primary; extensible via tree-sitter parsers

## Installation

```bash
# From PyPI
pip install llmap

# Or from source
pip install -e .
```

## Quick Start

```bash
# Initialize a new codemap
llmap init

# Generate/update the code map
llmap update

# Check if map is up-to-date (useful for CI)
llmap status

# Force full rebuild
llmap update --full

# Preview changes without updating
llmap update --dry-run

# Clean generated files (keeps config)
llmap clean
```

## Configuration

After `llmap init`, edit `.codemap/config.yaml`:

```yaml
# LLM provider configuration
llm:
  provider: anthropic  # Options: anthropic, openai, gemini, ollama
  model: claude-sonnet-4-20250514

# What files to analyze
include:
  - "src/**/*.cpp"
  - "src/**/*.h"
  - "include/**/*.h"

# What to exclude
exclude:
  - "**/test/**"
  - "**/build/**"
  - "**/vendor/**"

# Module detection strategy
modules:
  strategy: directory  # Options: directory, file
  depth: 2             # e.g., src/parser/ becomes one module
```

## Environment Variables

Set your API key for your chosen provider:

```bash
export ANTHROPIC_API_KEY=your-key-here
# or
export OPENAI_API_KEY=your-key-here
# or
export GEMINI_API_KEY=your-key-here
```

### Using Local LLMs (Ollama)

For free, private, unlimited usage:

1. Install [Ollama](https://ollama.com/) and run a model: `ollama run qwen2.5:7b`
2. Configure:
   ```yaml
   llm:
     provider: ollama
     model: qwen2.5:7b
     api_base: http://localhost:11434
   ```

## Output Structure

```text
.codemap/
├── config.yaml      # Your configuration
├── state.json       # Change tracking (hashes, timestamps)
├── overview.md      # High-level module index
└── modules/
    ├── src_parser.md
    ├── src_codegen.md
    └── ...
```

Each module file includes:
- **Purpose** — What problem the module solves
- **Dependencies** — Upstream/downstream relationships
- **Key Components** — Important classes and functions
- **Invariants** — Architectural assumptions and constraints

## Using with LLM Agents

Point your AI agent to the codemap for context:

```markdown
## Architecture
Read `.codemap/overview.md` for the module map before starting.
```

Or include in project context files (`.cursorrules`, `.agent/project.md`, etc.):

```markdown
## Architecture Reference
- `.codemap/overview.md` - System architecture
- `.codemap/modules/` - Per-module documentation
```

## Module Strategy Patterns

**Flat projects** (single `src/` directory):
```yaml
modules:
  strategy: directory
  depth: 1  # Treats src/ as one module
```

**Deep nesting** (e.g., `src/parser/lexer/`):
```yaml
modules:
  strategy: directory
  depth: 2  # Groups by second level
```

## Roadmap

- [ ] Watch mode (auto-update on file save)
- [ ] Git hooks (pre-commit staleness warning)
- [ ] CI integration (GitHub Action)
- [ ] Cross-references (auto-link modules by imports)
- [ ] MCP server (Model Context Protocol)
- [ ] Python/Rust/TypeScript language support

## License

MIT
