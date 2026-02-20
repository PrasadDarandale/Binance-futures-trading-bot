

import hashlib
import hmac
import time
import urllib.parse
from typing import Any, Optional

import requests

from .logging_config import get_logger

logger = get_logger(__name__)

BASE_URL = "https://testnet.binancefuture.com"
RECV_WINDOW = 5000  # milliseconds


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error payload."""

    def __init__(self, code: int, msg: str, status_code: int = 0):
        self.code = code
        self.msg = msg
        self.status_code = status_code
        super().__init__(f"Binance API error {code}: {msg}")


class BinanceClient:
    """
    Thin wrapper around the Binance Futures Testnet REST API.

    Responsibilities
    ----------------
    - Sign every private request with HMAC-SHA256
    - Attach required headers (X-MBX-APIKEY)
    - Retry on transient network failures (up to `max_retries` times)
    - Log every outgoing request and incoming response at DEBUG level
    - Raise BinanceAPIError for non-OK API responses
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = BASE_URL,
        timeout: int = 10,
        max_retries: int = 3,
    ):
        if not api_key or not api_secret:
            raise ValueError("API key and secret must not be empty.")

        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.info("BinanceClient initialised → base_url=%s", self.base_url)

   

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _sign(self, params: dict) -> str:
        """Return HMAC-SHA256 hex signature for the given query/body params."""
        query_string = urllib.parse.urlencode(params)
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()  

    def _build_signed_params(self, params: dict) -> dict:
        params["timestamp"] = self._timestamp()
        params["recvWindow"] = RECV_WINDOW
        params["signature"] = self._sign(params)
        return params

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        signed: bool = False,
    ) -> Any:
        """
        Execute an HTTP request with retry logic.

        Parameters
        ----------
        method   : HTTP method (GET / POST / DELETE)
        endpoint : API path, e.g. '/fapi/v1/order'
        params   : Query / body parameters
        signed   : Whether to attach timestamp + signature
        """
        url = f"{self.base_url}{endpoint}"
        params = params or {}

        if signed:
            params = self._build_signed_params(params)

        logger.debug(
            "→ %s %s  params=%s",
            method.upper(),
            endpoint,
            {k: v for k, v in params.items() if k != "signature"},
        )

        last_exception: Exception = RuntimeError("No attempts made.")

        for attempt in range(1, self.max_retries + 1):
            try:
                if method.upper() in ("GET", "DELETE"):
                    response = self._session.request(
                        method, url, params=params, timeout=self.timeout
                    )
                else:
                    response = self._session.request(
                        method, url, data=params, timeout=self.timeout
                    )

                logger.debug(
                    "← %s %s  status=%d  body=%s",
                    method.upper(),
                    endpoint,
                    response.status_code,
                    response.text[:500],
                )

                data = response.json()

               
                if isinstance(data, dict) and "code" in data and data["code"] != 200:
                    raise BinanceAPIError(
                        code=data.get("code", -1),
                        msg=data.get("msg", "Unknown error"),
                        status_code=response.status_code,
                    )

                return data

            except BinanceAPIError:
                raise  

            except requests.exceptions.Timeout as exc:
                last_exception = exc
                logger.warning(
                    "Request timed out (attempt %d/%d): %s %s",
                    attempt, self.max_retries, method, endpoint,
                )

            except requests.exceptions.ConnectionError as exc:
                last_exception = exc
                logger.warning(
                    "Connection error (attempt %d/%d): %s %s → %s",
                    attempt, self.max_retries, method, endpoint, exc,
                )

            except requests.exceptions.RequestException as exc:
                last_exception = exc
                logger.warning(
                    "Request error (attempt %d/%d): %s %s → %s",
                    attempt, self.max_retries, method, endpoint, exc,
                )

            if attempt < self.max_retries:
                wait = 2 ** (attempt - 1) 
                logger.info("Retrying in %ds…", wait)
                time.sleep(wait)

        raise ConnectionError(
            f"Failed to reach {url} after {self.max_retries} attempts. "
            f"Last error: {last_exception}"
        ) from last_exception



    def ping(self) -> bool:
        """Return True if the testnet is reachable."""
        try:
            self._request("GET", "/fapi/v1/ping")
            logger.info("Ping successful — testnet is reachable.")
            return True
        except Exception as exc:
            logger.error("Ping failed: %s", exc)
            return False

    def get_exchange_info(self) -> dict:
        """Fetch exchange metadata (symbol info, filters, etc.)."""
        return self._request("GET", "/fapi/v1/exchangeInfo")

    def get_account(self) -> dict:
        """Fetch account information (balances, positions)."""
        return self._request("GET", "/fapi/v2/account", signed=True)

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str,
        price: Optional[str] = None,
        time_in_force: Optional[str] = None,
        stop_price: Optional[str] = None,
        reduce_only: bool = False,
        position_side: str = "BOTH",
    ) -> dict:
        """
        Place a new order on Binance Futures Testnet.

        Parameters
        ----------
        symbol        : Trading pair, e.g. 'BTCUSDT'
        side          : 'BUY' or 'SELL'
        order_type    : 'MARKET', 'LIMIT', or 'STOP_MARKET'
        quantity      : Order quantity as string
        price         : Required for LIMIT orders
        time_in_force : e.g. 'GTC', 'IOC', 'FOK' (required for LIMIT)
        stop_price    : Required for STOP_MARKET orders
        reduce_only   : Whether the order should only reduce an existing position
        position_side : 'BOTH' (default), 'LONG', or 'SHORT'
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "positionSide": position_side,
        }

        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = time_in_force or "GTC"

        if order_type == "STOP_MARKET":
            params["stopPrice"] = stop_price

        if reduce_only:
            params["reduceOnly"] = "true"

        logger.info(
            "Placing order → symbol=%s side=%s type=%s qty=%s price=%s",
            symbol, side, order_type, quantity, price or stop_price or "N/A",
        )

        response = self._request("POST", "/fapi/v1/order", params=params, signed=True)
        logger.info("Order placed successfully → orderId=%s", response.get("orderId"))
        return response

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """Cancel an open order by orderId."""
        params = {"symbol": symbol, "orderId": order_id}
        logger.info("Cancelling order → symbol=%s orderId=%s", symbol, order_id)
        response = self._request("DELETE", "/fapi/v1/order", params=params, signed=True)
        logger.info("Order cancelled → orderId=%s status=%s", order_id, response.get("status"))
        return response

    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        """List all open orders, optionally filtered by symbol."""
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request("GET", "/fapi/v1/openOrders", params=params, signed=True)

    def get_order(self, symbol: str, order_id: int) -> dict:
        """Query a specific order by orderId."""
        params = {"symbol": symbol, "orderId": order_id}
        return self._request("GET", "/fapi/v1/order", params=params, signed=True)
