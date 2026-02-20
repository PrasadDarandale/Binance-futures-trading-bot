"""
Order placement business logic.

This module sits between the CLI layer and the BinanceClient.
It validates inputs, delegates to the client, and formats results.
"""

from decimal import Decimal
from typing import Optional

from .client import BinanceClient, BinanceAPIError
from .validators import validate_all
from .logging_config import get_logger

logger = get_logger(__name__)




def _format_order_response(response: dict) -> dict:
    """Extract and normalise the fields we care about from any order response."""
    return {
        "orderId":      response.get("orderId", "N/A"),
        "symbol":       response.get("symbol", "N/A"),
        "side":         response.get("side", "N/A"),
        "type":         response.get("type", "N/A"),
        "status":       response.get("status", "N/A"),
        "price":        response.get("price", "0"),
        "avgPrice":     response.get("avgPrice", "0"),
        "origQty":      response.get("origQty", "0"),
        "executedQty":  response.get("executedQty", "0"),
        "timeInForce":  response.get("timeInForce", "N/A"),
        "updateTime":   response.get("updateTime", "N/A"),
    }


def _print_order_summary(params: dict) -> None:
    """Print a human-readable order request summary to stdout."""
    print("\n" + "═" * 55)
    print("  ORDER REQUEST SUMMARY")
    print("═" * 55)
    print(f"  Symbol      : {params['symbol']}")
    print(f"  Side        : {params['side']}")
    print(f"  Type        : {params['order_type']}")
    print(f"  Quantity    : {params['quantity']}")
    if params.get("price"):
        label = "Stop Price" if params["order_type"] == "STOP_MARKET" else "Price"
        print(f"  {label:<12}: {params['price']}")
    print("═" * 55 + "\n")


def _print_order_result(result: dict, success: bool = True) -> None:
    """Print a human-readable order response to stdout."""
    print("─" * 55)
    print("  ORDER RESPONSE")
    print("─" * 55)
    print(f"  Status       : {'SUCCESS' if success else 'FAILED'}")
    print(f"  Order ID     : {result.get('orderId', 'N/A')}")
    print(f"  Symbol       : {result.get('symbol', 'N/A')}")
    print(f"  Side         : {result.get('side', 'N/A')}")
    print(f"  Type         : {result.get('type', 'N/A')}")
    print(f"  Order Status : {result.get('status', 'N/A')}")
    print(f"  Orig Qty     : {result.get('origQty', 'N/A')}")
    print(f"  Executed Qty : {result.get('executedQty', 'N/A')}")

    avg = result.get("avgPrice", "0")
    if avg and float(avg) > 0:
        print(f"  Avg Price    : {avg}")

    lmt = result.get("price", "0")
    if lmt and float(lmt) > 0:
        print(f"  Limit Price  : {lmt}")

    print("─" * 55 + "\n")



def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: Optional[str | float] = None,
    time_in_force: str = "GTC",
    reduce_only: bool = False,
) -> dict:
    """
    Validate inputs, place an order, and return the formatted response.

    Parameters
    ----------
    client        : Authenticated BinanceClient instance
    symbol        : e.g. 'BTCUSDT'
    side          : 'BUY' | 'SELL'
    order_type    : 'MARKET' | 'LIMIT' | 'STOP_MARKET'
    quantity      : Order size
    price         : Limit price (LIMIT) or stop price (STOP_MARKET)
    time_in_force : 'GTC' | 'IOC' | 'FOK' (LIMIT orders only)
    reduce_only   : Reduce-only flag

    Returns
    -------
    dict with formatted order response fields.

    Raises
    ------
    ValueError        – on invalid user inputs
    BinanceAPIError   – on API-level errors
    ConnectionError   – on network failures
    """


    logger.debug(
        "Validating inputs: symbol=%s side=%s type=%s qty=%s price=%s",
        symbol, side, order_type, quantity, price,
    )
    validated = validate_all(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
    )

    v_symbol     = validated["symbol"]
    v_side       = validated["side"]
    v_type       = validated["order_type"]
    v_quantity   = validated["quantity"]
    v_price: Optional[Decimal] = validated["price"]


    _print_order_summary({
        "symbol": v_symbol,
        "side": v_side,
        "order_type": v_type,
        "quantity": v_quantity,
        "price": v_price,
    })


    try:
        kwargs: dict = dict(
            symbol     = v_symbol,
            side       = v_side,
            order_type = v_type,
            quantity   = str(v_quantity),
            reduce_only= reduce_only,
        )

        if v_type == "LIMIT":
            kwargs["price"]          = str(v_price)
            kwargs["time_in_force"]  = time_in_force
        elif v_type == "STOP_MARKET":
            kwargs["stop_price"] = str(v_price)

        raw = client.place_order(**kwargs)

    except BinanceAPIError as exc:
        logger.error("API error while placing order: code=%s msg=%s", exc.code, exc.msg)
        print(f"\n Order FAILED — Binance API Error {exc.code}: {exc.msg}\n")
        raise

    except ConnectionError as exc:
        logger.error("Network error while placing order: %s", exc)
        print(f"\n Order FAILED — Network error: {exc}\n")
        raise


    result = _format_order_response(raw)
    _print_order_result(result, success=True)
    logger.info(
        "Order complete → id=%s symbol=%s side=%s type=%s status=%s executedQty=%s",
        result["orderId"], result["symbol"], result["side"],
        result["type"], result["status"], result["executedQty"],
    )

    return result
