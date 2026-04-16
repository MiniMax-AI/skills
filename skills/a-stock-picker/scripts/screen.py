#!/usr/bin/env python3
"""
A Stock Picker - Layer 1 Quantitative Screener
三层选股模型第一层：量化筛选
数据源：新浪（股票列表）+ 腾讯（K线，单请求）
"""

import json, sys, argparse, time

MARKET_CAP_MIN = 50
MARKET_CAP_MAX = 500
HISTORY_DAYS   = 60
THRESHOLD      = 0.15   # 可调

def fetch_sina_stocks():
    import urllib.request
    all_stocks = []
    for page in range(1, 25):
        url = (f"https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php"
               f"/Market_Center.getHQNodeDataSimple?page={page}&num=50"
               f"&sort=symbol&asc=1&node=hs_a")
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://finance.sina.com.cn"
            })
            with urllib.request.urlopen(req, timeout=8) as r:
                raw = r.read().decode("gbk", errors="ignore")
            page_data = json.loads(raw)
            if not page_data:
                break
            all_stocks.extend(page_data)
        except Exception:
            continue
    return all_stocks

def get_kline(code):
    """获取单只股票K线，返回(closes, vols)或(None, None)"""
    import urllib.request
    full = code  # Sina格式: sh600519 或 sz000858
    url = (f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
           f"?_var=kline_dayqfq&param={full},day,,,{HISTORY_DAYS},qfq&r=0.1")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            raw = r.read().decode("utf-8")
        start = raw.index("=") + 1
        data = json.loads(raw[start:])
        kdata = data.get("data", {})
        # 兼容 dict 和 list 两种返回格式
        if isinstance(kdata, list):
            return None, None
        kline = kdata.get(full, {}).get("qfqday", [])
        if not kline or len(kline) < 35:
            return None, None
        closes = [float(d[2]) for d in kline]
        vols   = [float(d[5]) for d in kline]
        return closes, vols
    except Exception:
        return None, None

def score_stock(s, closes, vols):
    ma5  = sum(closes[-5:]) / 5
    ma15 = sum(closes[-15:]) / 15
    ma60 = sum(closes[-60:]) / min(60, len(closes))
    gain5 = (closes[-1] - closes[-6]) / closes[-6] * 100

    # 趋势
    trend = 0.0
    if ma5 > ma15: trend += 0.5
    if ma15 > ma60: trend += 0.5

    # MACD近似
    macd_s = 0.3 if gain5 > 3 else (0.1 if gain5 > -3 else 0.0)

    # 量比
    avg_v = sum(vols[-5:]) / 5
    vr = vols[-1] / avg_v if avg_v > 0 else 1.0
    vol_s = 1.0 if vr >= 1.3 else (0.5 if vr >= 0.8 else 0.0)

    # 涨幅过滤
    gain_s = 1.0 if gain5 >= 1 else (0.5 if gain5 >= 0 else 0.0)

    total = trend * 0.30 + macd_s * 0.25 + vol_s * 0.20 + gain_s * 0.25
    return {
        "code": s["code"], "name": s["name"],
        "price": s["price"],
        "change_pct": s["change_pct"],
        "turnover": s["turnover"],
        "ma5": round(ma5, 2), "ma15": round(ma15, 2), "ma60": round(ma60, 2),
        "gain5": round(gain5, 2),
        "trend": round(trend, 2), "vr": round(vr, 2),
        "macd_s": macd_s, "vol_s": vol_s, "gain_s": gain_s,
        "total": round(total, 3),
    }

def screen(stocks, top_n=20):
    results = []
    scanned = 0
    for i, s in enumerate(stocks):
        code = s["code"]
        closes, vols = get_kline(code)
        if closes is None:
            print(f"  [{i+1}/{len(stocks)}] {s['name']}({code}) — 无K线数据，跳过", end="\r")
            continue
        scored = score_stock(s, closes, vols)
        scanned += 1
        if scored["total"] >= THRESHOLD:
            results.append(scored)
        print(f"  [{i+1}/{len(stocks)}] 扫描中... 已筛{len(results)}只通过  ", end="\r")
        if (i + 1) % 10 == 0:
            time.sleep(0.1)  # 避免太快触发限流
    results.sort(key=lambda x: x["total"], reverse=True)
    return results[:top_n], scanned

def print_results(results, scanned):
    print(f"\n\n{'='*90}")
    print(f"{'代码':<8}{'名称':<10}{'现价':>7}{'今日%':>7}{'换手%':>6}{'MA5':>7}{'MA15':>8}{'MA60':>8}{'5日涨%':>7}{'量比':>5}{'趋势':>5}{'MACD':>5}{'总分':>5}")
    print(f"{'─'*90}")
    if not results:
        # 显示top10供参照
        print("  今日无标的通过筛选（阈值 {:.2f}）".format(THRESHOLD))
        print("  💡 市场整体偏弱，等指数企稳后再扫")
    else:
        for s in results:
            t = {1.0:"多头", 0.5:"偏多", 0.0:"偏空"}.get(s["trend"], "?")
            mac = "✅" if s["gain5"] > 3 else ("❌" if s["gain5"] < -3 else "  ")
            print(f"{s['code']:<8}{s['name']:<10}{s['price']:>7.2f}{s['change_pct']:>7.2f}{s['turnover']:>6.2f}{s['ma5']:>7.2f}{s['ma15']:>8.2f}{s['ma60']:>8.2f}{s['gain5']:>7.2f}{s['vr']:>5.2f}{t:>5}{mac:>5}{s['total']:>5.2f}")
    print(f"{'─'*90}")
    print(f"  共扫描 {scanned} 只 | 通过筛选 {len(results)} 只 | 阈值 {THRESHOLD}")
    if results:
        print(f"  → 进入第二层定性分析")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--threshold", type=float, default=0.15)
    args = ap.parse_args()
    THRESHOLD = args.threshold

    print(f"\n🔍 A股量化筛选（第一层）| 市值{MARKET_CAP_MIN}~{MARKET_CAP_MAX}亿 | 阈值{THRESHOLD}")
    print("="*60)

    raw = fetch_sina_stocks()
    print(f"  → 新浪获取 {len(raw)} 只")

    stocks = [
        {"code": s["symbol"], "name": s["name"],
         "price": float(s.get("trade", 0) or 0),
         "change_pct": float(s.get("changepercent", 0) or 0),
         "turnover": float(s.get("turnover", 0) or 0)}
        for s in raw
        if s.get("name") and "ST" not in s.get("name", "")
        and 0 < float(s.get("trade", 0) or 0) < 500
        and not s.get("symbol", "").startswith("bj")
    ]
    print(f"  → 候选股票 {len(stocks)} 只")

    results, scanned = screen(stocks, top_n=args.top)
    print_results(results, scanned)
