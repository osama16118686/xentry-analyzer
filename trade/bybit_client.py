from pybit.unified_trading import HTTP

session = HTTP(
    testnet=True,
    api_key="pTJd8gOnB7Ckz9XE9c",
    api_secret="yXIL0fjWHD3ktsI8pncIUdd1QDCkVXpwbHTH"
)

def get_balance():
    return session.get_wallet_balance(accountType="UNIFIED")

def place_order(symbol, side, qty, entry_price, stop_loss, take_profit):
    try:
        response = session.place_order(
            category="spot",
            symbol=symbol.upper(),
            side=side,
            orderType="Limit",
            qty=qty,
            price=entry_price,
            timeInForce="GTC",
            stopLoss=stop_loss,
            takeProfit=take_profit
        )
        return response
    except Exception as e:
        print(f"❌ خطأ في تنفيذ الأمر: {e}")
        return None
