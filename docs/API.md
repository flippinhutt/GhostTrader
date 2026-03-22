# Technical Reference: Trader Bot API

Detailed reference for the core modules and classes within the Trader project.

## `src/client.py` - `PolymarketClient`

The primary interface for all Polymarket communication.

### Methods

| Method | Parameters | Returns | Description |
| :--- | :--- | :--- | :--- |
| `get_markets` | `limit: int`, `active: bool` | `list[dict]` | Fetches active markets from Gamma API. |
| `get_order_book` | `token_id: str` | `dict` or `None` | Fetches order book for a specific token ID. |
| `post_order` | `order_args: OrderArgs` | `dict` | Places a live order via CLOB SDK. |
| `get_balance` | None | `float` | Fetches wallet USDC balance. |

---

## `src/kalshi_client.py` - `KalshiClient`

The primary interface for all Kalshi communication (v2 RSA-signed API).

### Methods

| Method | Parameters | Returns | Description |
| :--- | :--- | :--- | :--- |
| `get_markets` | `limit: int`, `status: str` | `list[dict]` | Fetches active markets from Kalshi v2. |
| `get_order_book` | `ticker: str` | `dict` or `None` | Fetches order book for a specific ticker. |
| `post_order` | `ticker, side, action, count, price` | `dict` | Places a limit order on Kalshi. |
| `get_balance` | None | `float` | Fetches account USD balance (dollars). |

---

## `src/scanner.py` - `Scanner`

Logic for monitoring markets and detecting opportunities.

### Methods

| Method | Parameters | Returns | Description |
| :--- | :--- | :--- | :--- |
| `scan_for_inefficiencies` | None | `list[dict]` | Scans top markets for arbitrage signals. |
| `_analyze_market` | `market: dict`, `tokens: list[str]` | `dict` or `None` | Analyzes Unity constraint for a specific market. |

---

## `src/engine.py` - `Engine`

Trade coordination and risk management.

### Methods

| Method | Parameters | Returns | Description |
| :--- | :--- | :--- | :--- |
| `execute_trade` | `signal: dict` | None | Processes and executes a trade signal. |

---

## Configuration Settings (Environment)

- `KALSHI_API_KEY_ID`: Your Kalshi API Key ID (UUID).
- `KALSHI_PRIVATE_KEY_PATH`: Absolute path to your `.pem` private key.
- `KALSHI_ENVIRONMENT`: Either `demo` or `prod`.
- `POLYGON_PRIVATE_KEY`: Private key for EIP-712 signing.
- `CLOB_API_KEY`: Polymarket API public key.
- `LIVE_MODE`: Boolean toggle for real trades.
- `TRADE_LIMIT_USD`: Cap on USD investment per trade.
- `MIN_PROFIT_USD`: Minimum profit per share required.
- `SLIPPAGE_TOLERANCE`: Max slippage for orders (0.01 = 1%).
- `MARKET_SCAN_LIMIT`: Maximum number of markets to scan per iteration (~100-250 suggested).
- `POLL_INTERVAL_SECONDS`: Idle wait time between scan loops (~2-4s suggested).
