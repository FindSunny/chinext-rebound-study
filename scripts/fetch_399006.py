# -*- coding: utf-8 -*-
"""拉取创业板指(399006)日线全历史，双源交叉校验，落盘 CSV。

数据源：
  - 腾讯 web.ifzq.gtimg.cn (按日期区间分页，每页最多约 800 根)
  - 新浪 money.finance.sina.com.cn (最近约 1023 根，用于重叠期逐日比对)
东方财富 push2his 在本机被拒(RemoteDisconnected)，故不采用。
"""
import urllib.request, json, ssl, sys, os, csv, time
from datetime import datetime

ssl._create_default_https_context = ssl._create_unverified_context
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def tencent_range(begin, end, n=800):
    url = ("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
           f"?param=sz399006,day,{begin},{end},{n},qfq")
    j = json.loads(get(url))
    d = j.get("data")
    if not isinstance(d, dict) or "sz399006" not in d:
        return []
    node = d["sz399006"]
    for k in ("day", "qfqday"):
        if k in node:
            return node[k]
    return []


def fetch_all(start="2010-06-01", end=None):
    """从 start 往今天方向逐段取，每段取区间内最后 800 根，再回退。"""
    end = end or datetime.now().strftime("%Y-%m-%d")
    rows = {}
    cur_end = end
    for _ in range(30):
        bars = tencent_range(start, cur_end)
        if not bars:
            break
        new = 0
        for b in bars:
            dt = b[0]
            if dt not in rows:
                rows[dt] = {"date": dt, "open": float(b[1]), "close": float(b[2]),
                            "high": float(b[3]), "low": float(b[4]),
                            "volume": float(b[5]) if b[5] else 0.0}
                new += 1
        first = bars[0][0]
        print(f"  page end={cur_end} -> {len(bars)} bars, range {first}..{bars[-1][0]}, new={new}")
        if first <= start or new == 0:
            break
        # 回退一天
        y, m, d = map(int, first.split("-"))
        from datetime import date, timedelta
        cur_end = (date(y, m, d) - timedelta(days=1)).strftime("%Y-%m-%d")
        time.sleep(0.6)
    return [rows[k] for k in sorted(rows)]


def sina(datalen=1023):
    url = ("https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
           f"CN_MarketData.getKLineData?symbol=sz399006&scale=240&ma=no&datalen={datalen}")
    raw = get(url).decode("utf-8", "replace")
    return json.loads(raw)


def main():
    os.makedirs(OUT, exist_ok=True)
    print("[1] 腾讯分页拉取全历史 ...")
    tx = fetch_all()
    print(f"  合计 {len(tx)} 根, {tx[0]['date']} .. {tx[-1]['date']}")

    p1 = os.path.join(OUT, "399006_daily_tencent.csv")
    with open(p1, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["date", "open", "high", "low", "close", "volume"])
        w.writeheader()
        w.writerows(tx)

    print("[2] 新浪拉取重叠期做交叉校验 ...")
    try:
        sn = sina()
        sn_map = {r["day"]: float(r["close"]) for r in sn}
        tx_map = {r["date"]: r["close"] for r in tx}
        common = sorted(set(sn_map) & set(tx_map))
        diffs = [(d, sn_map[d], tx_map[d]) for d in common if abs(sn_map[d] - tx_map[d]) > 0.05]
        print(f"  重合计 {len(common)} 日, 收盘差异>0.05 的有 {len(diffs)} 日")
        for d in diffs[:10]:
            print(f"    {d[0]} sina={d[1]:.2f} tencent={d[2]:.2f}")
    except Exception as e:
        print(f"  新浪校验失败(不阻塞): {type(e).__name__}: {e}")

    print(f"[3] 落盘 {p1}")
    return p1


if __name__ == "__main__":
    main()
