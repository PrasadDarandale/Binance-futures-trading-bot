"""
Input validation for order parameters.
All validators raise ValueError with a clear human-readable message on failure.
"""

from decimal import Decimal, InvalidOperation
from typing import Optional


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


def validate_symbol(symbol: str) -> str:
    """Symbol must be a non-empty uppercase alphabetic string."""
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol cannot be empty.")
    if not symbol.isalpha():
        raise ValueError(
            f"Symbol '{symbol}' is invalid. Use alphanumeric characters only (e.g. BTCUSDT)."
        )
    return symbol


def validate_side(side: str) -> str:
    """Side must be BUY or SELL (case-insensitive)."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(
            f"Side '{side}' is invalid. Choose from: {', '.join(sorted(VALID_SIDES))}."
        )
    return side


def validate_order_type(order_type: str) -> str:
    """Order type must be MARKET, LIMIT, or STOP_MARKET."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Order type '{order_type}' is invalid. "
            f"Choose from: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity: str | float) -> Decimal:
    """Quantity must be a positive number."""
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        raise ValueError(f"Quantity '{quantity}' is not a valid number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be greater than 0 (got {qty}).")
    return qty


def validate_price(price: Optional[str | float], order_type: str) -> Optional[Decimal]:
    """
    Price is required for LIMIT orders; must be a positive number.
    Price is ignored (and warned about) for MARKET orders.
    """
    if order_type == "LIMIT":
        if price is None:
            raise ValueError("Price is required for LIMIT orders.")
        try:
            p = Decimal(str(price))
        except InvalidOperation:
            raise ValueError(f"Price '{price}' is not a valid number.")
        if p <= 0:
            raise ValueError(f"Price must be greater than 0 (got {p}).")
        return p

    if order_type == "STOP_MARKET":
        if price is None:
            raise ValueError("Stop price is required for STOP_MARKET orders.")
        try:
            p = Decimal(str(price))
        except InvalidOperation:
            raise ValueError(f"Stop price '{price}' is not a valid number.")
        if p <= 0:
            raise ValueError(f"Stop price must be greater than 0 (got {p}).")
        return p

    return None  


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: Optional[str | float] = None,
) -> dict:
    """
    Run all validators and return a clean dict of validated parameters.
    Raises ValueError on the first validation failure.
    """
    return {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
        "price": validate_price(price, order_type.strip().upper()),
    }
