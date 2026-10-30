# -*- coding: utf-8 -*-
"""核对：本轮下跌首次跌破「自高点 -40%」是哪一天（对应表里第 5 次触发）。"""
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
df = pd.read_csv(os.path.join(BASE, "data", "399006_daily_tencent.csv"), parse_dates=["date"])
df = df.sort_values("date").reset_index(drop=True)
c = df["close"].values
d = [x.strftime("%Y-%m-%d") for x in df["date"]]
peak = c.max()
thr = peak * 0.60
print("高点 %.2f  ->  -40%% 阈值 %.2f" % (peak, thr))

recent = [i for i in range(len(c)) if d[i] >= "2026-09-01"]
crossed = [i for i in recent if c[i] <= thr]
if crossed:
    i = crossed[0]
    print("首次收盘跌破阈值: %s  收盘 %.2f  回撤 %.2f%%" % (d[i], c[i], (c[i] / peak - 1) * 100))
    j = max(0, i - 3)
    for k in range(j, min(i + 3, len(c))):
        print("   %s  %.2f  (%.2f%%)" % (d[k], c[k], (c[k] / peak - 1) * 100))
else:
    print("本轮尚未跌破阈值")

# 该阈值上方最近一次收盘
above = [i for i in recent if c[i] > thr]
if above:
    print("阈值上方最后一个交易日: %s %.2f" % (d[above[-1]], c[above[-1]]))
