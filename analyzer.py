import requests
from utils import calculate_rsi, calculate_ma, detect_support_levels, save_analysis_result

def analyze_top_100():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 100, "page": 1}
    response = requests.get(url, params=params)
    data = response.json()

    # التحقق من صحة الاستجابة
    if not isinstance(data, list):
        print("❌ الاستجابة غير متوقعة من CoinGecko:", data)
        return

    stablecoins = ['usdt', 'usdc', 'busd', 'dai', 'tusd', 'usdd', 'gusd', 'eurt']
    strong_alerts = []
    results = []
    analyzed_count = 0

    for coin in data:
        symbol = coin['symbol'].lower()
        if symbol in stablecoins:
            continue  # تجاهل العملات المستقرة

        symbol_upper = symbol.upper()
        price = coin['current_price']
        historical = get_historical_data(coin['id'])

        if not historical:
            continue

        rsi = calculate_rsi(historical)
        ma7 = calculate_ma(historical, 7)
        lowest = min(historical)

        conditions = 0
        if price < ma7 * 0.9:
            conditions += 1
        if rsi < 35:
            conditions += 1
        if price <= lowest * 1.05:
            conditions += 1

        supports = detect_support_levels(historical)
        best_buy = supports[0] if supports else round(price * 0.97, 2)

        results.append((symbol_upper, conditions, best_buy))
        analyzed_count += 1

        if conditions >= 3:
            strong_alerts.append(f"""🚨 {symbol_upper} - فرصة ممتازة
🎯 أفضل سعر شراء: {best_buy}$""")

    save_analysis_result(results, strong_alerts)
    print(f"✅ تم تحليل {analyzed_count} عملة (بعد استثناء العملات المستقرة).")

def get_historical_data(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": 30, "interval": "hourly"}
        response = requests.get(url, params=params)
        prices = [item[1] for item in response.json().get("prices", [])]
        return prices[-240:]  # آخر 10 أيام × 24 ساعة ÷ 4 = 240 (شموع 4 ساعات)
    except Exception as e:
        print(f"❌ خطأ في جلب البيانات لـ {coin_id}: {str(e)}")
        return []
