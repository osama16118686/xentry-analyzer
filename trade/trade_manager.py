from utils.binance_client import place_order
from utils.logger import log

open_trades = {}

async def open_positions(results):
    for symbol, data in results.items():
        if symbol in open_trades:
            continue

        matched = len(data["matched_conditions"])
        if matched >= 2:
            amount = 200 if matched == 3 else 100
            response = place_order(symbol.upper() + "USDT", "BUY", amount)
            if response and "error" not in response:
                open_trades[symbol] = response["orderId"]
                log(f"🚀 Opened position for {symbol.upper()} | Amount: ${amount}")
            else:
                log(f"❌ Failed to open position for {symbol.upper()} | {response}")