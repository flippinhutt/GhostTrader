---
name: code-review
description: Comprehensive security and quality review for the Trader bot.
---

## Scope
Review changes to `src/scanner.py`, `src/engine.py`, and `src/client.py`.

## Process
1.  **Security**: Check for hardcoded API keys and credentials.
2.  **Concurrency**: Ensure `asyncio` patterns are followed and no blocking calls exist.
3.  **Efficiency**: Verify that inefficiency detection logic is accurate and efficient.
4.  **Error Handling**: Check for robust error handling in API interactions.

## Output Format
- Summary of changes.
- Key findings (Security, Performance, Code Quality).
- Recommended fixes.
