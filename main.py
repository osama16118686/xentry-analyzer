import requests

@bot.message_handler(commands=['price'])
def price_command(message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "❌ الرجاء إرسال الأمر بهذا الشكل: /price <رمز العملة>")
            return
        symbol = parts[1].lower()

        # نجيب بيانات السوق من CoinGecko
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {"vs_currency": "usd", "ids": "", "order": "market_cap_desc", "per_page": 250, "page": 1, "sparkline": False}
        response = requests.get(url, params=params)
        data = response.json()

        # نحاول نلاقي العملة اللي اسمها مطابق للرمز المدخل
        price = None
        name = None
        for coin in data:
            if coin['symbol'].lower() == symbol:
                price = coin['current_price']
                name = coin['name']
                break

        if price is not None:
            bot.send_message(message.chat.id, f"💰 سعر {name} ({symbol.upper()}) الحالي هو: ${price}")
        else:
            bot.send_message(message.chat.id, f"❌ لم أجد عملة بالرمز '{symbol.upper()}'")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ: {str(e)}")
