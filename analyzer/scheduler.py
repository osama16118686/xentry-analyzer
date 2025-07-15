last_analysis_results = {}
last_analysis_time = None

import asyncio
from datetime import datetime
from analyzer.logic import analyze_all_coins
from utils.logger import log
from trade.trade_manager import check_open_trades
from config import CHAT_ID
from bot.telegram_bot import bot

async def start_scheduler():
    global last_analysis_results, last_analysis_time
    while True:
        log("📡 بدء التحليل التلقائي لجميع العملات...")

        results = await analyze_all_coins()

        last_analysis_results = {
            coin: len(data["matched_conditions"])
            for coin, data in results.items()
        }

        last_analysis_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        count = len([coin for coin, matched in last_analysis_results.items() if matched >= 2])
        log(f"✅ تم التحليل - عدد الفرص: {count} (📅 آخر تحليل: {last_analysis_time})")

        # ✅ مراقبة الصفقات المفتوحة
        await check_open_trades(bot=bot, chat_id=CHAT_ID)

        await asyncio.sleep(3600)
