import telebot
from services.analyzer import analyze_single_coin
from services.report import get_last_analysis_summary, get_daily_report

BOT_TOKEN = "8016425590:AAGJohER6j7tCmhePCOfrsdczacEJLhqU7U"
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 أهلاً بك في Xentry Crypto Bot.\n\n🪙 اكتب اسم العملة (مثلاً BTC) لتحليلها.\n📊 استخدم الأوامر التالية:\n/status - آخر فحص تلقائي\n/report - تقرير آخر 24 ساعة")

@bot.message_handler(commands=['status'])
def status(message):
    summary = get_last_analysis_summary()
    bot.reply_to(message, summary)

@bot.message_handler(commands=['report'])
def report(message):
    report = get_daily_report()
    bot.reply_to(message, report)

@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    coin = message.text.strip().upper()
    result = analyze_single_coin(coin)
    bot.reply_to(message, result)

def run_bot():
    print("🤖 Telegram bot is running...")
    bot.polling()
