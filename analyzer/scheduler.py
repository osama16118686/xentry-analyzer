last_analysis_results = {}

import asyncio
from datetime import datetime
from analyzer.logic import analyze_all_coins
from utils.logger import log

async def start_scheduler():
    global last_analysis_results
    while True:
        log("📡 بدء التحليل التلقائي لجميع العملات...")
        results = await analyze_all_coins()

        # تخزين عدد الشروط لكل عملة
        last_analysis_results = {
            coin: len(data["matched_conditions"])
            for coin, data in results.items()
        }

        count = len([coin for coin, matched in last_analysis_results.items() if matched >= 2])
        log(f"✅ تم التحليل - عدد الفرص: {count}")
        await asyncio.sleep(3600)
