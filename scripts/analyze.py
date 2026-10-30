# -*- coding: utf-8 -*-
"""L1 基准率 + L2 条件概率（贝叶斯收缩）+ 同构性（价格形态层）。

严格遵循 预注册清单_2026-10-30.md：
  grid  = G1(20,3%) G2(20,5%) G3(20,10%) G4(60,10%)
  conds = C1..C5，冷却期 60 交易日，先验强度 n0=15
不依赖 scipy（自带不完全 Beta 函数实现）。
输出 data/analysis_result.json
"""
import os, json, math
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(BASE, "data", "399006_daily_tencent.csv")
OUTJ = os.path.join(BASE, "data", "analysis_result.json")

GRID = [("G1", 20, 0.03), ("G2", 20, 0.05), ("G3", 20, 0.10), ("G4", 60, 0.10)]
MAIN = "G2"
COOLDOWN = 60
N0 = 15.0
MAXH = max(h for _, h, _ in GRID)


# ---------------------------------------------------------------- 统计工具
def _betacf(a, b, x):
    MAXIT, EPS, FPMIN = 200, 3e-16, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    cc, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        cc = 1.0 + aa / cc
        if abs(cc) < FPMIN:
            cc = FPMIN
        d = 1.0 / d
        h *= d * cc
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        cc = 1.0 + aa / cc
        if abs(cc) < FPMIN:
            cc = FPMIN
        d = 1.0 / d
        de = d * cc
        h *= de
        if abs(de - 1.0) < EPS:
            break
    return h


def betai(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                  + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1 - x) / b


def beta_ppf(q, a, b):
    lo, hi = 0.0, 1.0
    for _ in range(120):
        mid = (lo + hi) / 2
        if betai(a, b, mid) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - s) / d), min(1.0, (c + s) / d))


def forward(c, i, H):
    """未来 H 日统计；数据不足返回 None"""
    if i + H >= len(c):
        return None
    seg = c[i + 1: i + H + 1]
    return dict(maxgain=float(seg.max() / c[i] - 1),
                maxdd=float(seg.min() / c[i] - 1),
                terminal=float(c[i + H] / c[i] - 1),
                newlow=bool(seg.min() < c[max(0, i - 119): i + 1].min()))


# ---------------------------------------------------------------- 数据
df = pd.read_csv(CSV, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
c = df["close"].values
vol = df["volume"].values
dates = [d.strftime("%Y-%m-%d") for d in df["date"]]
n = len(c)
is_friday = (df["date"].dt.weekday == 4).values

# 周线
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
    if not len(pos):
        continue
    li = pos[-1]
    # 该周已完成：后面还有交易日，或该周最后一天本身就是周五
    complete[li] = bool(li < n - 1 or is_friday[li])

streak_day = np.zeros(n, dtype=int)
for i in range(n):
    j = min(int(week_of[i]), len(wv) - 1)
    streak_day[i] = streak_w[j] if complete[i] else (streak_w[j - 1] if j >= 1 else 0)

roll_max250 = pd.Series(c).rolling(250, min_periods=60).max().values
dd250 = c / roll_max250 - 1
ret60 = np.full(n, np.nan)
ret60[60:] = c[60:] / c[:-60] - 1

i0 = n - 1
cur = dict(
    t0_date=dates[i0], t0_close=float(c[i0]),
    streak_completed=int(streak_day[i0]),
    streak_incl_current=int(streak_w[-1]),
    dd250=float(dd250[i0]), dd_all=float(c[i0] / c.max() - 1),
    peak_all=float(c.max()), peak_all_date=dates[int(np.argmax(c))],
    ret20=float(c[i0] / c[i0 - 20] - 1), ret60=float(ret60[i0]),
    ret120=float(c[i0] / c[i0 - 120] - 1),
    vol20=float(np.std(np.diff(np.log(c))[-20:]) * math.sqrt(252)),
)
seq = int(streak_w[-1])
cur["seq_weeks"] = seq
cur["seq_drop"] = float(wv[-1] / wv[-1 - seq] - 1)
cur["seq_drop_completed"] = float(wv[-2] / wv[-2 - int(streak_w[-2])] - 1) if streak_w[-2] > 0 else None

# ---------------------------------------------------------------- L1
base = {}
for gid, H, Y in GRID:
    rows = [forward(c, i, H) for i in range(n - H)]
    rows = [r for r in rows if r]
    k = sum(1 for r in rows if r["maxgain"] >= Y)
    t = len(rows)
    lo, hi = wilson(k, t)
    term = np.array([r["terminal"] for r in rows])
    base[gid] = dict(H=H, Y=Y, n=t, k=k, p=k / t, ci=[lo, hi],
                     terminal_mean=float(term.mean()), terminal_median=float(np.median(term)),
                     p_positive=float((term > 0).mean()),
                     q05=float(np.percentile(term, 5)), q95=float(np.percentile(term, 95)))

# ---------------------------------------------------------------- L2
def detect(mask):
    out, last = [], -10 ** 9
    for i in range(len(mask)):
        if mask[i] and i - last >= COOLDOWN:
            out.append(i)
            last = i
    return out


masks = {
    "C1": (dd250 <= -0.40) & (np.concatenate([[True], dd250[:-1] > -0.40])),
    "C2": (streak_day >= 4) & (np.nan_to_num(ret60, nan=0.0) <= -0.20),
    "C3": (np.nan_to_num(ret60, nan=0.0) <= -0.25),
    "C4": (streak_day >= 3) & (np.nan_to_num(ret60, nan=0.0) <= -0.12),
    "C5": (streak_day >= 5) & (np.nan_to_num(ret60, nan=0.0) <= -0.25),
}
LABELS = {"C1": "回撤≤−40%（首次触及）", "C2": "连跌≥4周 且 60日≤−20%",
          "C3": "60日≤−25%", "C4": "连跌≥3周 且 60日≤−12%",
          "C5": "连跌≥5周 且 60日≤−25%"}

conds = {}
for cid, m in masks.items():
    all_idx = detect(m)
    usable = [i for i in all_idx if i + MAXH < n]
    rec = dict(id=cid, label=LABELS[cid], n_matched=len(all_idx),
               matches_now=bool(m[i0]), event_dates=[dates[i] for i in usable],
               grids={})
    for gid, H, Y in GRID:
        p0 = base[gid]["p"]
        rows = [(i, forward(c, i, H)) for i in usable]
        rows = [(i, f) for i, f in rows if f]
        cnt = len(rows)
        if cnt == 0:
            rec["grids"][gid] = dict(n=0, k=0, p_raw=None, ci=[None, None],
                                     p_post=p0, cr=[None, None], maxdd_med=None,
                                     terminal_med=None, newlow_p=None, events=[])
            continue
        k = sum(1 for _, f in rows if f["maxgain"] >= Y)
        a, b = N0 * p0, N0 * (1 - p0)
        rec["grids"][gid] = dict(
            n=cnt, k=k, p_raw=k / cnt, ci=list(wilson(k, cnt)),
            p_post=(a + k) / (a + b + cnt),
            cr=[beta_ppf(0.05, a + k, b + cnt - k), beta_ppf(0.95, a + k, b + cnt - k)],
            maxdd_med=float(np.median([f["maxdd"] for _, f in rows])),
            terminal_med=float(np.median([f["terminal"] for _, f in rows])),
            newlow_p=float(np.mean([f["newlow"] for _, f in rows])),
            events=[dict(date=dates[i], **f) for i, f in rows])
    conds[cid] = rec

# ---------------------------------------------------------------- 同构：熊市段（摆动点 30/20）
# 规则：自峰值下跌 >=30% 进入熊市段，自最低点反弹 >=20% 结束该段。
# 这样嵌套下跌（如 2015 崩盘后 2016 年初再跌）会被拆成独立段，而不是被吞进一段。
THR_DOWN, THR_UP = 0.30, 0.20
legs_raw = []
state, peak_i, trough_i = "bull", 0, None
for i in range(1, n):
    if state == "bull":
        if c[i] > c[peak_i]:
            peak_i = i
        if c[i] / c[peak_i] - 1 <= -THR_DOWN:
            state, trough_i = "bear", i
    else:
        if c[i] < c[trough_i]:
            trough_i = i
        if c[i] / c[trough_i] - 1 >= THR_UP:
            legs_raw.append(dict(peak_i=peak_i, trough_i=trough_i, open=False))
            state = "bull"
            peak_i = trough_i + int(np.argmax(c[trough_i:i + 1]))
if state == "bear":
    legs_raw.append(dict(peak_i=peak_i, trough_i=trough_i, open=True))

legs = []
for L in legs_raw:
    p_i, t_i = L["peak_i"], L["trough_i"]
    r = np.diff(np.log(c[p_i:t_i + 1]))
    v_b = float(np.mean(vol[max(0, p_i - 60): p_i + 1]))
    v_a = float(np.mean(vol[max(0, t_i - 60): t_i + 1]))
    legs.append(dict(peak=dates[p_i], trough=dates[t_i], depth=float(c[t_i] / c[p_i] - 1),
                     dur_td=int(t_i - p_i),
                     speed_m=float((c[t_i] / c[p_i] - 1) / max(t_i - p_i, 1) * 20),
                     vol_ann=float(np.std(r) * math.sqrt(252)) if len(r) > 1 else None,
                     vol_shrink=float(v_a / v_b) if v_b else None,
                     open=bool(L["open"]), _pi=int(p_i), _ti=int(t_i)))

# 同位置类比：C1 的每一次「首次触及回撤 -40%」，逐次列出后续路径
# （与 C1 条件完全一致，保证报告内部口径统一）
c1_usable = [i for i in detect(masks["C1"]) if i + MAXH < n]
analogs = []
for i in c1_usable:
    rec = dict(touch_date=dates[i], depth=float(dd250[i]), close=float(c[i]))
    leg = next((L for L in legs if L["_pi"] <= i <= L["_ti"]), None)
    if leg:
        rec["leg_peak"], rec["leg_trough"] = leg["peak"], leg["trough"]
        rec["leg_depth"] = leg["depth"]
    for H in (20, 60, 120):
        f = forward(c, i, H)
        rec["f%d" % H] = ({k: f[k] for k in ("maxgain", "maxdd", "terminal", "newlow")}
                          if f else None)
    analogs.append(rec)

# C5「无先例」的边界诊断：把门槛放宽 1 个百分点会掉出什么
alt_mask = (streak_day >= 5) & (np.nan_to_num(ret60, nan=0.0) <= -0.24)
c5_alt = [i for i in detect(alt_mask) if i + MAXH < n]

# 形态向量距离：当前段与历史各段的相似度（等权 z 分数，ad hoc 但可复现）
feat = np.array([[abs(L["depth"]), math.log(L["dur_td"] + 1),
                  L["vol_ann"] or 0.0, L["vol_shrink"] or 0.0] for L in legs])
z = (feat - feat.mean(0)) / feat.std(0, ddof=1)
dist = np.sqrt(((z[:-1] - z[-1]) ** 2).sum(1))
similarity = [dict(peak=legs[i]["peak"], trough=legs[i]["trough"],
                   depth=legs[i]["depth"], dur_td=legs[i]["dur_td"],
                   speed_m=legs[i]["speed_m"], vol_ann=legs[i]["vol_ann"],
                   vol_shrink=legs[i]["vol_shrink"], dist=float(dist[i]))
              for i in np.argsort(dist)]

for L in legs:
    L.pop("_pi", None)
    L.pop("_ti", None)

result = dict(
    meta=dict(generated=pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), n_days=n,
              first=dates[0], last=dates[-1], cooldown=COOLDOWN, n0=N0, main=MAIN,
              grid=[dict(id=g, H=h, Y=y) for g, h, y in GRID]),
    current=cur, base=base, conditions=conds, legs=legs, analogs=analogs,
    similarity=similarity,
    c5_boundary=dict(threshold=-0.25, alt_threshold=-0.24,
                     alt_dates=[dates[i] for i in c5_alt], alt_n=len(c5_alt)))

with open(OUTJ, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=float)

# ---------------------------------------------------------------- 摘要
print("t0 = %s  %.2f" % (cur["t0_date"], cur["t0_close"]))
print("  完整下跌周 %d（含本周 %d），该段 %.2f%%；已确认段 %.2f%%"
      % (cur["streak_completed"], cur["streak_incl_current"],
         cur["seq_drop"] * 100, (cur["seq_drop_completed"] or 0) * 100))
print("  250日回撤 %.2f%%  历史最高回撤 %.2f%%  vol20 %.1f%%"
      % (cur["dd250"] * 100, cur["dd_all"] * 100, cur["vol20"] * 100))
print("\n[L1] 基准率")
for gid, H, Y in GRID:
    b = base[gid]
    print("  %s H=%2d Y=%2.0f%%: %4d/%4d = %5.1f%%  CI[%.1f,%.1f]  终点中位 %+.2f%%  P(>0)=%.1f%%"
          % (gid, H, Y * 100, b["k"], b["n"], b["p"] * 100, b["ci"][0] * 100,
             b["ci"][1] * 100, b["terminal_median"] * 100, b["p_positive"] * 100))

print("\n[L2] 主口径 G2（20日/5%）  收缩前 -> 收缩后")
for cid in ("C1", "C2", "C3", "C4", "C5"):
    g = conds[cid]["grids"][MAIN]
    if g["n"] == 0:
        print("  %s %-22s 无先例（匹配 %d 次，无前瞻数据）" % (cid, conds[cid]["label"], conds[cid]["n_matched"]))
        continue
    print("  %s %-22s n=%2d k=%2d  %5.1f%% -> %5.1f%%  CI[%.1f,%.1f] CR[%.1f,%.1f]  证据 %+.1fpp"
          % (cid, conds[cid]["label"], g["n"], g["k"], g["p_raw"] * 100, g["p_post"] * 100,
             g["ci"][0] * 100, g["ci"][1] * 100, g["cr"][0] * 100, g["cr"][1] * 100,
             (g["p_post"] - base[MAIN]["p"]) * 100))

print("\n[L2] 收缩后概率矩阵")
line = "  %-5s" % "cond"
for gid, _, _ in GRID:
    line += "%12s" % gid
print(line)
line = "  %-5s" % "base"
for gid, _, _ in GRID:
    line += "%11.1f%%" % (base[gid]["p"] * 100)
print(line)
for cid in ("C1", "C2", "C3", "C4", "C5"):
    line = "  %-5s" % cid
    for gid, _, _ in GRID:
        g = conds[cid]["grids"][gid]
        line += "%12s" % (("%.1f%%" % (g["p_post"] * 100)) if g["n"] else "--")
    print(line)

print("\n[同构] 熊市段（跌幅>=30% 触发，反弹>=20% 结束）")
for L in legs:
    print("  %s -> %s  %6.1f%%  %4dtd  速度 %6.1f%%/月  波动 %4.1f%%  量能 %.2fx%s"
          % (L["peak"], L["trough"], L["depth"] * 100, L["dur_td"], L["speed_m"] * 100,
             (L["vol_ann"] or 0) * 100, L["vol_shrink"] or 0, "  (进行中)" if L["open"] else ""))

print("\n[同构] 同位置类比：每一次「首次触及 250 日回撤 -40%」之后")
for a in analogs:
    f20, f60, f120 = a["f20"], a["f60"], a["f120"]
    print("  %s  段 %s->%s(%.1f%%)  20日终点 %s  60日终点 %s  120日终点 %s  20日最大回撤 %s  创新低 %s"
          % (a["touch_date"], a.get("leg_peak"), a.get("leg_trough"),
             (a.get("leg_depth") or 0) * 100,
             ("%+.1f%%" % (f20["terminal"] * 100)) if f20 else "--",
             ("%+.1f%%" % (f60["terminal"] * 100)) if f60 else "--",
             ("%+.1f%%" % (f120["terminal"] * 100)) if f120 else "--",
             ("%+.1f%%" % (f20["maxdd"] * 100)) if f20 else "--",
             f20["newlow"] if f20 else "--"))

print("\n[边界诊断] C5 门槛 -25%% -> -24%% 会掉出的历史样本：%d 个 %s"
      % (len(c5_alt), [dates[i] for i in c5_alt]))
print("\n[写出] %s" % OUTJ)
