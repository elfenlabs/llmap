"""Configuration loading and validation."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import yaml


class ConfigError(Exception):
    """Raised when configuration is invalid."""
    pass


@dataclass
class LLMConfig:
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    api_base: Optional[str] = None  # Custom API base URL (e.g., for Ollama on WSL2)


@dataclass
class ModulesConfig:
    strategy: str = "directory"
    depth: int = 2


@dataclass
class OutputConfig:
    include_diagrams: bool = True
    detail_level: str = "standard"


@dataclass
class Config:
    llm: LLMConfig = field(default_factory=LLMConfig)
    include: list[str] = field(default_factory=lambda: [
        "src/**/*.cpp",
        "src/**/*.h",
        "src/**/*.hpp",
        "include/**/*.h",
        "include/**/*.hpp",
    ])
    exclude: list[str] = field(default_factory=lambda: [
        "**/test/**",
        "**/tests/**",
        "**/vendor/**",
        "**/third_party/**",
        "**/build/**",
    ])
    modules: ModulesConfig = field(default_factory=ModulesConfig)
    output: OutputConfig = field(default_factory=OutputConfig)


def load_config(path: Path) -> Config:
    """Load configuration from YAML file."""
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    
    try:
        with open(path) as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML: {e}")
    
    config = Config()
    
    if "llm" in data:
        config.llm = LLMConfig(
            provider=data["llm"].get("provider", config.llm.provider),
            model=data["llm"].get("model", config.llm.model),
            api_base=data["llm"].get("api_base"),
        )
    
    if "include" in data:
        config.include = data["include"]
    
    if "exclude" in data:
        config.exclude = data["exclude"]
    
    if "modules" in data:
        config.modules = ModulesConfig(
            strategy=data["modules"].get("strategy", config.modules.strategy),
            depth=data["modules"].get("depth", config.modules.depth),
        )
    
    if "output" in data:
        config.output = OutputConfig(
            include_diagrams=data["output"].get("include_diagrams", config.output.include_diagrams),
            detail_level=data["output"].get("detail_level", config.output.detail_level),
        )
    
    return config


def create_default_config(path: Path):
    """Create a default configuration file."""
    default_yaml = """\
# Cartographer configuration

# LLM provider configuration
llm:
  provider: anthropic  # Options: anthropic, openai, gemini, ollama
  model: claude-sonnet-4-20250514
  # API key read from environment: ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, etc.

# What files to analyze
include:
  - "src/**/*.cpp"
  - "src/**/*.h"
  - "src/**/*.hpp"
  - "include/**/*.h"
  - "include/**/*.hpp"

# What to exclude
exclude:
  - "**/test/**"
  - "**/tests/**"
  - "**/vendor/**"
  - "**/third_party/**"
  - "**/build/**"

# Module detection strategy
modules:
  # How to identify module boundaries
  strategy: directory  # Options: directory, file, custom
  
  # For 'directory' strategy: which level defines a module
  depth: 2  # src/parser/ is one module, src/codegen/ is another

# Output customization
output:
  # Generate a mermaid diagram in overview.md
  include_diagrams: true
  
  # Maximum detail level (brief, standard, detailed)
  detail_level: standard
"""
    path.write_text(default_yaml)
