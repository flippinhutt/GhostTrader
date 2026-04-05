import logging
import os
from typing import List, Dict
from src.kalshi_client import KalshiClient

logger = logging.getLogger(__name__)


class Scanner:
    """Scans Kalshi prediction markets for pricing inefficiencies (Arbitrage)."""

    def __init__(self, client: KalshiClient):
        """Initializes the Scanner with a Kalshi client.

        Args:
            client (KalshiClient): The client used for API communication.
        """
        self.client = client

    async def scan_for_inefficiencies(self) -> List[Dict]:
        """Scans active markets for arbitrage opportunities.

        Fetches a larger pool, filters to liquid markets (volume > 0),
        then sorts by volume descending so the most active markets are inspected first.

        Returns:
            list[dict]: A list of dictionary objects representing discovered inefficiencies.
        """
        inefficiencies = []
        scan_limit = int(os.getenv("MARKET_SCAN_LIMIT", "100"))
        # Fetch 3x the limit to ensure we get enough liquid markets after filtering
        fetch_limit = min(scan_limit * 3, 1000)
        try:
            all_markets = self.client.get_markets(limit=fetch_limit)

            # Filter to markets with active volume — these have live bids
            liquid = [m for m in all_markets if m.volume and float(str(m.volume).split("#")[0].strip()) > 0]

            # Sort by volume descending (most liquid first)
            try:
                liquid.sort(key=lambda m: float(str(m.volume).split("#")[0].strip()), reverse=True)
            except Exception:
                pass  # If sort fails, use the natural order

            markets = liquid[:scan_limit]
            logger.info(
                f"Fetched {len(all_markets)} markets, {len(liquid)} liquid, scanning top {len(markets)}."
            )

            for i, market in enumerate(markets):
                if i > 0 and i % 10 == 0:
                    logger.info(f"Progress: Scanned {i}/{len(markets)} markets...")

                inefficiency = await self._analyze_kalshi_market(market)
                if inefficiency:
                    inefficiencies.append(inefficiency)

            logger.info(f"Scan complete. Found {len(inefficiencies)} opportunities.")

        except Exception as e:
            logger.error(f"Error during scan: {e}")

        return inefficiencies

    async def _analyze_kalshi_market(self, market) -> Dict | None:
        """Analyze a Kalshi market for pricing inefficiencies (Arbitrage).

        Arbitrage occurs when the sum of the best Bids across both sides is > 100¢.
        For example: YES best bid = 60¢, NO best bid = 55¢. Total Bids = 115¢.
        Implied YES Ask = 45¢, Implied NO Ask = 40¢. Total Cost = 85¢ (Profit = 15¢).

        Args:
            market: The Kalshi market object.

        Returns:
            Optional[dict]: Inefficiency data if an arbitrage opportunity is found, 
                else None.
        """
        ticker = market.ticker
        book = self.client.get_order_book(ticker)

        if not book:
            return None

        try:
            # Kalshi prices are 1-99 (cents)
            # BEST BID is the last element ([-1]) in the list
            yes_bid = book.yes[-1].price if book.yes else None
            no_bid = book.no[-1].price if book.no else None

            if not yes_bid or not no_bid:
                return None

            # Implied asks (cost to buy)
            implied_yes_ask = 100 - no_bid
            implied_no_ask = 100 - yes_bid
            total_cost_cents = implied_yes_ask + implied_no_ask

            # Price logging for diagnostics
            if total_cost_cents < 110: # Log if it's somewhat close to an arb
                logger.info(f"Inspecting {ticker}: Bids(Y={yes_bid}c, N={no_bid}c) | Implied Costs(Y={implied_yes_ask}c, N={implied_no_ask}c) | Total Cost={total_cost_cents}c")

            min_profit_threshold = float(os.getenv("MIN_PROFIT_USD", "0.01"))
            profit_per_share = (100 - total_cost_cents) / 100.0

            if total_cost_cents <= (100 - (min_profit_threshold * 100)):
                logger.warning(
                    f"INERTIA (Kalshi): Profitable market found: {ticker} | Total Cost: {total_cost_cents}c | Profit: ${profit_per_share:.4f}/share"
                )
                return {
                    "source": "kalshi",
                    "ticker": ticker,
                    "question": market.title,
                    "total_price": total_cost_cents / 100.0, # Total unit cost
                    "best_asks": [implied_yes_ask, implied_no_ask],
                }
        except (AttributeError, IndexError):
            pass

        return None
