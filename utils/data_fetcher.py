import httpx
import random

async def fetch_coin_data(symbol):
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, params={"localization": "false", "tickers": "false", "market_data": "true"})
            data = r.json()
            prices = [p["price"] for p in data["market_data"]["sparkline_7d"]["price"]]
            rsi = random.uniform(20, 80)
            return {
                "price": data["market_data"]["current_price"]["usd"],
                "prices": prices,
                "rsi": rsi
            }
    except Exception:
        return None

async def get_top_50_coins():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, params={"vs_currency": "usd", "order": "market_cap_desc", "per_page": 50, "page": 1})
            return [c["id"] for c in r.json()]
    except Exception:
        return []