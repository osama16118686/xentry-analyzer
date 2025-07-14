import httpx
import asyncio

async def fetch_price_data(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)
            if response.status_code != 200:
                return None

            data = response.json()
            market = data.get("market_data", {})

            price = market.get("current_price", {}).get("usd", 0)
            sma7 = market.get("moving_average_7d", price)  # غير متوفرة مباشرة، نستخدم السعر كبديل مؤقت
            rsi = 50  # CoinGecko لا توفر RSI، نقدر نضيف مكتبة لحسابه لاحقًا
            low_30d = market.get("low_30d", price * 0.9)
            support_zone = price <= low_30d * 1.05

            return {
                "price": price,
                "sma7": sma7,
                "rsi": rsi,
                "low_30d": low_30d,
                "support_zone": support_zone,
            }

    except Exception as e:
        print(f"❌ خطأ أثناء جلب البيانات لـ {coin_id}: {e}")
        return None
