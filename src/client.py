import httpx
import logging
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON
from py_clob_client.clob_types import OrderArgs

logger = logging.getLogger(__name__)


class PolymarketClient:
    """Wrapper for Polymarket Gamma API and official CLOB SDK.

    This client provides high-level methods for discovering markets via the Gamma API
    and placing/managing orders via the Central Limit Order Book (CLOB) SDK.
    """

    GAMMA_URL = "https://gamma-api.polymarket.com"

    def __init__(
        self,
        private_key: str = None,
        api_key: str = None,
        secret: str = None,
        passphrase: str = None,
    ):
        """Initializes the PolymarketClient.

        Args:
            private_key (str, optional): The Polygon wallet private key for signing orders.
            api_key (str, optional): The CLOB API key.
            secret (str, optional): The CLOB API secret.
            passphrase (str, optional): The CLOB API passphrase.
        """
        self.client = httpx.AsyncClient(timeout=10.0)
        self.clob_client = None

        if all([private_key, api_key, secret, passphrase]):
            self.clob_client = ClobClient(
                host="https://clob.polymarket.com",
                key=api_key,
                secret=secret,
                passphrase=passphrase,
                private_key=private_key,
                chain_id=POLYGON,
            )
            logger.info("Authenticated CLOB client initialized.")
        else:
            logger.warning(
                "CLOB client initialized without authentication (Read-only)."
            )

    def get_balance(self) -> float:
        """Fetch the current wallet USDC balance (mocked or fetched via SDK)."""
        if not self.clob_client:
            return 0.0
        try:
            # Poly CLOB SDK doesn't have a direct 'get_total_usdc' but get_balance_allowance
            # often provides some context, or we can use the private key to check on-chain.
            # For now, we'll try to fetch from the CLOB profile if possible.
            resp = self.clob_client.get_balance_allowance()
            # Standard USDC balance is often part of the return or can be inferred.
            # If not directly available, we'll return a placeholder or fetch via RPC.
            return float(resp.get("balance", 0.0))
        except Exception:
            return 0.0

    async def get_markets(self, limit: int = 100, active: bool = True):
        """Fetch active markets from the Gamma API.

        Args:
            limit (int): Maximum number of markets to return. Defaults to 100.
            active (bool): Whether to only fetch active markets. Defaults to True.

        Returns:
            list[dict]: A list of market objects from the Gamma API.
        """
        params = {"limit": limit, "active": str(active).lower()}
        response = await self.client.get(f"{self.GAMMA_URL}/markets", params=params)
        response.raise_for_status()
        return response.json()

    async def get_order_book(self, token_id: str):
        """Fetch the order book for a specific token from the CLOB API.

        Args:
            token_id (str): The unique identifier for the token.

        Returns:
            dict or None: The order book object, or None if the token is not found.
        """
        # Use the CLOB SDK for order book if available, else fallback to direct public endpoint
        if self.clob_client:
            return self.clob_client.get_order_book(token_id)

        # Public fallback
        response = await self.client.get(
            "https://clob.polymarket.com/book", params={"token_id": token_id}
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def post_order(self, order_args: OrderArgs):
        """Place an order via the authenticated CLOB client.

        Args:
            order_args (OrderArgs): The order parameters including price, size, and side.

        Returns:
            dict: The response from the CLOB API after placing the order.

        Raises:
            ValueError: If the client is not authenticated.
        """
        if not self.clob_client:
            raise ValueError("Client must be authenticated to post orders.")
        return self.clob_client.create_order(order_args)

    async def close(self):
        """Closes the underlying HTTP client."""
        await self.client.aclose()
