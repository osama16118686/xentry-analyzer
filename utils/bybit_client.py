import os
from pybit.unified_trading import HTTP

# جلب المفاتيح من البيئة
api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

# الاتصال بـ Bybit Testnet
session = HTTP(
    testnet=True,
    api_key=api_key,
    api_secret=api_secret,
)

# تنفيذ صفقة Spot بدون stop loss أو take profit
def place_order(symbol, side, qty, entry_price):
    try:
        response = session.place_order(
            category="spot",
            symbol=symbol.upper(),
            side=side,
            orderType="Limit",
            qty=str(qty),
            price=str(entry_price),
            timeInForce="GTC"
        )
        return response
    except Exception as e:
        return {"error": str(e)}
