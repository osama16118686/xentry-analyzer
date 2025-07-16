
import matplotlib.pyplot as plt
import requests
import datetime
from utils import detect_support_levels

def generate_chart_with_support(symbol):
    coin_id = get_coin_id(symbol)
    if not coin_id:
        raise ValueError("رمز العملة غير معروف")

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": 7, "interval": "hourly"}
    response = requests.get(url, params=params)
    prices_raw = response.json().get("prices", [])

    if not prices_raw:
        raise ValueError("لا توجد بيانات كافية")

    prices = [x[1] for x in prices_raw]
    times = [datetime.datetime.fromtimestamp(x[0]/1000) for x in prices_raw]

    supports = detect_support_levels(prices)
    best_buy = supports[0] if supports else round(prices[-1]*0.97, 2)

    # رسم الشارت
    plt.figure(figsize=(10, 5))
    plt.plot(times, prices, label=symbol, linewidth=1.5)
    for level in supports:
        plt.axhline(level, color='gray', linestyle='--', alpha=0.5)
        plt.text(times[-1], level, f"{level:.2f}$", va='bottom', fontsize=8, color='gray')

    plt.title(f"{symbol} - رسم بياني 4H")
    plt.xlabel("الوقت")
    plt.ylabel("السعر ($)")
    plt.tight_layout()
    img_path = f"xentry_crypto_bot/chart_{symbol}.png"
    plt.savefig(f"/mnt/data/{img_path}")
    plt.close()

    summary = f"💰 {symbol}
🎯 أفضل سعر شراء: {best_buy}$
🛡️ خطوط الدعم: " + ", ".join([f"{s:.2f}" for s in supports[:3]])
    return f"/mnt/data/{img_path}", summary

def get_coin_id(symbol):
    # قائمة مختصرة قابلة للتوسيع حسب الحاجة
    common = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "BNB": "binancecoin",
        "SOL": "solana",
        "ADA": "cardano",
        "XRP": "ripple"
    }
    return common.get(symbol.upper())
