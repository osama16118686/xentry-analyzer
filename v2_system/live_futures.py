"""Live public futures snapshot: OKX (via curl) + Hyperliquid. Read-only public market data, no keys."""
import json, subprocess, urllib.request
def okx(path):
    r = subprocess.run(["curl", "-s", "-m", "20", "https://www.okx.com" + path], capture_output=True, text=True)
    return json.loads(r.stdout)["data"]
def hlinfo():
    req = urllib.request.Request("https://api.hyperliquid.xyz/info", data=b'{"type":"metaAndAssetCtxs"}', headers={"Content-Type": "application/json"})
    m, c = json.load(urllib.request.urlopen(req, timeout=20)); return {u["name"]: x for u, x in zip(m["universe"], c)}
hl = hlinfo()
for c in ("BTC", "ETH", "SOL"):
    o = {}
    try:
        o["perp"] = float(okx(f"/api/v5/market/ticker?instId={c}-USDT-SWAP")[0]["last"])
        o["funding%/8h"] = float(okx(f"/api/v5/public/funding-rate?instId={c}-USDT-SWAP")[0]["fundingRate"])*100
        oi = okx(f"/api/v5/rubik/stat/contracts/open-interest-volume?ccy={c}&period=1H")
        o["OI$bn"] = float(oi[0][1])/1e9; o["OIchg6h%"] = (float(oi[0][1])/float(oi[6][1])-1)*100; o["OIchg24h%"] = (float(oi[0][1])/float(oi[24][1])-1)*100
        ls = okx(f"/api/v5/rubik/stat/contracts/long-short-account-ratio?ccy={c}&period=1H")
        o["L/S"] = float(ls[0][1]); o["L/S_24h_ago"] = float(ls[24][1])
        tk = okx(f"/api/v5/rubik/stat/taker-volume?ccy={c}&instType=CONTRACTS&period=1H")[:6]
        o["takerBuy/Sell6h"] = sum(float(x[2]) for x in tk)/sum(float(x[1]) for x in tk)
    except Exception as e: o["okx_err"] = str(e)[:60]
    h = hl.get(c, {}); o["HL_mark"] = float(h.get("markPx", "nan")); o["HL_funding%/8h"] = float(h.get("funding", "nan"))*800
    print(c, {k: round(v, 4) for k, v in o.items() if isinstance(v, float)}, o.get("okx_err", ""))
