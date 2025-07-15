import httpx
import statistics
from utils.data_fetcher import fetch_coin_data
from utils.logger import log

async def analyze_coin(symbol):
    try:
        data = await fetch_coin_data(symbol)
        if not data:
            return None

        current_price = data["price"]
        sma7 = statistics.mean(data["prices"][-7:])
        rsi = data["rsi"]
        low_30d = min(data["prices"])

        matched = []
        if current_price < sma7 * 0.9:
            matched.append("MA7")
        if rsi < 35:
            matched.append("RSI")
        if current_price <= low_30d * 1.05:
            matched.append("LOW30")

        opportunity = len(matched) >= 2
        strong_opportunity = len(matched) == 3

        return {
            "current_price": round(current_price, 4),
            "sma7": round(sma7, 4),
            "rsi": round(rsi, 2),
            "low_30d": round(low_30d, 4),
            "matched_conditions": matched,
            "opportunity": opportunity,
            "strong_opportunity": strong_opportunity
        }
    except Exception as e:
        log(f"[ERROR] analyze_coin: {e}")
        return None

async def analyze_all_coins():
    from utils.data_fetcher import get_top_50_coins
    coins = await get_top_50_coins()
    results = {}
    for coin in coins:
        result = await analyze_coin(coin)
        if result:
            results[coin] = result
    return results