import requests
import os
from utils import calculate_rsi, calculate_ma, detect_support_levels, save_analysis_result

def analyze_top_30():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 30, "page": 1}
    response = requests.get(url, params=params)
    data = response.json()

    if not isinstance(data, list):
        print("❌ الاستجابة غير متوقعة من CoinGecko:", data)
        return

    stablecoins = ['usdt', 'usdc', 'busd', 'dai', 'tusd', 'usdd', 'gusd', 'eurt']
    strong_alerts = []
    results = []
    analyzed_symbols = []
    analyzed_count = 0
    failed_count = 0
    fetched_symbols = []

    for coin in data:
        symbol = coin['symbol'].lower()
        fetched_symbols.append(symbol.upper())
        if symbol in stablecoins:
            continue

        symbol_upper = symbol.upper()
        price = coin['current_price']
        historical = get_historical_data(coin['id'])

        if not historical or len(historical) < 50:
            failed_count += 1
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

        if conditions >= 3:
            status = "✅"
        elif conditions == 2:
            status = "⚠️"
        elif conditions == 1:
            status = "❗"
        else:
            status = "❌"

        results.append((symbol_upper, f"{conditions} {status}", best_buy))
        analyzed_symbols.append(symbol_upper)
        analyzed_count += 1

        if conditions >= 3:
            strong_alerts.append(
                f"🚨 {symbol_upper} - فرصة ممتازة\n"
                f"✅ شروط محققة: {conditions}/3\n"
                f"🎯 أفضل سعر شراء: {best_buy}$"
            )

    # تأكد من وجود مجلد data قبل الحفظ
    if not os.path.exists("data"):
        os.makedirs("data")

    save_analysis_result(results, strong_alerts)

    if not analyzed_symbols:
        analyzed_symbols.append("❌ لم يتم تحليل أي عملة.")
    with open("data/analyzed_symbols.txt", "w") as f:
        f.write("\n".join(analyzed_symbols))

    print(f"✅ تم جلب {len(fetched_symbols)} عملة: {', '.join(fetched_symbols)}")
    print(f"✅ تم تحليل {analyzed_count} عملة بنجاح (استثناء {failed_count} عملة لعدم توفر البيانات).")

def get_historical_data(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": 30, "interval": "hourly"}
        response = requests.get(url, params=params)
        prices = [item[1] for item in response.json().get("prices", [])]
        return prices[-240:]
    except Exception as e:
        print(f"❌ خطأ في جلب البيانات لـ {coin_id}: {str(e)}")
        return []
