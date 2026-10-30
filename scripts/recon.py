# -*- coding: utf-8 -*-
"""侦察脚本：只回答两件事
  A. 用户前提是否成立（连跌几周、累计跌幅、所处位置）
  B. 条件概率问题的有效样本量有多少（决定统计上能不能给精度）
不做预测，不建模型。输出供方案文档引用。
"""
import os, csv, math
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(BASE, "data", "399006_daily_tencent.csv")


def load():
    df = pd.read_csv(CSV, parse_dates=["date"])
    df = df.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    return df


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z*z/n
    c = p + z*z/(2*n)
    s = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return ((c - s)/d, (c + s)/d)


def main():
    df = load()
    c = df["close"].values
    d = df["date"].dt.date.values
    n = len(df)
    print(f"样本: {n} 个交易日  {d[0]} .. {d[-1]}   最新收盘 {c[-1]:.2f}")
    print("=" * 78)

    # ---------- A. 用户前提 ----------
    print("\n[A] 当前位置")
    w = df.set_index("date")["close"].resample("W-FRI").last().dropna()
    print("  最近 12 周收盘（周线）:")
    for dt, v in w.tail(12).items():
        print(f"    {dt.date()}  {v:8.2f}")

    wr = w.pct_change().dropna()
    streak = 0
    for v in wr.values[::-1]:
        if v < 0:
            streak += 1
        else:
            break
    print(f"  连续下跌周数: {streak}")
    if streak:
        print(f"  该段累计: {(w.iloc[-1]/w.iloc[-1-streak]-1)*100:.2f}%")

    for lb in (20, 60, 120, 250):
        if n > lb:
            r = c[-1]/c[-1-lb]-1
            allr = c[lb:]/c[:-lb]-1
            pct = (allr < r).mean()*100
            print(f"  近{lb:3d}日涨跌: {r*100:7.2f}%   历史分位: {pct:5.1f}%")

    peak_all = c.max(); pk_i = int(np.argmax(c))
    print(f"  历史最高 {peak_all:.2f} ({d[pk_i]})  当前距最高: {(c[-1]/peak_all-1)*100:.2f}%")
    for lb in (250, 500):
        seg = c[-lb:]; i = int(np.argmax(seg))
        print(f"  近{lb}日高点 {seg[i]:.2f} ({d[n-lb+i]})  回撤: {(c[-1]/seg[i]-1)*100:.2f}%")

    # 波动率状态
    ret = np.diff(np.log(c))
    vol20 = ret[-20:].std()*math.sqrt(252)*100
    vol_all = pd.Series(ret).rolling(20).std()*math.sqrt(252)*100
    print(f"  20日实现波动率(年化): {vol20:.1f}%   历史分位: {(vol_all.dropna() < vol20).mean()*100:.1f}%")

    # ---------- B. 有效样本量 ----------
    print("\n[B] 条件样本量侦察：'连跌K周' + '近M日跌幅<=X' 之后，20日内反弹>=Y%")
    print("    （冷却期 60 个交易日，避免重叠事件重复计数）")
    print(f"    {'K周':>3} {'M日':>4} {'X%':>6} {'Y%':>4} | {'事件数':>4} {'反弹数':>5} {'条件概率':>8} {'95%CI':>16}")
    print("    " + "-"*76)

    wvals = w.values
    wdates = w.index
    # 周线 -> 对应到日线位置：按周最后一个交易日
    wk_end_idx = []
    for dt in wdates:
        pos = df["date"].searchsorted(pd.Timestamp(dt), side="right") - 1
        wk_end_idx.append(min(pos, n-1))
    wk_end_idx = np.array(wk_end_idx)

    rows = []
    for K in (3, 4, 5, 6):
        for M, X in ((20, -8), (60, -12), (60, -15), (60, -20)):
            for Y in (5, 10):
                hits = []
                last = -999
                for i in range(max(M, 80), n):
                    if i - last < 60:
                        continue
                    wi = np.searchsorted(wk_end_idx, i, side="right") - 1
                    if wi < K:
                        continue
                    # 连续 K 周为负
                    ok = True
                    for j in range(K):
                        a, b = wk_end_idx[wi-j], wk_end_idx[wi-j-1]
                        if b < 0 or not (wvals[wi-j] < wvals[wi-j-1]):
                            ok = False
                            break
                    if not ok:
                        continue
                    if c[i]/c[i-M]-1 > X/100:
                        continue
                    fwd = c[i+1:i+21]
                    if len(fwd) < 20:
                        continue
                    hits.append((i, (fwd.max()/c[i]-1)*100))
                    last = i
                cnt = len(hits)
                if cnt == 0:
                    rows.append((K, M, X, Y, 0, 0, float("nan"), float("nan"), float("nan")))
                    print(f"    {K:>3} {M:>4} {X:>6} {Y:>4} | {0:>4} {0:>5} {'--':>8} {'--':>16}")
                    continue
                kk = sum(1 for _, g in hits if g >= Y)
                lo, hi = wilson(kk, cnt)
                # 先跌后涨：窗口内最大回撤
                worst = np.mean([ (c[i+1:i+21].min()/c[i]-1)*100 for i, _ in hits ])
                rows.append((K, M, X, Y, cnt, kk, kk/cnt, lo, hi))
                print(f"    {K:>3} {M:>4} {X:>6} {Y:>4} | {cnt:>4} {kk:>5} {kk/cnt*100:>7.1f}% "
                      f"[{lo*100:>5.1f}%,{hi*100:>5.1f}%]  窗口内平均最大回撤 {worst:.1f}%")

    # 无条件基准率
    print("\n[B2] 无条件基准率（全样本任意一天起算，20日内最大涨幅>=Y 的比例）")
    for Y in (3, 5, 10, 15):
        gains = []
        for i in range(n-20):
            gains.append((c[i+1:i+21].max()/c[i]-1)*100)
        gains = np.array(gains)
        k = int((gains >= Y).sum()); t = len(gains)
        lo, hi = wilson(k, t)
        print(f"    Y={Y:>2}% : {k:>4}/{t} = {k/t*100:5.1f}%   95%CI [{lo*100:.1f}%, {hi*100:.1f}%]")

    # 无条件：未来20日收益分布
    fwd20 = np.array([c[i+20]/c[i]-1 for i in range(n-20)])*100
    print(f"\n[B3] 未来20日收益率分布(全样本): 均值 {fwd20.mean():.2f}%  中位 {np.median(fwd20):.2f}%  "
          f"P(>0)={100*(fwd20>0).mean():.1f}%  5%分位 {np.percentile(fwd20,5):.1f}%  95%分位 {np.percentile(fwd20,95):.1f}%")

    out = os.path.join(BASE, "data", "recon_summary.txt")
    print(f"\n[完成] 关键数字已打印，明细见 {out}")


if __name__ == "__main__":
    main()
