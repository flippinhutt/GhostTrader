import asyncio
import logging
import os
import inspect
from dotenv import load_dotenv
from src.client import PolymarketClient
from src.kalshi_client import KalshiClient
from src.scanner import Scanner
from src.engine import Engine

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def main():
    logger.info("Initializing Trader Bot (MULTI-MARKET FRAMEWORK)...")
    
    # Preference: Choose Kalshi for US-regulated trading if credentials exist
    if os.getenv("KALSHI_API_KEY_ID"):
        logger.info("Using Kalshi Client (v2 API Key)...")
        client = KalshiClient(
            key_id=os.getenv("KALSHI_API_KEY_ID"),
            private_key_path=os.getenv("KALSHI_PRIVATE_KEY_PATH"),
            environment=os.getenv("KALSHI_ENVIRONMENT", "demo")
        )
    else:
        logger.info("Using Polymarket Client...")
        client = PolymarketClient(
            private_key=os.getenv("POLYGON_PRIVATE_KEY"),
            api_key=os.getenv("CLOB_API_KEY"),
            secret=os.getenv("CLOB_SECRET"),
            passphrase=os.getenv("CLOB_PASSPHRASE")
        )
    
    scanner = Scanner(client)
    
    # Fetch actual balance for the engine
    logger.info("Fetching account balance...")
    try:
        # Polymarket client methods are mostly async, but get_balance is sync for now
        # We check if it's a coroutine just in case of future SDK changes
        if inspect.iscoroutinefunction(client.get_balance):
            actual_balance = await client.get_balance()
        else:
            actual_balance = client.get_balance()
        logger.info(f"Verified Balance: ${actual_balance:.2f}")
    except Exception as e:
        logger.warning(f"Could not fetch live balance ({e}). Using default.")
        actual_balance = 1400.0
        
    engine = Engine(client, balance=actual_balance)
    
    try:
        if os.getenv("LIVE_MODE") == "true":
            logger.warning("!!! BOT IS RUNNING IN LIVE MODE !!!")
        
        while True:
            logger.info("Scanning for inefficiencies...")
            inefficiencies = await scanner.scan_for_inefficiencies()
            
            for item in inefficiencies:
                await engine.execute_trade(item)
            
            logger.info(f"Status: {engine.trades_executed} trades | Balance: ${engine.balance:.2f}")
            await asyncio.sleep(10)
    finally:
        client.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Trader Bot stopping...")
