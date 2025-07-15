from utils.logger import log
from utils.data_fetcher import fetch_price_data

def check_conditions(data):
    return [
        "price_below_sma" if data["price"] < data["sma7"] * 0.90 else None,
        "rsi_low" if data["rsi"] < 35 else None,
        "near_30d_low" if data["price"] <= data["low_30d"] * 1.05 else None,
        "strong_support_zone" if data["support_zone"] else None
    ]

async def analyze_coin(coin):
    data = await fetch_price_data(coin)
    if not data:
        return None

    matched = list(filter(None, check_conditions(data)))
    return {
        "coin": coin,
        "matched_conditions": matched,
        "opportunity": len(matched) >= 2,
        "strong_opportunity": len(matched) >= 3 and data["support_zone"],
        "current_price": data["price"],
        "support": data["support_zone"],
        "sma7": data["sma7"],
        "rsi": data["rsi"],
        "low_30d": data["low_30d"],
    }

async def analyze_all_coins():
    top_50 = [
        "bitcoin", "ethereum", "tether", "bnb", "solana", "ripple", "dogecoin", "cardano",
        "avalanche", "shiba-inu", "polkadot", "chainlink", "tron", "polygon", "litecoin",
        "uniswap", "internet-computer", "stellar", "aptos", "vechain", "filecoin", "arweave",
        "the-graph", "algorand", "aave", "maker", "elrond-erd-2", "tezos", "decentraland",
        "theta-token", "fantom", "injective-protocol", "chiliz", "render-token", "synthetix",
        "ocean-protocol", "flow", "iota", "gala", "curve-dao-token", "1inch", "kava", "zcash",
        "dash", "ens", "quant-network", "nexo", "rocket-pool", "immutable-x", "lido-dao"
    ]
    results = {}
    for coin in top_50:
        result = await analyze_coin(coin)
        if result:
            results[coin] = result
        await asyncio.sleep(1.5)  # تأخير لتجنب الحظر من CoinGecko

    return results
