import asyncio
import logging
import os
from typing import List, Dict, Union
from src.client import PolymarketClient
from src.kalshi_client import KalshiClient

logger = logging.getLogger(__name__)

class Scanner:
    """Scans prediction markets for pricing inefficiencies (Arbitrage).
    
    Supports both Polymarket (EIP-712) and Kalshi (US Regulated).
    """
    
    def __init__(self, client: Union[PolymarketClient, KalshiClient]):
        """Initializes the Scanner with a market client.
        
        Args:
            client (Union[PolymarketClient, KalshiClient]): The client used for API communication.
        """
        self.client = client
        self.is_kalshi = isinstance(client, KalshiClient)

    async def scan_for_inefficiencies(self) -> List[Dict]:
        """Scans the top active markets for arbitrage opportunities.
        
        Returns:
            list[dict]: A list of dictionary objects representing discovered inefficiencies.
        """
        inefficiencies = []
        try:
            if self.is_kalshi:
                markets = self.client.get_markets(limit=50)
            else:
                markets = await self.client.get_markets(limit=50)

            for market in markets:
                if self.is_kalshi:
                    # In Kalshi v2, the market object structure differs
                    ticker = market.ticker
                    inefficiency = await self._analyze_kalshi_market(market)
                else:
                    tokens = market.get("clob_token_ids")
                    if not tokens or len(tokens) != 2:
                        continue
                    inefficiency = await self._analyze_poly_market(market, tokens)
                
                if inefficiency:
                    inefficiencies.append(inefficiency)
                    
        except Exception as e:
            logger.error(f"Error during scan: {e}")
            
        return inefficiencies

    async def _analyze_poly_market(self, market: Dict, tokens: List[str]) -> Dict:
        """Analyzes a Polymarket for Unity constraint violations."""
        tasks = [self.client.get_order_book(tid) for tid in tokens]
        books = await asyncio.gather(*tasks)
        
        if not all(books):
            return None

        try:
            best_asks = []
            for book in books:
                asks = book.get("asks", [])
                if not asks:
                    return None
                best_asks.append(float(asks[0]["price"]))
            
            total_price = sum(best_asks)
            min_profit_threshold = float(os.getenv("MIN_PROFIT_USD", "0.01"))
            
            if total_price < (1.0 - min_profit_threshold):
                logger.warning(f"INERTIA (Poly): Profitable market found: {market['question']} | Total: ${total_price:.4f}")
                return {
                    "source": "polymarket",
                    "market_id": market["id"],
                    "question": market["question"],
                    "total_price": total_price,
                    "tokens": tokens,
                    "best_asks": best_asks
                }
        except (ValueError, KeyError, IndexError):
            pass
            
        return None

    async def _analyze_kalshi_market(self, market) -> Dict:
        """Analyzes a Kalshi market for arbitrage.
        
        Kalshi usually enforces YES + NO = 100 on the same contract, but cross-market
        or momentary inconsistencies can still exist.
        """
        ticker = market.ticker
        book = self.client.get_order_book(ticker)
        
        if not book:
            return None

        try:
            # Kalshi prices are 1-99 (cents)
            yes_ask = book.yes[0].price if book.yes else None
            no_ask = book.no[0].price if book.no else None
            
            if not yes_ask or not no_ask:
                return None
            
            # Convert to 0-1.0 scale
            total_price = (yes_ask + no_ask) / 100.0
            min_profit_threshold = float(os.getenv("MIN_PROFIT_USD", "0.01"))

            if total_price < (1.0 - min_profit_threshold):
                logger.warning(f"INERTIA (Kalshi): Profitable market found: {ticker} | Total: ${total_price:.4f}")
                return {
                    "source": "kalshi",
                    "ticker": ticker,
                    "question": market.title,
                    "total_price": total_price,
                    "best_asks": [yes_ask, no_ask]
                }
        except (AttributeError, IndexError):
            pass
        
        return None
