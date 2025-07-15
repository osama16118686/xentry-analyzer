from binance.client import Client
import os

api_key = "3vw03Wx4NgsK8qCpe6yyPiKDaGe6B03RLfEdDx8i2rIaKuXUvgm0UPPah0P1owSMV"
api_secret = "tVkggtXfCCfLfwz8F5g6oglxGGXsMfQ0aW6rbswx7BE4N6O274AivLKo7gh8cns4E"

client = Client(api_key, api_secret)
client.API_URL = 'https://testnet.binance.vision/api'

def place_order(symbol, side, quantity):
    try:
        order = client.create_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quoteOrderQty=quantity
        )
        return order
    except Exception as e:
        return {"error": str(e)}