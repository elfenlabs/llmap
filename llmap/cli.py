"""Click-based CLI for llmap."""

import click
from pathlib import Path


CODEMAP_DIR = ".codemap"


def _setup_litellm():
    """Suppress litellm noise - call before using LLM features."""
    import os
    import warnings
    os.environ["LITELLM_LOG"] = "ERROR"
    import litellm
    litellm.suppress_debug_info = True
    litellm.set_verbose = False
    warnings.filterwarnings("ignore", module="pydantic")


@click.group()
@click.version_option()
def main():
    """Generate navigable code maps to help LLMs understand project architecture."""
    pass


@main.command()
@click.option("--force", is_flag=True, help="Overwrite existing configuration")
def init(force: bool):
    """Initialize a new codemap in the current project."""
    from .config import create_default_config
    
    codemap_path = Path(CODEMAP_DIR)
    config_path = codemap_path / "config.yaml"
    
    if config_path.exists() and not force:
        click.echo(f"Codemap already initialized. Use --force to reinitialize.")
        raise SystemExit(1)
    
    codemap_path.mkdir(exist_ok=True)
    (codemap_path / "modules").mkdir(exist_ok=True)
    
    create_default_config(config_path)
    
    click.echo(f"✓ Created {config_path}")
    click.echo(f"✓ Created {codemap_path / 'modules'}/")
    click.echo()
    click.echo("Next steps:")
    click.echo(f"  1. Edit {config_path} to configure your project")
    click.echo("  2. Run 'llmap update' to generate the code map")


@main.command()
@click.option("--full", is_flag=True, help="Force full rebuild (ignore cache)")
@click.option("--dry-run", is_flag=True, help="Show what would be updated without doing it")
def update(full: bool, dry_run: bool):
    """Update the code map (incrementally by default)."""
    from .config import load_config, ConfigError
    from .state import StateManager
    from .detector import ChangeDetector
    from .modules import ModuleGrouper
    from .generator import MapGenerator
    
    _setup_litellm()  # Suppress litellm noise before generator uses it
    
    codemap_path = Path(CODEMAP_DIR)
    
    if not codemap_path.exists():
        click.echo("Error: No codemap found. Run 'llmap init' first.")
        raise SystemExit(1)
    
    try:
        config = load_config(codemap_path / "config.yaml")
    except ConfigError as e:
        click.echo(f"Error: {e}")
        raise SystemExit(1)
    
    state = StateManager(codemap_path / "state.json")
    detector = ChangeDetector(config, state)
    grouper = ModuleGrouper(config)
    generator = MapGenerator(config, codemap_path)
    
    # Detect changes
    if full:
        changed_files = detector.get_all_files()
        click.echo("Mode: Full rebuild")
    else:
        changed_files = detector.get_changed_files()
        if not changed_files:
            click.echo("✓ Code map is up-to-date")
            return
    
    # Group into modules
    modules = grouper.group_files(changed_files)
    
    if dry_run:
        click.echo("Would update the following modules:")
        for module in modules:
            click.echo(f"  - {module.name} ({len(module.files)} files)")
        return
    
    # Generate maps
    click.echo(f"Updating {len(modules)} module(s)...")
    for module in modules:
        click.echo(f"  → {module.name}")
        generator.generate_module(module)
    
    # Generate overview index
    generator.generate_overview()
    click.echo("  → overview.md")
    
    # Update state - build list of (filepath, hash, module_name) tuples
    root = Path.cwd()
    file_updates = []
    for module in modules:
        for path, file_hash in module.files:
            rel_path = str(path.relative_to(root))
            file_updates.append((rel_path, file_hash, module.name))
    
    state.update(file_updates)
    state.save()
    
    click.echo(f"✓ Updated {len(modules)} module(s)")


@main.command()
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def clean(yes: bool):
    """Erase the codemap and state, keeping the config."""
    codemap_path = Path(CODEMAP_DIR)
    
    if not codemap_path.exists():
        click.echo("No codemap found. Nothing to clean.")
        return
    
    # Files/dirs to remove (keeping config.yaml)
    state_file = codemap_path / "state.json"
    modules_dir = codemap_path / "modules"
    overview_file = codemap_path / "overview.md"
    
    items_to_remove = []
    if state_file.exists():
        items_to_remove.append(("file", state_file))
    if overview_file.exists():
        items_to_remove.append(("file", overview_file))
    if modules_dir.exists():
        module_files = list(modules_dir.glob("*.md"))
        for f in module_files:
            items_to_remove.append(("file", f))
    
    if not items_to_remove:
        click.echo("✓ Nothing to clean (config preserved)")
        return
    
    if not yes:
        click.echo("Will remove:")
        for item_type, item_path in items_to_remove:
            click.echo(f"  - {item_path}")
        if not click.confirm("Proceed?"):
            click.echo("Aborted.")
            return
    
    # Remove items
    for item_type, item_path in items_to_remove:
        item_path.unlink()
    
    click.echo(f"✓ Cleaned {len(items_to_remove)} item(s) (config preserved)")


@main.command()
def status():
    """Check if the code map is up-to-date."""
    from .config import load_config, ConfigError
    from .state import StateManager
    from .detector import ChangeDetector
    
    codemap_path = Path(CODEMAP_DIR)
    
    if not codemap_path.exists():
        click.echo("No codemap found. Run 'llmap init' first.")
        raise SystemExit(1)
    
    try:
        config = load_config(codemap_path / "config.yaml")
    except ConfigError as e:
        click.echo(f"Error: {e}")
        raise SystemExit(1)
    
    state = StateManager(codemap_path / "state.json")
    detector = ChangeDetector(config, state)
    
    changed_files = detector.get_changed_files()
    
    if not changed_files:
        click.echo("✓ Code map is up-to-date")
    else:
        click.echo(f"✗ {len(changed_files)} file(s) have changed since last update:")
        for f in changed_files[:10]:
            click.echo(f"  - {f}")
        if len(changed_files) > 10:
            click.echo(f"  ... and {len(changed_files) - 10} more")
        click.echo()
        click.echo("Run 'llmap update' to regenerate.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
