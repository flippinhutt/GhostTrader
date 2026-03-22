# Changelog

## [1.1.0] - 2026-03-22

### Added
- Configurable polling interval via `POLL_INTERVAL_SECONDS` environment variable.
- Configurable market scan limit via `MARKET_SCAN_LIMIT` environment variable.
- Project-wide documentation overhaul including API reference and architecture updates.

### Changed
- Improved market scanning logic to use `<=` for profit thresholds, increasing trade frequency.
- Reduced default polling interval from 10 seconds to 3 seconds for more aggressive arbitrage capture.
- Increased default market scan limit from 50 to 100.
- Cleaned up unused local variables and formatted code with `ruff`.

### Fixed
- Issue where bot would not execute trades due to overly strict mathematical constraints.
