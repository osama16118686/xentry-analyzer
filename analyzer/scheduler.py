
import asyncio
from datetime import datetime
from analyzer.logic import analyze_all_coins
from utils.logger import log

async def start_scheduler():
    while True:
        log("📡 بدء التحليل التلقائي لجميع العملات...")
        results = await analyze_all_coins()
        count = len([c for c in results.values() if c['opportunity'] or c['strong_opportunity']])
        log(f"✅ تم التحليل - عدد الفرص: {count}")
        await asyncio.sleep(3600)
