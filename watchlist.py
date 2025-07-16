
import json
import os

WATCHLIST_FILE = "xentry_crypto_bot/watchlist.json"

def load_watchlist():
    if not os.path.exists(WATCHLIST_FILE):
        return {}
    with open(WATCHLIST_FILE, "r") as f:
        return json.load(f)

def save_watchlist(data):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_to_watchlist(symbol, target_price):
    data = load_watchlist()
    data[symbol] = target_price
    save_watchlist(data)
    return f"📌 تمت إضافة {symbol} إلى قائمة المراقبة عند السعر {target_price}$"

def check_watchlist_prices(bot):
    import requests
    url = "https://api.coingecko.com/api/v3/simple/price"
    data = load_watchlist()
    if not data:
        return

    for symbol, target in data.items():
        coin_id = get_coin_id(symbol)
        if not coin_id:
            continue
        params = {"ids": coin_id, "vs_currencies": "usd"}
        res = requests.get(url, params=params).json()
        current = res.get(coin_id, {}).get("usd")
        if not current:
            continue

        # إذا السعر الحالي قريب من الهدف بـ3%
        if abs(current - target) / target <= 0.03:
            message = f"👁️ {symbol} اقترب من السعر المحدد {target}$\\nالسعر الحالي: {current}$"
            bot.send_message(1795891469, message)  # استخدم معرفك هنا أو خزّنه ديناميكياً

def get_coin_id(symbol):
    from chart import get_coin_id as g
    return g(symbol)
