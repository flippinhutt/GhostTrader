import logging
import kalshi_python
from kalshi_python.api import markets_api, exchange_api, portfolio_api
from kalshi_python.models import create_order_request

logger = logging.getLogger(__name__)


class KalshiClient:
    """Wrapper for the official Kalshi v2 API using RSA Key signatures."""

    def __init__(
        self,
        key_id: str = None,
        private_key_path: str = None,
        environment: str = "demo",
    ):
        """Initializes the KalshiClient.

        Args:
            key_id (str): Kalshi API Key ID (UUID).
            private_key_path (str): Path to the RSA private key (.pem).
            environment (str): 'demo' or 'prod'. Defaults to 'demo'.
        """
        # Robust handling of environment string (strip comments/whitespace)
        env = str(environment).split("#")[0].strip().lower()
        if env == "demo":
            host = "https://demo-api.kalshi.co/trade-api/v2"
        else:
            host = "https://api.elections.kalshi.com/trade-api/v2"

        configuration = kalshi_python.Configuration(host=host)
        self.api_client = kalshi_python.ApiClient(configuration)

        if key_id and private_key_path:
            # v2 uses RSA signing via set_kalshi_auth
            self.api_client.set_kalshi_auth(key_id, private_key_path)
            logger.info("Successfully configured Kalshi RSA authentication.")

        self.markets_api = markets_api.MarketsApi(self.api_client)
        self.exchange_api = exchange_api.ExchangeApi(self.api_client)
        self.portfolio_api = portfolio_api.PortfolioApi(self.api_client)

    def get_balance(self) -> float:
        """Fetch the current account balance in USD (cents converted to dollars)."""
        try:
            response = self.portfolio_api.get_balance()
            # Kalshi returns balance in cents
            return float(response.balance) / 100.0
        except Exception as e:
            logger.error(f"Error fetching Kalshi balance: {e}")
            return 0.0

    def get_markets(self, limit: int = 100, status: str = "open"):
        """Fetch markets from Kalshi."""
        try:
            response = self.markets_api.get_markets(limit=limit, status=status)
            return response.markets
        except Exception as e:
            logger.error(f"Error fetching Kalshi markets: {e}")
            return []

    def get_order_book(self, ticker: str):
        """Fetch order book for a specific Kalshi ticker."""
        try:
            response = self.markets_api.get_market_orderbook(ticker)
            return response.orderbook
        except Exception as e:
            logger.debug(f"Order book not found for ticker {ticker}: {e}")
            return None

    def post_order(self, ticker: str, side: str, action: str, count: int, price: int):
        """Place an order on Kalshi."""
        try:
            body = create_order_request.CreateOrderRequest(
                ticker=ticker,
                action=action,
                type="limit",
                side=side,
                count=count,
                yes_price=price if side == "yes" else (100 - price),
            )
            return self.exchange_api.create_order(body)
        except Exception as e:
            logger.error(f"Failed to place Kalshi order: {e}")
            raise

    def close(self):
        """Close the API client."""
        pass
