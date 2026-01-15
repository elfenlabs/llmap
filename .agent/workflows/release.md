---
description: How to release a new version of llmap
---

# Release Workflow

## Pre-release Checklist

1. Ensure all tests pass:
   ```bash
   pytest
   ```

2. Update version in `pyproject.toml`:
   ```toml
   version = "X.Y.Z"
   ```

3. Update `CHANGELOG.md`:
   - Move items from `[Unreleased]` to new version section
   - Add release date: `## [X.Y.Z] - YYYY-MM-DD`
   - Update comparison links at bottom

4. Commit version bump:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: release vX.Y.Z"
   ```

## Creating the Release

// turbo
5. Create and push a git tag:
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

6. Create GitHub release:
   ```bash
   gh release create vX.Y.Z --title "vX.Y.Z" --notes-from-tag
   ```
   Or use `--generate-notes` for auto-generated release notes.

## Publishing to PyPI

7. Build the package:
   ```bash
   python -m build
   ```

8. Upload to PyPI:
   ```bash
   twine upload dist/*
   ```

## Version Numbering

- **MAJOR** (X): Breaking changes to CLI or config format
- **MINOR** (Y): New features, new language support
- **PATCH** (Z): Bug fixes, documentation updates

## Example Release

```bash
# After updating pyproject.toml to 0.2.0 and CHANGELOG.md
git add pyproject.toml CHANGELOG.md
git commit -m "chore: release v0.2.0"
git tag v0.2.0
git push origin main --tags
gh release create v0.2.0 --title "v0.2.0" --generate-notes
python -m build
twine upload dist/*
```
