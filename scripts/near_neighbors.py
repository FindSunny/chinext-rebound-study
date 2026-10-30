# -*- coding: utf-8 -*-
"""最近邻时点的前瞻表现：2012-02-01 / 2024-02-02 / 2011-12-27 等。"""
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
df = pd.read_csv(os.path.join(BASE, "data", "399006_daily_tencent.csv"), parse_dates=["date"])
df = df.sort_values("date").reset_index(drop=True)
c = df["close"].values
dates = [d.strftime("%Y-%m-%d") for d in df["date"]]
n = len(c)

TARGETS = ["2012-02-01", "2012-01-18", "2011-12-27", "2024-02-02", "2015-07-07", "2015-10-21"]

for t in TARGETS:
    if t not in dates:
        continue
    i = dates.index(t)
    print("\n%s  收盘 %.2f" % (t, c[i]))
    for H in (20, 60, 120, 250):
        if i + H >= n:
            continue
        seg = c[i + 1:i + H + 1]
        print("   %3d日后: 最大涨幅 %+6.2f%%  最大回撤 %+6.2f%%  终点 %+6.2f%%  是否破前低 %s"
              % (H, (seg.max() / c[i] - 1) * 100, (seg.min() / c[i] - 1) * 100,
                 (c[i + H] / c[i] - 1) * 100,
                 "是" if seg.min() < c[max(0, i - 119):i + 1].min() else "否"))
