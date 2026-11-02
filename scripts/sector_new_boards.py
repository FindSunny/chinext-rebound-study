# -*- coding: utf-8 -*-
"""补充分析 v2：修正日期对齐后，重算科创板/双创在两个熊底的表现。

关键修正：px（行业，2012 起）与 nb（科创板，2019 起）行数不同，
必须按日期 outer join 后再取位置索引，否则会张冠李戴。
"""
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
px = pd.read_csv(os.path.join(BASE, "data", "sectors_daily.csv"),
                 parse_dates=["date"]).set_index("date")
nb = pd.read_csv(os.path.join(BASE, "data", "new_boards_daily.csv"),
                 parse_dates=["date"]).set_index("date")
alldf = px.join(nb, how="outer").sort_index().ffill()
print("对齐后: %d 行, %d 列 (%s .. %s)" %
      (len(alldf), alldf.shape[1], alldf.index[0].date(), alldf.index[-1].date()))

SECTORS = ["能源", "材料", "工业", "可选消费", "主要消费", "医药", "金融", "信息", "通信", "公用事业"]
NEWB = [c for c in alldf.columns if c not in SECTORS + ["沪深300", "创业板指"]]
print("新增标的:", NEWB)

print("\n" + "=" * 96)
print("【一】2022-04 与 2024-02 熊底后 20 日：把科创板/双创放进来一起排")
print("=" * 96)
for bd in ["2022-04-26", "2024-02-02"]:
    t = int(alldf.index.searchsorted(pd.Timestamp(bd)))
    vals, miss = {}, []
    for nm in SECTORS + NEWB:
        s = alldf[nm].values
        if t + 20 < len(s) and not np.isnan(s[t]) and not np.isnan(s[t + 20]):
            vals[nm] = s[t + 20] / s[t] - 1
        else:
            miss.append(nm)
    order = sorted(vals.items(), key=lambda x: -x[1])
    print("\n  %s（20 个交易日）:" % bd)
    for i, (nm, v) in enumerate(order):
        tag = "  ← 新板块" if nm in NEWB else ""
        print("    %2d. %-10s %+7.1f%%%s" % (i + 1, nm, v * 100, tag))
    if miss:
        print("    （缺数据: %s）" % ", ".join(miss))

print("\n" + "=" * 96)
print("【二】科创板指数在这两个底部之后的走势路径（相对底部收盘）")
print("=" * 96)
for bd in ["2022-04-26", "2024-02-02"]:
    t = int(alldf.index.searchsorted(pd.Timestamp(bd)))
    print("\n  %s 起:" % bd)
    for nm in ["创业板指", "科创50", "科创50ETF", "双创ETF", "创业板50ETF"]:
        if nm not in alldf.columns:
            continue
        s = alldf[nm].values
        if np.isnan(s[t]):
            continue
        row = [s[t + h] / s[t] - 1 if t + h < len(s) else np.nan for h in (5, 10, 20, 60, 120)]
        print("    %-10s " % nm + "  ".join(
            ("%d日%+.1f%%" % (h, v * 100)) if not np.isnan(v) else "%d日 n/a" % h
            for h, v in zip((5, 10, 20, 60, 120), row)))

print("\n【校验】2024-02-02 是政策底，此后 20 日应普涨；若新板块显示下跌即为对齐错误。")
