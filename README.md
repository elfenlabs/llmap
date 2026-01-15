# Cartographer

**Generate navigable "code maps" to help LLMs understand project architecture.**

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Initialize a new codemap
cartographer init

# Update the code map (incremental)
cartographer update

# Force full rebuild
cartographer update --full

# Check if map is up-to-date
cartographer status

# Preview what would be updated
cartographer update --dry-run
```

## Configuration

After running `cartographer init`, edit `.codemap/config.yaml`:

```yaml
llm:
  provider: anthropic  # or openai, gemini, ollama
  model: claude-sonnet-4-20250514

include:
  - "src/**/*.cpp"
  - "src/**/*.h"

exclude:
  - "**/test/**"
  - "**/build/**"

modules:
  strategy: directory
  depth: 2
```

## Environment Variables

Set your API key:
```bash
export ANTHROPIC_API_KEY=your-key-here
# or
export OPENAI_API_KEY=your-key-here
# or
export GEMINI_API_KEY=your-key-here
```

## Output

The tool generates:
```
.codemap/
├── config.yaml      # Your configuration
├── state.json       # Change tracking
└── modules/
    ├── src_parser.md
    ├── src_codegen.md
    └── ...
```
