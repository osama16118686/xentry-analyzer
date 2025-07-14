import random
from utils.logger import log
from utils.data_fetcher import fetch_price_data

# شروط الشراء
def check_conditions(data):
    conditions = {
        "price_below_sma": data["price"] < data["sma7"] * 0.90,
        "rsi_low": data["rsi"] < 35,
        "near_30d_low": data["price"] <= data["low_30d"] * 1.05,
        "strong_support_zone": data["support_zone"],
    }
    matched = [key for key, value in conditions.items() if value]
    return matched

# تحليل عملة واحدة
async def analyze_coin(coin):
    data = await fetch_price_data(coin)
    if not data:
        return None

    matched = check_conditions(data)
    is_opportunity = len(matched) >= 2
    is_strong = len(matched) >= 3 and data["support_zone"]

    log(f"✅ تحليل {coin} - الشروط المحققة: {matched}")
    return {
        "coin": coin,
        "matched_conditions": matched,
        "opportunity": is_opportunity,
        "strong_opportunity": is_strong,
        "current_price": data["price"],
        "support": data["support_zone"],
        "sma7": data["sma7"],
        "rsi": data["rsi"],
        "low_30d": data["low_30d"],
    }

# تحليل جميع العملات
async def analyze_all_coins():
    top_50 = [f"COIN{i}" for i in range(1, 51)]  # لاحقًا نربطها من API حقيقي
    results = {}

    for coin in top_50:
        result = await analyze_coin(coin)
        if result:
            results[coin] = result

    return results
