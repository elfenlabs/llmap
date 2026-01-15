# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-01-15

### Added
- Initial release of llmap
- CLI commands: `init`, `update`, `status`, `clean`
- Tree-sitter based C++ parsing for structural extraction
- LLM-powered summarization via litellm (Anthropic, OpenAI, Gemini, Ollama)
- Incremental updates using content hashing
- Module grouping strategies: `directory` and `file`
- Configurable include/exclude patterns
- Automatic `overview.md` generation with module index
- Lazy imports for fast CLI startup (~33ms)
- WSL2 + Ollama connectivity support

### Infrastructure
- Python 3.10+ with hatchling build system
- MIT License

[Unreleased]: https://github.com/elfenlabs/llmap/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/elfenlabs/llmap/releases/tag/v0.1.0
