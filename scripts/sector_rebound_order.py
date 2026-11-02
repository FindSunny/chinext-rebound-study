# -*- coding: utf-8 -*-
"""历次熊底之后，申万式一级行业的反弹顺序与幅度。

数据：中证全指一级行业指数 000986-000995（10 个），沪深300、创业板指作基准。
底部定义：沪深300 自峰值下跌 >=30% 进入熊市段，自低点反弹 >=20% 结束该段，
        取该段的低点作为"熊底"。
"""
import os, json, ssl, time
import urllib.request
import numpy as np
import pandas as pd

ssl._create_default_https_context = ssl._create_unverified_context
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(BASE, "data", "sectors_daily.csv")
UA = {"User-Agent": "Mozilla/5.0"}

SECTORS = [
    ("sh000986", "能源"), ("sh000987", "材料"), ("sh000988", "工业"),
    ("sh000989", "可选消费"), ("sh000990", "主要消费"), ("sh000991", "医药"),
    ("sh000992", "金融"), ("sh000993", "信息"), ("sh000994", "通信"),
    ("sh000995", "公用事业"),
]
BENCH = [("sh000300", "沪深300"), ("sz399006", "创业板指")]


def fetch(code, start="2012-06-01"):
    rows = {}
    end = "2026-11-02"
    for _ in range(30):
        url = ("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
               f"?param={code},day,{start},{end},800,qfq")
        raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read()
        d = json.loads(raw).get("data", {})
        if not isinstance(d, dict) or code not in d:
            break
        node = d[code]
        bars = node.get("day") or node.get("qfqday") or []
        if not bars:
            break
        new = 0
        for b in bars:
            if b[0] not in rows:
                rows[b[0]] = float(b[2]); new += 1
        if new == 0 or bars[0][0] <= start:
            break
        y, m, dd = map(int, bars[0][0].split("-"))
        from datetime import date, timedelta
        end = (date(y, m, dd) - timedelta(days=1)).strftime("%Y-%m-%d")
        time.sleep(0.25)
    return rows


if os.path.exists(CACHE):
    px = pd.read_csv(CACHE, parse_dates=["date"]).set_index("date")
    print("缓存命中: %s (%d 行)" % (CACHE, len(px)))
else:
    series = {}
    for code, name in SECTORS + BENCH:
        r = fetch(code)
        print("  %-10s %-8s %d 日  %s .. %s" % (code, name, len(r),
              min(r) if r else "-", max(r) if r else "-"))
        series[name] = pd.Series(r)
    px = pd.DataFrame(series).sort_index()
    px.index = pd.to_datetime(px.index)
    px.index.name = "date"
    px.to_csv(CACHE, encoding="utf-8-sig")
    print("已缓存 ->", CACHE)

px = px.dropna(how="all")
px = px.ffill()
names = [n for _, n in SECTORS]
print("\n区间: %s .. %s，共 %d 个交易日，%d 个行业" %
      (px.index[0].date(), px.index[-1].date(), len(px), len(names)))

# ---------------------------------------------------------------- 找熊底
hs = px["创业板指"].values   # 用创业板识别熊底（牛市熊市更分明）
dts = px.index
n = len(hs)
legs, state, peak, trough = [], "bull", 0, None
for i in range(1, n):
    if state == "bull":
        if hs[i] > hs[peak]:
            peak = i
        if hs[i] / hs[peak] - 1 <= -0.30:
            state, trough = "bear", i
    else:
        if hs[i] < hs[trough]:
            trough = i
        if hs[i] / hs[trough] - 1 >= 0.20:
            legs.append((peak, trough))
            state = "bull"
            peak = trough + int(np.argmax(hs[trough:i + 1]))
if state == "bear":
    legs.append((peak, trough))

print("\n创业板指 熊市段（%d 段，阈值 30%%/20%%）:" % len(legs))
for p, t in legs:
    print("  %s -> %s  %+6.1f%%  历时 %d 日" %
          (dts[p].date(), dts[t].date(), (hs[t] / hs[p] - 1) * 100, t - p))

# 只保留有 120 日前瞻数据的底
MAXH = 120
legmap = {t: p for p, t in legs}
bottoms = [t for _, t in legs if t + MAXH < n]
print("\n可用于反弹分析的熊底（需 %d 日前瞻）: %d 个" % (MAXH, len(bottoms)))
for t in bottoms:
    print("  %s  (创业板指=%.0f, 距峰值 %.1f%%)" %
          (dts[t].date(), hs[t], (hs[t] / hs[legmap[t]] - 1) * 100))

# ---------------------------------------------------------------- 前瞻统计
def fwd(name, t, H):
    c = px[name].values
    if t + H >= len(c):
        return np.nan
    return c[t + H] / c[t] - 1


def days_to(name, t, thr=0.10, maxh=MAXH):
    c = px[name].values
    base = c[t]
    for h in range(1, min(maxh, len(c) - t - 1) + 1):
        if c[t + h] / base - 1 >= thr:
            return h
    return np.nan


print("\n" + "=" * 100)
print("各熊底之后 20 / 60 / 120 个交易日的行业涨幅")
print("=" * 100)
rows = []
for t in bottoms:
    rec = {"底部": str(dts[t].date())}
    for nm in names:
        rec[nm] = fwd(nm, t, 20)
    rows.append(rec)
    line = "  %s  20日: " % dts[t].date()
    line += "  ".join("%s %+.1f" % (nm, rec[nm] * 100) for nm in names if not np.isnan(rec[nm]))
    print(line)

print("\n" + "=" * 100)
print("每个熊底后的【行业排序】（按 20 日涨幅，1=最强）")
print("=" * 100)
rank_tbl = {}
for t in bottoms:
    vals = {nm: fwd(nm, t, 20) for nm in names}
    v = pd.Series(vals).dropna()
    rk = v.rank(ascending=False)
    rank_tbl[str(dts[t].date())] = rk
    order = v.sort_values(ascending=False)
    print("  %s  %s" % (dts[t].date(), "  ".join("%s(%.0f)" % (nm, rk[nm]) for nm in order.index)))

rt = pd.DataFrame(rank_tbl)
print("\n【排序稳定性】各行业在 %d 个熊底中的平均排名（1=最强，10=最弱）:" % rt.shape[1])
avg = rt.mean(axis=1).sort_values()
for nm, r in avg.items():
    sd = rt.loc[nm].std()
    print("  %-8s 平均 %.1f  标准差 %.1f  %s" % (nm, r, sd, "  ".join("%.0f" % rt.loc[nm, c] for c in rt.columns)))

# 排序一致性：底部之间排名相关
print("\n【底部之间的排序一致性】(Spearman, 越接近 1 越说明顺序稳定)")
cc = rt.corr(method="spearman")
print(cc.round(2).to_string())
off = cc.values[np.triu_indices_from(cc.values, k=1)]
print("\n  平均相关系数: %.2f   （>0.5 才算存在稳定顺序，≈0 说明每次都不一样）" % np.nanmean(off))

# 到达 +10% 所需天数（顺序的直接度量）
print("\n" + "=" * 100)
print("【谁先到 +10%】自底部起首次达到 +10% 所需交易日（-表示 120 日内未达到）")
print("=" * 100)
lead = {}
for t in bottoms:
    d = {nm: days_to(nm, t) for nm in names}
    lead[str(dts[t].date())] = d
    print("  %s  %s" % (dts[t].date(),
          "  ".join("%s%s" % (nm, "-" if np.isnan(v) else "%.0f" % v) for nm, v in d.items())))
lt = pd.DataFrame(lead)
print("\n  平均所需交易日（越小越快）:")
for nm, v in lt.mean(axis=1).sort_values().items():
    n_ok = lt.loc[nm].notna().sum()
    print("    %-8s %6.1f 日  (达到 %d/%d 次)" % (nm, v, n_ok, lt.shape[1]))
