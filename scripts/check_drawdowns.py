# -*- coding: utf-8 -*-
"""核对历史最大回撤段，用于方案文档中的类比事实校验。"""
import os
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
df = pd.read_csv(os.path.join(BASE, "data", "399006_daily_tencent.csv"), parse_dates=["date"])
df = df.sort_values("date").reset_index(drop=True)
c = df["close"].values
d = df["date"]

dds = []
peak_i = 0
for i in range(1, len(c)):
    if c[i] > c[peak_i]:
        peak_i = i
    dds.append((c[i] / c[peak_i] - 1, peak_i, i))

print("最大回撤段（峰 -> 谷，按深度排序，峰值间隔 >=40 交易日去重）:")
seen = []
for dd, pi, ti in sorted(dds, key=lambda x: x[0]):
    if any(abs(pi - sp) < 40 for sp in seen):
        continue
    seen.append(pi)
    print(f"  {d[pi].date()} {c[pi]:8.1f}  ->  {d[ti].date()} {c[ti]:8.1f}   {dd*100:6.1f}%")
    if len(seen) >= 6:
        break

print("\n各年度 年内最高 -> 最低:")
df["y"] = df["date"].dt.year
for y, g in df.groupby("y"):
    hi, lo = g["close"].max(), g["close"].min()
    print(f"  {y}: {hi:8.1f} -> {lo:8.1f}  {(lo/hi-1)*100:6.1f}%")
