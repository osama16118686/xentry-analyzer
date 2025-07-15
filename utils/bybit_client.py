import os
import httpx

BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")

BASE_URL = "https://api-testnet.bybit.com"  # testnet URL

headers = {
    "Content-Type": "application/json",
    "X-BYBIT-API-KEY": BYBIT_API_KEY
}

def place_order(symbol, side, qty, entry_price):
    """
    إرسال أمر شراء أو بيع إلى Bybit Testnet
    """
    order = {
        "category": "spot",
        "symbol": symbol,
        "side": side,
        "orderType": "MARKET",
        "qty": str(qty)
    }

    try:
        response = httpx.post(f"{BASE_URL}/v5/order/create", headers=headers, json=order)
        data = response.json()
        if data.get("retCode") == 0:
            print(f"✅ تم تنفيذ أمر {side} لـ {symbol} بنجاح.")
        else:
            print(f"❌ فشل تنفيذ الأمر: {data.get('retMsg')}")
    except Exception as e:
        print(f"⚠️ خطأ أثناء تنفيذ الطلب: {e}")
