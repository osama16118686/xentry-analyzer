import asyncio
from datetime import datetime
from analyzer.logic import analyze_all_coins
from utils.logger import log
from utils.notifier import notify_opportunity

async def start_scheduler():
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log(f"بدء تحليل العملات في {now}")

        results = await analyze_all_coins()

        for coin, result in results.items():
            if result["strong_opportunity"]:
                await notify_opportunity(coin, result, strength="قوية")
            elif result["opportunity"]:
                await notify_opportunity(coin, result, strength="عادية")

        log("انتهاء التحليل، الانتظار 60 دقيقة...")
        await asyncio.sleep(3600)  # تحليل كل ساعة
