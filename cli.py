#!/usr/bin/env python3
"""
Trading Bot CLI — Binance Futures Testnet (USDT-M)

Usage examples
--------------
# Market BUY
python cli.py place-order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Limit SELL
python cli.py place-order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 100000

# Stop-Market BUY
python cli.py place-order --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.001 --price 95000

# Ping testnet
python cli.py ping

# Show account balances
python cli.py account

# List open orders
python cli.py open-orders --symbol BTCUSDT

# Cancel an order
python cli.py cancel-order --symbol BTCUSDT --order-id 123456789
"""

import os
import sys
from pathlib import Path  # ADD THIS
from typing import Optional


sys.path.insert(0, str(Path(__file__).resolve().parent))

import click

from bot.logging_config import setup_logging, get_logger
from bot.client import BinanceClient, BinanceAPIError
from bot.orders import place_order
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
)

setup_logging()
logger = get_logger(__name__)


def _get_client() -> BinanceClient:
    """
    Build a BinanceClient from environment variables.

    Required env vars:
        BINANCE_API_KEY
        BINANCE_API_SECRET

    Optional:
        BINANCE_BASE_URL  (default: https://testnet.binancefuture.com)
    """
    api_key    = os.environ.get("BINANCE_API_KEY", "").strip()
    api_secret = os.environ.get("BINANCE_API_SECRET", "").strip()
    base_url   = os.environ.get("BINANCE_BASE_URL", "https://testnet.binancefuture.com").strip()

    if not api_key or not api_secret:
        click.echo(
            "\n  Missing credentials.\n"
            "    Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables.\n"
            "    Example:\n"
            "      export BINANCE_API_KEY=your_key\n"
            "      export BINANCE_API_SECRET=your_secret\n",
            err=True,
        )
        sys.exit(1)

    return BinanceClient(api_key=api_key, api_secret=api_secret, base_url=base_url)


def _validate_symbol_cb(ctx, param, value):
    try:
        return validate_symbol(value)
    except ValueError as exc:
        raise click.BadParameter(str(exc))


def _validate_side_cb(ctx, param, value):
    try:
        return validate_side(value)
    except ValueError as exc:
        raise click.BadParameter(str(exc))


def _validate_type_cb(ctx, param, value):
    try:
        return validate_order_type(value)
    except ValueError as exc:
        raise click.BadParameter(str(exc))


def _validate_quantity_cb(ctx, param, value):
    try:
        return validate_quantity(value)
    except ValueError as exc:
        raise click.BadParameter(str(exc))

@click.group()
@click.version_option("1.0.0", prog_name="Trading Bot")
def cli():
    """
      Binance Futures Testnet Trading Bot

    Manages orders on the USDT-M perpetual futures testnet.
    Set BINANCE_API_KEY and BINANCE_API_SECRET before use.
    """

@cli.command("place-order")
@click.option(
    "--symbol", "-s",
    required=True,
    callback=_validate_symbol_cb,
    help="Trading pair, e.g. BTCUSDT",
)
@click.option(
    "--side",
    required=True,
    type=click.Choice(["BUY", "SELL"], case_sensitive=False),
    callback=_validate_side_cb,
    help="Order side: BUY or SELL",
)
@click.option(
    "--type", "order_type",
    required=True,
    type=click.Choice(["MARKET", "LIMIT", "STOP_MARKET"], case_sensitive=False),
    callback=_validate_type_cb,
    help="Order type: MARKET | LIMIT | STOP_MARKET",
)
@click.option(
    "--quantity", "-q",
    required=True,
    type=str,
    callback=_validate_quantity_cb,
    help="Order quantity (e.g. 0.001 for BTC)",
)
@click.option(
    "--price", "-p",
    default=None,
    type=str,
    help="Limit price (required for LIMIT) or stop price (required for STOP_MARKET)",
)
@click.option(
    "--tif",
    default="GTC",
    type=click.Choice(["GTC", "IOC", "FOK"], case_sensitive=False),
    show_default=True,
    help="Time-in-force for LIMIT orders",
)
@click.option(
    "--reduce-only",
    is_flag=True,
    default=False,
    help="Mark order as reduce-only (closes existing position only)",
)
def cmd_place_order(symbol, side, order_type, quantity, price, tif, reduce_only):
    """Place a MARKET, LIMIT, or STOP_MARKET order on Binance Futures Testnet."""

    # Validate price here since we need order_type context
    try:
        validate_price(price, order_type)
    except ValueError as exc:
        raise click.UsageError(str(exc))

    logger.info(
        "CLI → place-order symbol=%s side=%s type=%s qty=%s price=%s",
        symbol, side, order_type, quantity, price,
    )

    client = _get_client()

    try:
        place_order(
            client=client,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            time_in_force=tif.upper(),
            reduce_only=reduce_only,
        )
    except (ValueError, BinanceAPIError, ConnectionError):
        sys.exit(1)
    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        click.echo(f"\n Unexpected error: {exc}", err=True)
        sys.exit(1)

@cli.command("ping")
def cmd_ping():
    """Check connectivity to the Binance Futures Testnet."""
    client = _get_client()
    if client.ping():
        click.echo("  Testnet is reachable.")
    else:
        click.echo("  Testnet is NOT reachable.", err=True)
        sys.exit(1)


@cli.command("account")
@click.option(
    "--show-all",
    is_flag=True,
    default=False,
    help="Show all assets, including zero balances",
)
def cmd_account(show_all):
    """Display account balances from Binance Futures Testnet."""
    client = _get_client()
    try:
        data = client.get_account()
    except BinanceAPIError as exc:
        click.echo(f"\n  API Error {exc.code}: {exc.msg}", err=True)
        sys.exit(1)
    except ConnectionError as exc:
        click.echo(f"\n  Network error: {exc}", err=True)
        sys.exit(1)

    assets = data.get("assets", [])
    print("\n" + "═" * 60)
    print("  ACCOUNT BALANCES (Binance Futures Testnet)")
    print("═" * 60)
    for asset in assets:
        wallet = float(asset.get("walletBalance", 0))
        if wallet == 0 and not show_all:
            continue
        print(
            f"  {asset.get('asset', '???'):<10}"
            f"  Wallet: {wallet:>14.4f}"
            f"  Unrealized PnL: {float(asset.get('unrealizedProfit', 0)):>10.4f}"
        )
    print("═" * 60 + "\n")

@cli.command("open-orders")
@click.option(
    "--symbol", "-s",
    default=None,
    callback=lambda ctx, p, v: validate_symbol(v) if v else None,
    help="Filter by symbol, e.g. BTCUSDT (omit for all symbols)",
)
def cmd_open_orders(symbol):
    """List all open orders on Binance Futures Testnet."""
    client = _get_client()
    try:
        orders = client.get_open_orders(symbol=symbol)
    except BinanceAPIError as exc:
        click.echo(f"\n  API Error {exc.code}: {exc.msg}", err=True)
        sys.exit(1)
    except ConnectionError as exc:
        click.echo(f"\n  Network error: {exc}", err=True)
        sys.exit(1)

    if not orders:
        click.echo(
            f"\n  No open orders"
            + (f" for {symbol}" if symbol else "")
            + ".\n"
        )
        return

    print(f"\n{'═'*70}")
    print(f"  OPEN ORDERS{' — ' + symbol if symbol else ''}")
    print(f"{'═'*70}")
    for o in orders:
        print(
            f"  ID: {o.get('orderId'):<14} "
            f"{o.get('symbol'):<12} "
            f"{o.get('side'):<5} "
            f"{o.get('type'):<15} "
            f"qty={o.get('origQty')} "
            f"price={o.get('price')} "
            f"status={o.get('status')}"
        )
    print(f"{'═'*70}\n")

@cli.command("cancel-order")
@click.option(
    "--symbol", "-s",
    required=True,
    callback=_validate_symbol_cb,
    help="Trading pair, e.g. BTCUSDT",
)
@click.option(
    "--order-id",
    required=True,
    type=int,
    help="The orderId to cancel",
)
def cmd_cancel_order(symbol, order_id):
    """Cancel an open order by orderId."""
    client = _get_client()
    try:
        result = client.cancel_order(symbol=symbol, order_id=order_id)
    except BinanceAPIError as exc:
        click.echo(f"\n  API Error {exc.code}: {exc.msg}", err=True)
        sys.exit(1)
    except ConnectionError as exc:
        click.echo(f"\n  Network error: {exc}", err=True)
        sys.exit(1)

    click.echo(
        f"\n  Order cancelled → orderId={result.get('orderId')} "
        f"status={result.get('status')}\n"
    )

if __name__ == "__main__":
    cli()
