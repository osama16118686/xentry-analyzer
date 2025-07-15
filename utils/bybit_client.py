import os
import httpx

# جلب مفاتيح API من متغيرات البيئة
BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")

# رابط testnet الخاص بـ Bybit
BASE_URL = "https://api-testnet.bybit.com"

# إعداد الهيدر
headers = {
    "Content-Type": "application/json",
    "X-BYBIT-API-KEY": BYBIT_API_KEY
}

def place_order(symbol, side, qty, entry_price=None, stop_loss=None, take_profit=None):
    """
    تنفيذ أمر على Bybit Testnet مع إمكانية تحديد وقف الخسارة وهدف الربح.
    """
    order = {
        "category": "spot",
        "symbol": symbol,
        "side": side,
        "orderType": "MARKET",  # أمر مباشر بالسعر الحالي
        "qty": str(qty)
    }

    # هذه المفاتيح غير مدعومة في "spot" API مباشرة ولكن نضعها اختياريًا في حال دعم مستقبلي
    if stop_loss:
        order["stopLoss"] = str(stop_loss)
    if take_profit:
        order["takeProfit"] = str(take_profit)

    try:
        response = httpx.post(f"{BASE_URL}/v5/order/create", headers=headers, json=order)
        data = response.json()
        return data  # ← مهم جدًا أن نُعيد البيانات ليتم استخدامها في مكان آخر
    except Exception as e:
        return {"error": str(e)}
