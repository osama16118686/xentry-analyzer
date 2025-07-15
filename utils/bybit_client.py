import os
import httpx

BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")

BASE_URL = "https://api-testnet.bybit.com"

headers = {
    "Content-Type": "application/json",
    "X-BYBIT-API-KEY": BYBIT_API_KEY
}

def place_order(symbol, side, qty, entry_price=None, stop_loss=None, take_profit=None):
    """
    تنفيذ أمر على Bybit Testnet مع إمكانية تحديد وقف الخسارة وهدف الربح
    """
    order = {
        "category": "spot",
        "symbol": symbol,
        "side": side,
        "orderType": "MARKET",
        "qty": str(qty)
    }

    # نضيف وقف الخسارة والهدف إذا تم تحديدهم
    if stop_loss:
        order["stopLoss"] = str(stop_loss)
    if take_profit:
        order["takeProfit"] = str(take_profit)

    try:
        response = httpx.post(f"{BASE_URL}/v5/order/create", headers=headers, json=order)
        data = response.json()
        if data.get("retCode") == 0:
            print(f"✅ تم تنفيذ أمر {side} لـ {symbol} بنجاح.")
        else:
            print(f"❌ فشل تنفيذ الأمر: {data.get('retMsg')}")
    except Exception as e:
        print(f"⚠️ خطأ أثناء تنفيذ الطلب: {e}")
