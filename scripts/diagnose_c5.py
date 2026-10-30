# -*- coding: utf-8 -*-
"""诊断：C5（连跌>=5周 且 60日<=-25%）为何无先例——历史最近邻有多近。"""
import os, math
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
df = pd.read_csv(os.path.join(BASE, "data", "399006_daily_tencent.csv"), parse_dates=["date"])
df = df.sort_values("date").reset_index(drop=True)
c = df["close"].values
dates = [d.strftime("%Y-%m-%d") for d in df["date"]]
n = len(c)
is_friday = (df["date"].dt.weekday == 4).values

wk = df.set_index("date")["close"].resample("W-FRI").last().dropna()
wv = wk.values
w_idx = wk.index
streak_w = np.zeros(len(wv), dtype=int)
for j in range(1, len(wv)):
    streak_w[j] = streak_w[j - 1] + 1 if wv[j] < wv[j - 1] else 0

week_of = np.searchsorted(w_idx.values, df["date"].values, side="left")
complete = np.zeros(n, dtype=bool)
for j in range(len(w_idx)):
    pos = np.where(week_of == j)[0]
    if len(pos) and (pos[-1] < n - 1 or is_friday[pos[-1]]):
        complete[pos[-1]] = True
streak = np.array([streak_w[min(int(week_of[i]), len(wv) - 1)] if complete[i]
                   else (streak_w[min(int(week_of[i]), len(wv) - 1) - 1] if week_of[i] >= 1 else 0)
                   for i in range(n)])
ret60 = np.full(n, np.nan)
ret60[60:] = c[60:] / c[:-60] - 1
v = np.nan_to_num(ret60, nan=0.0)

hist = np.array([dt < "2026-01-01" for dt in dates])
print("A. 60日跌幅 <= -24% 的日子里，连跌周数的最大值：")
m = (v <= -0.24) & hist
print("   [历史，不含2026] 样本 %d 日，最大连跌周数 = %d" % (m.sum(), streak[m].max() if m.any() else 0))
for i in np.argsort(v)[:6]:
    print("   %s  60日 %6.2f%%  连跌 %d 周" % (dates[i], v[i] * 100, streak[i]))

print("\nB. 连跌周数 >= 5 的日子里，60日跌幅的最小值（跌得最深的一次）：")
m2 = (streak >= 5) & hist
print("   [历史，不含2026] 样本 %d 日" % m2.sum())
idx = np.where(m2)[0]
if len(idx):
    for i in idx[np.argsort(v[idx])[:6]]:
        print("   %s  连跌 %d 周  60日 %6.2f%%" % (dates[i], streak[i], v[i] * 100))

print("\nC. 两个条件各自最接近的时点（综合距离）")
score = streak / 5.0 + np.minimum(-v, 1.0) / 0.25   # 越接近2越好
o = np.argsort(-np.nan_to_num(score))
for i in o[:5]:
    print("   %s  连跌 %d 周  60日 %6.2f%%  综合 %.2f" % (dates[i], streak[i], v[i] * 100, score[i]))
