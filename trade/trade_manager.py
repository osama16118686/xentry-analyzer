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

async def open_trade(coin, analysis_result):
    if coin in open_positions:
        return None  # already open

    is_strong = analysis_result["strong_opportunity"]
    is_ok = analysis_result["opportunity"]

    if not is_ok:
        return None

    price = analysis_result["current_price"]
    trade = calculate_trade_levels(price, is_strong)
    open_positions[coin] = trade
    return trade

async def check_open_trades(bot=None, chat_id=None):
    closed = []
    for coin, trade in list(open_positions.items()):
        price = trade["entry"] * 1.08  # simulate current price

        if price <= trade["stop_loss"]:
            result = f"❌ صفقة خاسرة لـ {coin.upper()}.
خسارة: {round(trade['entry'] - price, 4)}"
            closed.append((coin, result))
            del open_positions[coin]
        elif price >= trade["take_profit"]:
            result = f"✅ صفقة رابحة لـ {coin.upper()}!
ربح: {round(price - trade['entry'], 4)}"
            closed.append((coin, result))
            del open_positions[coin]

    if bot and chat_id:
        for _, msg in closed:
            await bot.send_message(chat_id, msg)