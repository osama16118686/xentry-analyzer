import os
import telebot
import asyncio
from analyzer.logic import analyze_coin, analyze_all_coins
from utils.logger import log
from analyzer import scheduler
from utils.binance_client import place_order  # ← تم التبديل إلى Binance
from trade.trade_manager import open_positions

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 أهلاً بك في Xentry Crypto Bot.\n\nاكتب اسم العملة (مثلاً bitcoin أو solana) لتحليلها.")

@bot.message_handler(commands=['report'])
def report(message):
    if not scheduler.last_analysis_results:
        bot.reply_to(message, "ℹ️ لا توجد نتائج تحليل محفوظة حتى الآن.")
        return

    msg = "📈 نتائج التحليل الأخير:\n\n"
    rare = []
    medium = []

    for coin, count in scheduler.last_analysis_results.items():
        if count == 3:
            rare.append(f"- {coin} ✅✅✅")
        elif count == 2:
            medium.append(f"- {coin} ✅✅")

    if rare:
        msg += "🔥 فرص نادرة (3 شروط):\n" + "\n".join(rare) + "\n\n"
    if medium:
        msg += "✅ فرص متوسطة (2 شروط):\n" + "\n".join(medium) + "\n\n"

    msg += "⚠️ باقي العملات لم تتحقق فيها الشروط.\n"

    if scheduler.last_analysis_time:
        msg += f"\n🕒 آخر تحليل تم في: {scheduler.last_analysis_time}"

    bot.reply_to(message, msg)

@bot.message_handler(commands=['analyze_now'])
def analyze_now(message):
    async def run_analysis():
        results = await analyze_all_coins()
        scheduler.last_analysis_results = {
            coin: len(data["matched_conditions"])
            for coin, data in results.items()
        }
        from datetime import datetime
        scheduler.last_analysis_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        count = len([c for c, matched in scheduler.last_analysis_results.items() if matched >= 2])
        return count

    try:
        loop = asyncio.get_event_loop()
        count = loop.run_until_complete(run_analysis())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        count = loop.run_until_complete(run_analysis())

    bot.reply_to(message, f"✅ تم التحليل اليدوي بنجاح.\n📊 عدد الفرص المكتشفة: {count}")

@bot.message_handler(commands=['status'])
def status(message):
    if not scheduler.last_analysis_results:
        bot.reply_to(message, "ℹ️ لا توجد نتائج تحليل حتى الآن.")
        return

    total = len(scheduler.last_analysis_results)
    time = scheduler.last_analysis_time or "غير متوفر"
    bot.reply_to(message, f"📊 تم تحليل {total} عملة.\n🕒 آخر تحليل: {time}")

@bot.message_handler(commands=['test_trade'])
def test_trade(message):
    try:
        response = place_order(
            symbol="BTCUSDT",
            side="BUY",
            quantity=10.0  # مبلغ افتراضي بالدولار
        )
        if response and response.get("status") == "FILLED":
            bot.reply_to(message, "✅ تم تنفيذ صفقة تجريبية بنجاح (Binance API).")
        else:
            bot.reply_to(message, f"⚠️ لم تنجح الصفقة. الرد:\n{response}")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ أثناء محاولة تنفيذ الصفقة:\n{str(e)}")

@bot.message_handler(func=lambda msg: True)
def handle_coin(message):
    coin = message.text.strip().lower()
    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(analyze_coin(coin))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(analyze_coin(coin))

    if not result:
        bot.reply_to(message, "🚫 لم أتمكن من جلب بيانات العملة.")
        return

    msg = f"📊 تحليل {coin.upper()}:\n"
    msg += f"السعر الحالي: ${result['current_price']}\n"
    msg += f"أقل سعر 30 يوم: ${result['low_30d']}\n"
    msg += f"MA7: ${result['sma7']}\n"
    msg += f"RSI (مؤقت): {result['rsi']}\n"
    msg += f"✅ شروط متحققة: {len(result['matched_conditions'])}/3\n"

    if result["strong_opportunity"]:
        msg += "\n🔥 فرصة نادرة! نسبة نجاح عالية"
    elif result["opportunity"]:
        msg += "\n✅ فرصة شراء متوسطة"
    else:
        msg += "\n⚠️ لا توجد فرصة واضحة الآن"

    bot.reply_to(message, msg)

def start_bot():
    log("🤖 بدء تشغيل بوت التليجرام...")
    bot.polling()
