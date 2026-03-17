---
name: release
description: Release new versions of the Trader bot.
---

## Scope
Deployment and versioning for the bot.

## Process
1.  **Versioning**: Bump version in `package.json` (if applicable) or `src/__init__.py`.
2.  **Changelog**: Update `CHANGELOG.md`.
3.  **Tagging**: Create a git tag for the release.
4.  **Deploy**: Push changes to the production branch.

## Output Format
- Tag name and version.
- Highlights of the release.
- Deployment status.
