
import telebot
import os
from analyzer import analyze_top_100
from chart import generate_chart_with_support
from watchlist import add_to_watchlist, check_watchlist_prices
from utils import summarize_analysis

# تحميل التوكن من .env
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# أوامر Telegram

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, "🤖 أهلاً بك في Xentry Crypto Bot! أرسل /analyzed لتحصل على تقرير العملات، أو /check <رمز العملة> لرؤية التحليل البياني.")

@bot.message_handler(commands=['analyzed'])
def analyzed_command(message):
    result = summarize_analysis()
    bot.send_message(message.chat.id, result)

@bot.message_handler(commands=['alerted'])
def alerted_command(message):
    with open("data/strong_alerts.txt", "r") as f:
        alerts = f.read()
    bot.send_message(message.chat.id, alerts or "لا توجد صفقات قوية حالياً.")

@bot.message_handler(commands=['watch'])
def watch_command(message):
    try:
        _, symbol, price = message.text.split()
        response = add_to_watchlist(symbol.upper(), float(price))
        bot.send_message(message.chat.id, response)
    except:
        bot.send_message(message.chat.id, "❌ الصيغة غير صحيحة. مثال: /watch BTC 52000")

@bot.message_handler(commands=['check'])
def check_command(message):
    try:
        _, symbol = message.text.split()
        img_path, summary = generate_chart_with_support(symbol.upper())
        bot.send_photo(message.chat.id, open(img_path, 'rb'), caption=summary)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ لم أتمكن من تحليل العملة. {str(e)}")

# تشغيل الفحص الدوري كل 30 دقيقة
import threading, time

def run_analysis_loop():
    while True:
        analyze_top_100()
        check_watchlist_prices(bot)
        time.sleep(1800)  # 30 دقيقة

threading.Thread(target=run_analysis_loop, daemon=True).start()

print("✅ Bot is running...")
bot.polling()
