import telebot
import os
from analyzer import analyze_top_30
from chart import generate_chart_with_support
from watchlist import add_to_watchlist, check_watchlist_prices
from utils import summarize_analysis
import threading, time

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

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

@bot.message_handler(commands=['conditions'])
def conditions_command(message):
    try:
        with open("data/analysis.txt", "r") as f:
            lines = f.readlines()
        filtered = [line for line in lines if "شروط: 1" in line or "شروط: 2" in line or "شروط: 3" in line]
        if filtered:
            reply = "📊 العملات التي تحقق شرطًا واحدًا أو أكثر:\n" + "".join(filtered)
        else:
            reply = "❌ لا توجد عملات تحقق أي شرط حالياً."
        bot.send_message(message.chat.id, reply)
    except:
        bot.send_message(message.chat.id, "❌ لم يتم العثور على بيانات تحليل.")

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "🧠 Xentry Crypto Bot – قائمة الأوامر:\n\n"
        "/start – بدء المحادثة\n"
        "/analyzed – عرض العملات التي تم تحليلها ✅\n"
        "/conditions – العملات التي تحقق شرط واحد أو أكثر ⚠️\n"
        "/alerted – عرض أقوى الصفقات (نسبة ≥ 70٪)\n"
        "/check <رمز العملة> – تحليل عملة + الرسم البياني\n"
        "/watch <رمز السعر> – مراقبة عملة وتنبيه عند الوصول\n"
        "/analyze_now – تنفيذ التحليل الآن يدويًا 🧠\n"
        "/help – عرض هذه القائمة 📘"
    )
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['analyze_now'])
def analyze_now_command(message):
    bot.send_message(message.chat.id, "📊 جاري تشغيل التحليل الآن...")
    try:
        analyze_top_30()
        bot.send_message(message.chat.id, "✅ تم تنفيذ التحليل بنجاح.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ أثناء التحليل: {e}")

@bot.message_handler(commands=['analyzed_list'])
def analyzed_list_command(message):
    try:
        with open("data/analyzed_symbols.txt", "r") as f:
            symbols = f.read().splitlines()
        if symbols:
            text = "✅ العملات التي تم تحليلها:\n- " + "\n- ".join(symbols)
        else:
            text = "❌ لا توجد عملات تم تحليلها بعد."
        bot.send_message(message.chat.id, text)
    except:
        bot.send_message(message.chat.id, "❌ لا يمكن قراءة قائمة العملات المحللة.")

def run_analysis_loop():
    while True:
        analyze_top_30()
        check_watchlist_prices(bot)
        time.sleep(1800)

threading.Thread(target=run_analysis_loop, daemon=True).start()

print("✅ Bot is running...")
bot.polling()
