import os
import sys
import logging
import asyncio
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.getcwd())

from src.kalshi_client import KalshiClient
from src.scanner import Scanner
from src.engine import Engine

logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("VERIFIER")

load_dotenv(override=True)

async def verify():
    key_id = os.getenv("KALSHI_API_KEY_ID")
    private_key_path = os.getenv("KALSHI_PRIVATE_KEY_PATH")
    env = os.getenv("KALSHI_ENVIRONMENT", "demo")
    
    logger.info(f"Connecting to Kalshi {env}...")
    try:
        client = KalshiClient(key_id=key_id, private_key_path=private_key_path, environment=env)
        
        balance = client.get_balance()
        logger.info(f"Verified Balance: ${balance:.2f}")
        
        # We'll run in DRY-RUN mode for verification
        os.environ["LIVE_MODE"] = "false"
        engine = Engine(client, balance=balance)
        scanner = Scanner(client)
        
        logger.info("Starting ONE-TIME SCAN for verification...")
        # Scan only a few markets for speed
        os.environ["MARKET_SCAN_LIMIT"] = "10" 
        inefficiencies = await scanner.scan_for_inefficiencies()
        
        if not inefficiencies:
            logger.info("No arbitrage opportunities found in these markets (expected).")
            logger.info("Manual check: Finding an active liquid market to verify sorting...")
            all_markets = client.get_markets(limit=200)
            # Filter to liquid markets only
            liquid = [m for m in all_markets if m.volume and float(str(m.volume).split("#")[0].strip()) > 0]
            liquid.sort(key=lambda m: float(str(m.volume).split("#")[0].strip()), reverse=True)
            logger.info(f"Found {len(liquid)} liquid markets (out of {len(all_markets)} fetched).")
            markets = liquid
            found_active = False
            for m in markets:
                book = client.get_order_book(m.ticker)
                if book and book.yes and book.no:
                    logger.info(f"Targeting {m.ticker} ({m.title})...")
                    logger.info(f"Book structure: yes_len={len(book.yes)}, no_len={len(book.no)}")
                    # Verify indices
                    worst_yes = book.yes[0].price
                    best_yes = book.yes[-1].price
                    worst_no = book.no[0].price
                    best_no = book.no[-1].price
                    logger.info(f"YES Bids: Lowest={worst_yes}c, Highest(Best)={best_yes}c")
                    logger.info(f"NO Bids: Lowest={worst_no}c, Highest(Best)={best_no}c")
                    
                    # Verify logic
                    sum_best_bids = best_yes + best_no
                    total_cost = (100 - best_yes) + (100 - best_no)
                    logger.info(f"Sum of Best Bids: {sum_best_bids}c")
                    logger.info(f"Implied Total Cost: {total_cost}c (Arbitrage if < 100c)")
                    
                    if sum_best_bids > 100:
                        logger.warning("!!! ARBITRAGE OPPORTUNITY CONFIRMED BY LOGIC !!!")
                    else:
                        logger.info("Market is currently efficient (no arb).")
                    found_active = True
                    break
            if not found_active:
                logger.warning("Could not find any active markets with both YES and NO bids.")
        else:
            logger.info(f"Discovered {len(inefficiencies)} opportunities! Processing first one in Dry-Run...")
            await engine.execute_trade(inefficiencies[0])

    except Exception as e:
        logger.error(f"Verification failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
