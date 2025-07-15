import asyncio
from datetime import datetime
from analyzer.logic import analyze_all_coins
from trade.trade_manager import open_positions

last_analysis_results = {}
last_analysis_time = None

async def periodic_analysis():
    global last_analysis_results, last_analysis_time
    while True:
        print("🔄 Running periodic analysis...")
        results = await analyze_all_coins()
        last_analysis_results = {
            coin: len(data["matched_conditions"])
            for coin, data in results.items()
        }
        last_analysis_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await open_positions(results)
        await asyncio.sleep(3600)