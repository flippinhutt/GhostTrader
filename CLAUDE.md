# CLAUDE.md: GhostTrades Bot

## Overview
A multi-market trading bot developed with Python to scan Polymarket and Kalshi for pricing inefficiencies (Unity Arbitrage).

## Tech Stack
- **Languages**: Python 3.12+
- **Containerization**: Docker & Docker Compose
- **SDKs**: `kalshi-python` (v2), `py-clob-client` (Polymarket)
- **Data Validation**: `pydantic`
- **Frameworks**: `asyncio`
- **Testing**: `pytest`

## Repository Layout
- `src/`: Core logic (scanner, engine, etc.)
- `docs/`: Architecture documents and ADRs.
- `.claude/`: Claude-specific skills and settings.
- `tools/`: Utility scripts and prompts.

## Coding Conventions
- **Async First**: Use `asyncio` for all I/O bound operations.
- **Type Safety**: Prefer `pydantic` for data validation and `typing` for function signatures.
- **TDD**: Write tests for scanner logic (efficiency detection).
- **Security**: Never hardcode secrets; use environment variables.

## References
- [architecture.md](file:///Users/ryanhutto/projects/Trader/docs/architecture.md)
- [decisions/](file:///Users/ryanhutto/projects/Trader/docs/decisions/)
