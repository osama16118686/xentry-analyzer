from utils.bybit_client import place_order

# صفقة وهمية لعملة BTC (أو أي رمز موجود في testnet)
symbol = "BTCUSDT"
side = "Buy"
qty = 0.001  # كمية صغيرة تجريبية
price = 20000  # سعر وهمي (لن يتم التنفيذ غالبًا)
stop_loss = 19500
take_profit = 21000

result = place_order(
    symbol=symbol,
    side=side,
    qty=qty,
    entry_price=price,
    stop_loss=stop_loss,
    take_profit=take_profit
)

if result:
    print("✅ تم إرسال الأمر بنجاح إلى Bybit Testnet.")
    print(result)
else:
    print("❌ فشل في إرسال الأمر.")
