---
description: start work on a GitHub issue by creating a worktree and branch
---

# Work on GitHub Issue

Start work on an issue by creating a dedicated worktree and branch, using the issue's checklist for progress tracking.

## Steps

1. Fetch issue details with `gh issue view <number>`. Look for a checklist in the issue body—this guides implementation.

2. Create a new branch and worktree:
```bash
git worktree add .worktrees/gh-issue-<number> -b issue-<number>
```

3. Initialize submodules in the worktree if any:
```bash
cd .worktrees/gh-issue-<number> && git submodule update --init --recursive
``

5. Work on the issue in `.worktrees/gh-issue-<number>`, following the checklist items in order.

6. **Update checklist progress** as you complete items. Add a comment to the issue:
```bash
gh issue comment <number> --body "Completed: <checklist item description>"
```

7. When ready, create a PR:
```bash
gh pr create --title "<title>" --body "Fixes #<number>"
```

8. After PR is merged, clean up:
```bash
git worktree remove --force .worktrees/gh-issue-<number>
```

## Issue Checklist Format

When creating issues, include an implementation checklist:

```markdown
## Implementation Checklist
- [ ] Step 1: Description
- [ ] Step 2: Description
- [ ] Step 3: Description

## Verification
- [ ] All tests pass
- [ ] No regressions
```

The agent will read the checklist to understand what needs to be done and update progress via comments.