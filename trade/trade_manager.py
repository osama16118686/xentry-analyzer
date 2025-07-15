from utils.binance_client import place_order
from utils.data_fetcher import fetch_price_data

open_positions = {}

def calculate_trade_levels(price, is_strong):
    entry = round(price, 4)
    stop_loss = round(entry * 0.975, 4)  # max 2.5% loss
    take_profit = round(entry * 1.07, 4)  # target 7% gain as midpoint
    amount = 200 if is_strong else 100

    return {
        "entry": entry,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "amount": amount
    }

async def open_trade(coin, analysis_result, bot=None, chat_id=None):
    if coin in open_positions:
        return None  # already open

    is_strong = analysis_result["strong_opportunity"]
    is_ok = analysis_result["opportunity"]

    if not is_ok:
        return None

    price = analysis_result["current_price"]
    trade = calculate_trade_levels(price, is_strong)
    open_positions[coin] = trade

    # تنفيذ الصفقة فعليًا
    place_order(
        symbol=coin,
        side="BUY",
        quantity=trade["amount"],
        price=trade["entry"]
    )

    # إرسال تنبيه عبر التلغرام
    if bot and chat_id:
        msg = (
            f"🟢 تم فتح صفقة لـ {coin.upper()}.\n"
            f"سعر الدخول: {trade['entry']}\n"
            f"وقف الخسارة: {trade['stop_loss']}\n"
            f"جني الربح: {trade['take_profit']}"
        )
        await bot.send_message(chat_id, msg)

    return trade

async def check_open_trades(bot=None, chat_id=None):
    closed = []
    for coin, trade in list(open_positions.items()):
        data = await fetch_price_data(coin)
        if not data:
            continue

        price = data["price"]

        if price <= trade["stop_loss"]:
            result = (
                f"❌ تم تفعيل وقف الخسارة لـ {coin.upper()} بسعر السوق.\n"
                f"السعر الحالي: {price}\n"
                f"الخسارة: {round(trade['entry'] - price, 4)}"
            )
            del open_positions[coin]
            if bot and chat_id:
                await bot.send_message(chat_id, result)

        elif price >= trade["take_profit"]:
            result = (
                f"✅ تم تحقيق جني الأرباح لـ {coin.upper()}!\n"
                f"السعر الحالي: {price}\n"
                f"الربح: {round(price - trade['entry'], 4)}"
            )
            del open_positions[coin]
            if bot and chat_id:
                await bot.send_message(chat_id, result)
