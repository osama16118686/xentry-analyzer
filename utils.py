
import numpy as np
import os

def calculate_rsi(prices, period=14):
    prices = np.array(prices)
    delta = np.diff(prices)
    up = delta.clip(min=0)
    down = -1 * delta.clip(max=0)
    ema_up = np.mean(up[-period:])
    ema_down = np.mean(down[-period:])
    rs = ema_up / (ema_down + 1e-6)
    return 100 - (100 / (1 + rs))

def calculate_ma(prices, period):
    return np.mean(prices[-period:])

def detect_support_levels(prices, window=10):
    supports = []
    for i in range(window, len(prices) - window):
        is_support = all(prices[i] < prices[i - j] and prices[i] < prices[i + j] for j in range(1, window))
        if is_support:
            supports.append(prices[i])
    return sorted(set(round(s, 2) for s in supports), reverse=True)[:3]

def save_analysis_result(results, strong_alerts):
    if not os.path.exists("data"):
        os.makedirs("data")
    with open("data/analysis.txt", "w") as f:
        for r in results:
            f.write(f"{r[0]} | شروط: {r[1]} | شراء: {r[2]}\n")
    with open("data/strong_alerts.txt", "w") as f:
        for a in strong_alerts:
            f.write(a + "\n")

def summarize_analysis():
    try:
        with open("data/analysis.txt", "r") as f:
            return f.read() or "لا توجد بيانات حالياً."
    except:
        return "❌ لم يتم تنفيذ أي تحليل بعد."
