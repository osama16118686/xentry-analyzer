import httpx
import asyncio

async def fetch_price_data(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)

            if response.status_code != 200:
                print(f"⚠️ فشل جلب {coin_id} - Status {response.status_code}")
                return None

            print(f"✅ تم جلب {coin_id} - Status {response.status_code}")  # ← السطر المضاف

            data = response.json()
            market = data.get("market_data", {})

            price = market.get("current_price", {}).get("usd", 0)
            sma7 = price  # لا يتوفر فعليًا من CoinGecko
            rsi = 50      # وهمي مؤقتًا (نضيف الحقيقي لاحقًا)
            low_30d = market.get("low_30d", {}).get("usd", price * 0.9)
            support_zone = price <= low_30d * 1.05

            return {
                "price": price,
                "sma7": sma7,
                "rsi": rsi,
                "low_30d": low_30d,
                "support_zone": support_zone,
            }

    except httpx.RequestError as e:
        print(f"❌ Request error for {coin_id}: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error for {coin_id}: {e}")
        return None
