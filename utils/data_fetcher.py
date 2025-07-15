import httpx
import os

BYBIT_API_URL = "https://api-testnet.bybit.com"
HEADERS = {
    "Content-Type": "application/json",
    "X-BYBIT-API-KEY": os.getenv("BYBIT_API_KEY"),
    "X-BYBIT-API-SECRET": os.getenv("BYBIT_API_SECRET")
}

async def fetch_price_data(symbol):
    endpoint = f"/v5/market/tickers"
    url = BYBIT_API_URL + endpoint

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params={"category": "spot", "symbol": symbol})

            if response.status_code != 200:
                print(f"⚠️ فشل جلب {symbol} - Status {response.status_code}")
                return None

            data = response.json().get("result", {}).get("list", [])
            if not data:
                print(f"❌ لم يتم العثور على بيانات لـ {symbol}")
                return None

            ticker = data[0]
            price = float(ticker["lastPrice"])
            low_price = float(ticker["lowPrice24h"])

            # مؤشرات وهمية مؤقتًا
            sma7 = price
            rsi = 50
            support_zone = price <= low_price * 1.05

            print(f"✅ تم جلب {symbol} - السعر: {price}")
            return {
                "price": price,
                "sma7": sma7,
                "rsi": rsi,
                "low_30d": low_price,
                "support_zone": support_zone
            }

    except Exception as e:
        print(f"❌ خطأ أثناء جلب بيانات {symbol}: {e}")
        return None
