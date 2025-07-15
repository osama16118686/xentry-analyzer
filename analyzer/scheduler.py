last_analysis_results = {}
last_analysis_time = None  # ← تم إضافة هذا السطر

import asyncio
from datetime import datetime
from analyzer.logic import analyze_all_coins
from utils.logger import log

async def start_scheduler():
    global last_analysis_results, last_analysis_time
    while True:
        log("📡 بدء التحليل التلقائي لجميع العملات...")

        results = await analyze_all_coins()

        # تخزين عدد الشروط لكل عملة
        last_analysis_results = {
            coin: len(data["matched_conditions"])
            for coin, data in results.items()
        }

        last_analysis_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # ← تم إضافة هذا السطر

        count = len([coin for coin, matched in last_analysis_results.items() if matched >= 2])
        log(f"✅ تم التحليل - عدد الفرص: {count} (📅 آخر تحليل: {last_analysis_time})")
        await asyncio.sleep(3600)
