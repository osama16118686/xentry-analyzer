from pybit.unified_trading import HTTP

session = HTTP(
    testnet=True,
    api_key="pTJd8gOnB7Ckz9XE9c",
    api_secret="yXIL0fjWHD3ktsI8pncIUdd1QDCkVXpwbHTH"
)

def get_balance():
    try:
        return session.get_wallet_balance(accountType="UNIFIED")
    except Exception as e:
        print(f"❌ خطأ أثناء جلب الرصيد: {e}")
        return None

def place_order(symbol, side, qty, entry_price):
    try:
        response = session.place_order(
            category="spot",  # يمكن تغييره إلى 'linear' إذا كنت تستخدم عقود
            symbol=symbol.upper(),
            side=side,
            orderType="Limit",
            qty=qty,
            price=entry_price,
            timeInForce="GTC"
        )
        return response
    except Exception as e:
        print(f"❌ خطأ في تنفيذ الأمر: {e}")
        return {"error": str(e)}
