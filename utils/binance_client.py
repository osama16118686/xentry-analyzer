from binance.client import Client

# مفاتيح API من Binance Spot Testnet
api_key = "3vw03Wx4NgsK8qCpe6yyPiKDaGe6B03RLfEdDx8i2rIaKuXUvgm0UPPah0P1owSMV"
api_secret = "tVkggtXfCCfLfwz8F5g6oglxGGXsMfQ0aW6rbswx7BE4N6O274AivLKo7gh8cns4E"

# الاتصال بـ Binance Testnet
client = Client(api_key, api_secret, testnet=True)
client.API_URL = 'https://testnet.binance.vision/api'
