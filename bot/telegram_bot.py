
import os
import telebot
import asyncio
from analyzer.logic import analyze_coin
from utils.logger import log

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 أهلاً بك في Xentry Crypto Bot.\n\nاكتب اسم العملة (مثلاً bitcoin أو solana) لتحليلها.")

@bot.message_handler(func=lambda msg: True)
def handle_coin(message):
    coin = message.text.strip().lower()
    result = asyncio.run(analyze_coin(coin))
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
@bot.message_handler(commands=['report'])
def report(message):
    from analyzer import scheduler
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

    msg += "⚠️ باقي العملات لم تتحقق فيها الشروط."
    bot.reply_to(message, msg)
