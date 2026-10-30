# -*- coding: utf-8 -*-
"""生成《创业板反弹概率（快速版）》单文件 HTML 报告。"""
import os, json, math
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = os.path.join(BASE, "data", "analysis_result.json")
OUT = os.path.join(BASE, "out", "创业板反弹概率_快速版_2026-10.html")

PAPER, INK, RULE = "#f7f5f1", "#17181a", "#d9d4cb"
TEAL, RUST, GOLD, MUTED = "#0b6e6e", "#b4462f", "#a67c1f", "#6f6a61"

R = json.load(open(J, encoding="utf-8"))
cur, base, conds = R["current"], R["base"], R["conditions"]
legs, analogs, sim = R["legs"], R["analogs"], R["similarity"]


def pct(x, d=1, sign=False):
    if x is None:
        return "—"
    return ("%+.*f%%" if sign else "%.*f%%") % (d, x * 100)


# ---------------------------------------------------------------- 图1 概率
def chart_prob():
    W, H = 860, 342
    L, Rw, T, B = 268, 118, 34, 58
    rows = [("无条件基准率（不看任何信号）", base["G2"]["p"], base["G2"]["ci"], 3963, "base"),
            ("C1 回撤首次≤−40%", conds["C1"]["grids"]["G2"]["p_post"],
             conds["C1"]["grids"]["G2"]["cr"], conds["C1"]["grids"]["G2"]["n"], "cond"),
            ("C2 连跌≥4周＋60日≤−20%", conds["C2"]["grids"]["G2"]["p_post"],
             conds["C2"]["grids"]["G2"]["cr"], conds["C2"]["grids"]["G2"]["n"], "thin"),
            ("C3 60日≤−25%", conds["C3"]["grids"]["G2"]["p_post"],
             conds["C3"]["grids"]["G2"]["cr"], conds["C3"]["grids"]["G2"]["n"], "thin"),
            ("C4 连跌≥3周＋60日≤−12%", conds["C4"]["grids"]["G2"]["p_post"],
             conds["C4"]["grids"]["G2"]["cr"], conds["C4"]["grids"]["G2"]["n"], "cond")]
    pw = W - L - Rw

    def x(p):
        return L + pw * (p / 100.0)

    P = [f'<line x1="{x(0):.1f}" y1="{T-10}" x2="{x(0):.1f}" y2="{H-B}" stroke="{RULE}"/>']
    for p in (25, 50, 75, 100):
        P.append(f'<line x1="{x(p):.1f}" y1="{T-10}" x2="{x(p):.1f}" y2="{H-B}" stroke="{RULE}" stroke-width="1"/>')
        P.append(f'<text x="{x(p):.1f}" y="{H-B+19}" text-anchor="middle" class="ax">{p}%</text>')
    bp = base["G2"]["p"] * 100
    P.append(f'<line x1="{x(bp):.1f}" y1="{T-16}" x2="{x(bp):.1f}" y2="{H-B+2}" stroke="{GOLD}" stroke-width="1.3" stroke-dasharray="5 3"/>')
    P.append(f'<text x="{x(bp):.1f}" y="{T-22}" text-anchor="middle" class="ax gold">基准 {bp:.1f}%</text>')

    rh = (H - B - T) / len(rows)
    for i, (label, pv, ci, nn, kind) in enumerate(rows):
        cy = T + rh * i + rh / 2
        col = TEAL if kind == "base" else (RUST if kind == "cond" else "#b9b2a6")
        P.append(f'<text x="{L-14}" y="{cy+4:.1f}" text-anchor="end" class="lbl">{label}</text>')
        if ci[0] is not None and pv is not None:
            P.append(f'<line x1="{x(ci[0]*100):.1f}" y1="{cy:.1f}" x2="{x(ci[1]*100):.1f}" y2="{cy:.1f}" stroke="{col}" stroke-width="1.5" opacity=".5"/>')
            for e in ci:
                P.append(f'<line x1="{x(e*100):.1f}" y1="{cy-6:.1f}" x2="{x(e*100):.1f}" y2="{cy+6:.1f}" stroke="{col}" stroke-width="1.5" opacity=".5"/>')
        fill = col if kind == "base" else ("none" if kind == "thin" else col)
        P.append(f'<circle cx="{x(pv*100):.1f}" cy="{cy:.1f}" r="5.2" fill="{fill}" stroke="{col}" stroke-width="1.7"/>')
        P.append(f'<text x="{W-Rw+12}" y="{cy-1:.1f}" class="ax val">{pv*100:.1f}%</text>')
        P.append(f'<text x="{W-Rw+12}" y="{cy+12:.1f}" class="ax n">n={nn}</text>')
    return f'<svg viewBox="0 0 {W} {H}" class="chart">{chr(10).join(P)}</svg>'


# ---------------------------------------------------------------- 图2 同位置类比
def chart_analogs():
    W, H = 860, 330
    L, Rw, T, B = 140, 30, 30, 74
    hs = [("f20", "20 日", TEAL), ("f60", "60 日", GOLD), ("f120", "120 日", "#8a8378")]
    vals = []
    for a in analogs:
        for k, _, _ in hs:
            if a.get(k):
                vals.append(a[k]["terminal"] * 100)
    lo, hi = min(vals + [0]) - 4, max(vals + [0]) + 4

    def y(v):
        return T + (H - T - B) * (1 - (v - lo) / (hi - lo))

    pw = W - L - Rw
    gw = pw / len(analogs)
    P = [f'<line x1="{L}" y1="{y(0):.1f}" x2="{W-Rw}" y2="{y(0):.1f}" stroke="#a8a29a" stroke-width="1.2"/>']
    for g in range(-2, 5):
        v = g * 5
        if lo < v < hi:
            P.append(f'<line x1="{L}" y1="{y(v):.1f}" x2="{W-Rw}" y2="{y(v):.1f}" stroke="{RULE}" stroke-width="1"/>')
            P.append(f'<text x="{L-10}" y="{y(v)+4:.1f}" text-anchor="end" class="ax">{v}%</text>')
    bw = gw / (len(hs) + 2)
    for gi, a in enumerate(analogs):
        gx = L + gw * gi
        for hi_, (k, _, col) in enumerate(hs):
            f = a.get(k)
            if not f:
                continue
            v = f["terminal"] * 100
            t, bbase = min(y(0), y(v)), max(y(0), y(v))
            bx = gx + bw * (hi_ + 1)
            P.append(f'<rect x="{bx:.1f}" y="{t:.1f}" width="{bw*0.82:.1f}" height="{max(bbase-t,1.4):.1f}" fill="{col}" opacity="0.85"/>')
            lab = ("%+.1f%%" % v) if abs(v) < 1 else ("%+.0f%%" % v)
            P.append(f'<text x="{bx+bw*0.41:.1f}" y="{(t-4) if v>=0 else (bbase+12):.1f}" text-anchor="middle" class="ax sm">{lab}</text>')
        P.append(f'<text x="{gx+gw/2:.1f}" y="{H-B+22}" text-anchor="middle" class="lbl">{a["touch_date"]}</text>')
    lg = "  ".join([f'<tspan fill="{c}">■</tspan> {n}' for _, n, c in hs])
    P.append(f'<text x="{L}" y="{T-8}" class="ax">{lg}</text>')
    return f'<svg viewBox="0 0 {W} {H}" class="chart">{chr(10).join(P)}</svg>'


# ---------------------------------------------------------------- 图3 形态散点
def chart_legs():
    W, H = 860, 320
    L, Rw, T, B = 64, 158, 44, 46
    xs = [lg["dur_td"] for lg in legs]
    ys = [abs(lg["depth"]) * 100 for lg in legs]
    xmax = max(xs) * 1.06
    ylo, yhi = min(ys) - 1.5, max(ys) + 1.5

    def X(v):
        return L + (W - L - Rw) * (v / xmax)

    def Y(v):
        return T + (H - T - B) * (1 - (v - ylo) / (yhi - ylo))

    P = []
    g = int(math.ceil(ylo / 5.0)) * 5
    while g < yhi:
        P.append(f'<line x1="{L}" y1="{Y(g):.1f}" x2="{W-Rw}" y2="{Y(g):.1f}" stroke="{RULE}"/>')
        P.append(f'<text x="{L-8}" y="{Y(g)+4:.1f}" text-anchor="end" class="ax">−{g}%</text>')
        g += 5
    for x0 in range(0, int(xmax) + 1, 100):
        P.append(f'<text x="{X(x0):.1f}" y="{H-B+19}" text-anchor="middle" class="ax">{x0}</text>')

    cd = abs(cur["dd_all"]) * 100
    P.append(f'<line x1="{L}" y1="{Y(cd):.1f}" x2="{W-Rw}" y2="{Y(cd):.1f}" stroke="{RUST}" stroke-width="1" stroke-dasharray="3 4" opacity=".5"/>')

    # 只标注有代表性的点，其余靠上表查阅
    label_set = set()
    if legs:
        by_dur = sorted(range(len(legs)), key=lambda i: legs[i]["dur_td"])
        label_set.add(by_dur[0])                      # 最短（最快崩盘）
        label_set.add(by_dur[-1])                     # 最长（慢熊）
        deepest = max(range(len(legs)), key=lambda i: abs(legs[i]["depth"]))
        label_set.add(deepest)
        cur_i = next((i for i, lg in enumerate(legs) if lg["open"]), None)
        if cur_i is not None:
            label_set.add(cur_i)
            second_fast = by_dur[1] if len(by_dur) > 1 else None
            if second_fast is not None:
                label_set.add(second_fast)

    # 图上只标当前点，其余点与上表一一对应，避免标注互相压线
    for i, lg in enumerate(legs):
        is_cur = lg["open"]
        cx, cy = X(lg["dur_td"]), Y(abs(lg["depth"]) * 100)
        col = RUST if is_cur else TEAL
        P.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{7 if is_cur else 4.6}" '
                 f'fill="{col if is_cur else "none"}" stroke="{col}" stroke-width="1.7" opacity="{1 if is_cur else .85}"/>')
        if is_cur:
            P.append(f'<text x="{cx+11:.1f}" y="{cy-9:.1f}" class="ax cur">当前 2026-06</text>')
    P.append(f'<text x="{L}" y="{T-24}" class="ax">横轴：跌了多久（交易日）　纵轴：跌了多深　→ 越靠左上＝越快越急</text>')
    P.append(f'<text x="{W-Rw+14}" y="{Y(cd)+4:.1f}" class="ax rust">当前 −{cd:.1f}%</text>')
    return f'<svg viewBox="0 0 {W} {H}" class="chart">{chr(10).join(P)}</svg>'


def cjk_quotes(html):
    """把正文里的 ASCII 双引号成对替换为中文弯引号；跳过标签内部与 script/style。"""
    import re
    parts = re.split(r"(<[^>]*>)", html)
    out, in_code = [], False
    for seg in parts:
        if seg.startswith("<"):
            low = seg.lower()
            if low.startswith("<script") or low.startswith("<style"):
                in_code = True
            elif low.startswith("</script") or low.startswith("</style"):
                in_code = False
            out.append(seg)
            continue
        if in_code:
            out.append(seg)
            continue
        buf, opening = [], True
        for ch in seg:
            if ch == chr(34):
                buf.append(chr(0x201C) if opening else chr(0x201D))
                opening = not opening
            else:
                buf.append(ch)
        out.append("".join(buf))
    return "".join(out)


def main():
    c1 = conds["C1"]["grids"]["G2"]
    c4 = conds["C4"]["grids"]["G2"]
    b2 = base["G2"]
    c1_10 = conds["C1"]["grids"]["G3"]
    c1_60 = conds["C1"]["grids"]["G4"]

    css = """
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:P;color:IK;font:16px/1.78 -apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;-webkit-font-smoothing:antialiased}
a{color:TL;text-decoration:none;border-bottom:1px solid rgba(11,110,110,.28)}a:hover{border-bottom-color:TL}
.wrap{display:flex;max-width:1240px;margin:0 auto;gap:44px;padding:0 28px}
#toc{position:sticky;top:0;align-self:flex-start;width:198px;flex:0 0 198px;height:100vh;overflow:auto;padding:32px 0;font-size:13.5px}
#toc .tt{font-size:11px;letter-spacing:.14em;color:MU;margin-bottom:14px}
#toc a{display:block;color:#5c5750;border:0;padding:5px 0 5px 11px;border-left:2px solid RU;line-height:1.45}
#toc a.on{color:IK;border-left-color:TL;font-weight:600}#toc a:hover{color:TL}
main{flex:1 1 auto;min-width:0;padding:0 0 110px}
#bar{position:fixed;top:0;left:0;height:2px;background:TL;width:0;z-index:99}
.cover{min-height:94vh;display:flex;flex-direction:column;justify-content:center;border-bottom:1px solid RU;padding:56px 0 44px}
.kicker{font-size:12px;letter-spacing:.2em;color:RU_;margin-bottom:20px}
h1{font-size:clamp(29px,4.2vw,47px);line-height:1.18;margin:0 0 18px;letter-spacing:-.02em}
.sub{font-size:clamp(15.5px,1.5vw,19px);color:#4a453f;line-height:1.72;max-width:44em;margin:0 0 30px}
.meta{display:flex;flex-wrap:wrap;gap:24px;font-size:13px;color:MU;border-top:1px solid RU;padding-top:18px}
.meta div{white-space:nowrap}
.meta b{color:IK;font-weight:600;display:block;font-size:15px;font-variant-numeric:tabular-nums}
h2{font-size:23px;margin:60px 0 6px;font-weight:700;letter-spacing:-.01em}
h2 .num{font-size:12px;letter-spacing:.16em;color:RU_;display:block;margin-bottom:8px;font-weight:600}
h3{font-size:16.5px;margin:30px 0 8px;font-weight:650}
p{margin:13px 0}.lead{font-size:17.5px;color:#332f2a;line-height:1.8}
hr.sec{border:0;border-top:1px solid RU;margin:0}
.verdict{background:#fff;border:1px solid RU;border-left:3px solid RU_;padding:20px 24px;margin:26px 0}
.verdict .h{font-size:11px;letter-spacing:.16em;color:RU_;margin-bottom:10px;font-weight:600}
.note{background:rgba(11,110,110,.055);border:1px solid rgba(11,110,110,.18);padding:16px 20px;margin:22px 0;font-size:15px}
.note .h{font-size:11px;letter-spacing:.16em;color:TL;margin-bottom:6px;font-weight:600}
.warn{background:rgba(166,124,31,.07);border:1px solid rgba(166,124,31,.25);padding:16px 20px;margin:22px 0;font-size:15px}
.warn .h{font-size:11px;letter-spacing:.16em;color:#7d5c14;margin-bottom:6px;font-weight:600}
table{width:100%;border-collapse:collapse;margin:18px 0;font-size:14px}
th{text-align:left;font-size:11.5px;letter-spacing:.06em;color:MU;font-weight:600;border-bottom:1.5px solid #c9c3b9;padding:8px 9px 8px 0;white-space:nowrap}
td{padding:9px 9px 9px 0;border-bottom:1px solid #e6e1d8;vertical-align:top;font-variant-numeric:tabular-nums}
.num{text-align:right;white-space:nowrap}
.ctr{text-align:center}
tr.hi td{background:rgba(180,70,47,.07)}
.neg{color:RU_} .pos{color:TL}
.kpi{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:24px 0}
.kpi div{border:1px solid RU;background:#fff;padding:15px 16px}
.kpi .v{font-size:26px;font-weight:700;letter-spacing:-.02em;font-variant-numeric:tabular-nums;line-height:1.2}
.kpi .l{font-size:12px;color:MU;margin-top:5px;line-height:1.45}
.kpi .v.r{color:RU_} .kpi .v.t{color:TL}
.chart{width:100%;height:auto;display:block;margin:8px 0 2px;overflow:visible}
.chart .ax{font-size:11px;fill:MU}
.chart .ax.sm{font-size:10px}
.chart .lbl{font-size:12.5px;fill:#3a3630}.chart .val{font-size:12.5px;fill:#3a3630;font-weight:600}
.chart .n{fill:MU}.chart .gold{fill:GO}.chart .rust{fill:RU_}.chart .cur{font-weight:700;fill:RU_}
figcaption{font-size:12.5px;color:MU;margin:2px 0 24px}
.fn{font-size:12px;color:MU;margin:-4px 0 20px}
ol.steps{counter-reset:s;list-style:none;padding:0;margin:18px 0}
ol.steps>li{counter-increment:s;position:relative;padding:14px 0 14px 44px;border-bottom:1px solid #e6e1d8}
ol.steps>li::before{content:counter(s);position:absolute;left:0;top:14px;width:25px;height:25px;border:1px solid TL;color:TL;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600}
ol.steps .t{font-weight:650;margin-bottom:3px}ol.steps .d{color:#4a453f;font-size:14.5px}
ul.tight{margin:10px 0;padding-left:20px}ul.tight li{margin:7px 0}
footer{border-top:1px solid RU;padding:28px 0 56px;font-size:12.5px;color:MU;line-height:1.7}
@media (max-width:900px){.wrap{flex-direction:column;padding:0 16px;gap:0}#toc{position:static;width:100%;flex:none;height:auto;padding:16px 0;border-bottom:1px solid RU}#toc a{display:inline-block;border-left:0;border-bottom:2px solid transparent;padding:3px 9px 3px 0}#toc a.on{border-bottom-color:TL}.cover{min-height:auto;padding:36px 0 28px}.kpi{grid-template-columns:repeat(2,1fr)}table{font-size:12.5px}h2{margin-top:42px}}
@media print{#toc,#bar{display:none}body{background:#fff;font-size:10.5pt}.wrap{display:block;max-width:none;padding:0}main{padding:0}.cover{min-height:auto;page-break-after:always}h2{page-break-after:avoid;margin-top:20pt}table,.chart,.verdict,.note,.warn,.kpi{page-break-inside:avoid}@page{size:A4;margin:15mm 13mm}}
"""
    css = (css.replace("PAPER", PAPER).replace("PAPER", PAPER).replace("IK", INK)
              .replace("TL", TEAL).replace("MU", MUTED).replace("RU_", RUST)
              .replace("RU", RULE).replace("GO", GOLD).replace("P;", PAPER + ";"))
    css = css.replace("background:P;", "background:%s;" % PAPER)

    secs = [("s1", "01 现在的位置"), ("s2", "02 概率结论"), ("s3", "03 同位置类比"),
            ("s4", "04 形态同构性"), ("s5", "05 最近的那一次"), ("s6", "06 对加仓的含义"),
            ("s7", "07 失效条件"), ("s8", "08 方法与声明")]
    toc = "".join('<a href="#%s">%s</a>' % (i, t) for i, t in secs)

    # 同位置类比表
    def leg_depth_for(a):
        d = a["touch_date"]
        inside = [lg for lg in legs if lg["peak"] <= d <= lg["trough"]]
        if inside:
            return pct(inside[0]["depth"]), ""
        prev = [lg for lg in legs if lg["trough"] < d]
        if prev:
            return pct(prev[-1]["depth"]), "†"
        return "—", ""

    rows_a = ""
    for a in analogs:
        f20, f60, f120 = a["f20"], a["f60"], a["f120"]
        hit = "是" if f20 and f20["maxgain"] >= 0.05 else "否"
        ldep, mark = leg_depth_for(a)
        rows_a += (
            '<tr><td>%s</td><td class="num">%s%s</td><td class="ctr">%s</td>'
            '<td class="num %s">%s</td><td class="num %s">%s</td><td class="num %s">%s</td>'
            '<td class="num %s">%s</td><td class="ctr">%s</td></tr>' % (
                a["touch_date"], ldep, mark, hit,
                "pos" if f20["maxgain"] >= 0.05 else "neg", pct(f20["maxgain"], 1, True),
                "neg" if f20["maxdd"] < 0 else "pos", pct(f20["maxdd"], 1, True),
                "neg" if f60 and f60["terminal"] < 0 else "pos", pct(f60["terminal"], 1, True) if f60 else "—",
                "neg" if f120 and f120["terminal"] < 0 else "pos", pct(f120["terminal"], 1, True) if f120 else "—",
                "是" if f20["newlow"] else "否"))

    # 形态段表
    rows_l = ""
    for lg in legs:
        rows_l += ('<tr class="%s"><td>%s → %s</td><td class="num neg">%s</td><td class="num">%d</td>'
                   '<td class="num">%s</td><td class="num">%s</td><td class="num">%.2fx</td></tr>'
                   % ("hi" if lg["open"] else "", lg["peak"], lg["trough"],
                      pct(lg["depth"]), lg["dur_td"], pct(lg["speed_m"]),
                      pct(lg["vol_ann"]), lg["vol_shrink"] or 0))

    # 相似度前三
    top3 = sim[:3]
    sim_txt = "、".join("%s（%s，%s）" % (s["peak"][:7], pct(s["depth"]), "%d 日" % s["dur_td"]) for s in top3)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>创业板反弹概率 · 快速版 · 2026-10</title>
<style>{css}</style></head>
<body><div id="bar"></div>
<div class="wrap">
<nav id="toc"><div class="tt">目录</div>{toc}</nav>
<main>

<header class="cover">
  <div class="kicker">快 速 版 · L1 + L2 + 形态同构</div>
  <h1>反弹概率约五成，<br>但"见底"的证据不足</h1>
  <p class="sub">按你定的口径（20 个交易日内收盘反弹 ≥5%），概率中枢落在 <b>49%</b> 附近，可信区间 31%–68%。20 日维度历史确实偏向给一次反弹；但拉到 60 日，四次历史类比里有三次是负收益。<b>短线的"会弹"和中期的"见底"是两个问题，这份报告把它们分开答。</b></p>
  <div class="meta">
    <div><b>{cur['t0_close']:,.2f}</b>基准收盘（{cur['t0_date']}）</div>
    <div><b>−{abs(cur['dd_all'])*100:.1f}%</b>距历史高点</div>
    <div><b>{cur['streak_completed']}</b>完整下跌周</div>
    <div><b>3,983</b>交易日样本</div>
  </div>
</header>

<section id="s1">
<h2><span class="num">0 1</span>现在的位置：历史第三深</h2>
<p class="lead">先把口径校准。你在昨天那份方案里看到的"连跌 6 周"包含了本周尚未收盘的点位；严格按完整周计算，截至 10-29 收盘是 <b>5 个完整下跌周、累计 −20.42%</b>，含本周至今则为 6 周、−25.35%。这个区别在条件匹配里很重要，因为未完成的周带着未来信息。</p>
<div class="kpi">
  <div><div class="v r">−{abs(cur['dd_all'])*100:.1f}%</div><div class="l">距历史高点 4,371.99（2026-06-25），16 年第三深</div></div>
  <div><div class="v r">{cur['streak_completed']}</div><div class="l">完整下跌周数（第 6 周待今日收盘确认）</div></div>
  <div><div class="v r">{pct(cur['ret20'],1,True)}</div><div class="l">近 20 日，历史第 0.6 百分位</div></div>
  <div><div class="v t">{cur['vol20']*100:.0f}%</div><div class="l">20 日年化波动率，历史第 83 百分位</div></div>
</div>
<p>把它放回 16 年：这个回撤排第三深，前面只有 2015-06→2018-10（−69.7%）和 2010-12→2012-12（−51.9%）。按摆动点规则拆出来的 9 段熊市里，<b>当前的下跌速度（−10.1%/月）显著快于任何一段慢熊（−1.6 至 −7.3%/月），但慢于 2015 年 6–7 月的崩塌（−35.6%/月）</b>。</p>
</section>

<hr class="sec">
<section id="s2">
<h2><span class="num">0 2</span>概率：基准率之外，证据很薄</h2>
<p>主口径 P(20 日 / ≥5%) 的答案分三档，取决于你愿意相信哪一层：</p>
<table>
<thead><tr><th>口径</th><th class="num">样本</th><th class="num">原始命中</th><th class="num">收缩后概率</th><th class="num">90% 可信区间</th><th class="num">相对基准</th></tr></thead>
<tbody>
<tr><td>无条件基准率（什么都不看）</td><td class="num">3,963</td><td class="num">42.2%</td><td class="num">42.2%</td><td class="num">40.7–43.8%</td><td class="num">—</td></tr>
<tr class="hi"><td><b>C1 回撤首次 ≤−40%</b>（最贴近当前形态）</td><td class="num">4</td><td class="num">3/4 = 75.0%</td><td class="num"><b>49.1%</b></td><td class="num">30.7–67.6%</td><td class="num pos">+6.9pp</td></tr>
<tr><td>C2 连跌≥4周 且 60日≤−20%</td><td class="num">3</td><td class="num">3/3 = 100%</td><td class="num">51.8%</td><td class="num">32.8–70.6%</td><td class="num pos">+9.6pp</td></tr>
<tr><td>C3 60日≤−25%</td><td class="num">5</td><td class="num">3/5 = 60.0%</td><td class="num">46.7%</td><td class="num">28.9–64.8%</td><td class="num pos">+4.4pp</td></tr>
<tr><td>C4 连跌≥3周 且 60日≤−12%（宽口径）</td><td class="num">16</td><td class="num">11/16 = 68.8%</td><td class="num">55.9%</td><td class="num">41.2–70.2%</td><td class="num pos">+13.7pp</td></tr>
<tr><td>C5 连跌≥5周 且 60日≤−25%</td><td class="num">0</td><td class="num">无先例</td><td class="num">退回基准</td><td class="num">—</td><td class="num">—</td></tr>
</tbody></table>
{chart_prob()}
<figcaption>贝叶斯收缩前后对比。原始命中率从 60% 到 100% 不等，收缩后全部收敛到 47%–56%——因为样本量实在太少（n=3 至 16）。金色虚线是无条件基准率 42.2%。</figcaption>

<p><b>C5 是最扎眼的一条：条件完全对得上今天，但历史上一次都没出现过。</b>我做了边界诊断：把 60 日跌幅门槛从 −25% 放宽到 −24%，仍然是 0 个。原因是两个条件在 16 年里从未同时满足——2026 年之前，103 个"连跌≥5 周"的日子里，60 日跌幅最深的是 2012-02-01 的 −23.69%；而 74 个"60 日跌超 24%"的日子里，连跌周数最多也只有 3 周（2015 年 8–9 月，那是急跌不是阴跌）。<b>你现在的状态，是 16 年里最极端的那一种组合，没有先例可依。</b></p>

<div class="verdict">
<div class="h">如 果 只 记 一 个 数 字</div>
<p>主口径 <b>P(20 日内反弹 ≥5%) ≈ 49%，区间 31%–68%</b>。把它读成"五五开、略偏正面"是合理的；读成"大概率见底"是错的。</p>
<p>敏感性：同样的条件下，<b>P(20 日内 ≥10%) 收缩后为 31.6%</b>（基准 20.0%），<b>P(60 日内 ≥10%) 为 49.4%</b>（基准 42.6%）。门槛越严，优势越薄——1 个月里给你 5% 的概率确实高于无条件的市场常态，但给你 10% 的概率就没那么突出了。</p>
</div>

<h3>为什么收缩是必须的</h3>
<p>C2 给出的是 3/3 = 100%。任何一份递给老板或发给朋友的材料，都会把"历史上三次全部反弹"当成强证据。但这三个样本来自 3 次事件，其中两次（2015-07、2015-10）还是同一轮崩盘里的相邻时点，信息高度重复。用基准率做先验、n₀=15 个伪观测做收缩，得到的 51.8% 才是这句话应有的重量。<b>收缩不是保守，是把"三次"翻译成它真实的证据量。</b></p>
</section>

<hr class="sec">
<section id="s3">
<h2><span class="num">0 3</span>同位置类比：短线会弹，中期难说</h2>
<p>最可比的口径不是"跌到底之后怎样"（那有后视偏差），而是<b>"回撤第一次触及 −40% 的那一天之后怎样"</b>。历史上发生过 4 次：</p>
<table>
<thead><tr><th>触及日</th><th class="num">所在段深度</th><th class="ctr">20日内涨≥5%</th><th class="num">20日最大涨幅</th><th class="num">20日最大回撤</th><th class="num">60日终点</th><th class="num">120日终点</th><th class="ctr">20日内破前低</th></tr></thead>
<tbody>{rows_a}</tbody></table>
<p class="fn">† 该时点落在前一轮崩盘的反弹途中，没有对应的独立熊市段，取最近一段作参照。</p>
{chart_analogs()}
<figcaption>四次同位置类比各时点的终点收益。20 日维度 3 正 1 负；60 日维度 3 负 1 正；120 日维度分化明显。</figcaption>

<p><b>这个表读出来的东西，和"抄底"叙事的期望并不一致：</b></p>
<ul class="tight">
<li><b>20 日维度确实偏正</b>：4 次里 3 次在 20 天内给到 +5% 以上，最大涨幅分别是 +0.3%、+26.2%、+19.6%、+21.9%（唯一失败的是 2011-12-27）。符合"超跌反弹"的直觉。</li>
<li><b>60 日维度多数是负的</b>：−5.9%、−6.9%、−7.2%、+20.0%。三次下跌有两次是因为反弹在两个月内被二次探底吃掉（2015-07 之后有 8 月崩盘，2015-10 之后有熔断）。</li>
<li><b>失败的代价不小</b>：2011-12-27 之后 20 日最大回撤 −14.1%，且创了新低。也就是说，"五成偏上"的概率背后，有四分之一的概率是先挨 14% 再谈反弹。</li>
</ul>

<div class="warn">
<div class="h">这 就 是 你 的 判 断 需 要 被 量 化 的 地 方</div>
"跌多了要反弹"在 20 日尺度上成立（约五成偏上，高于基准 42%），在 60 日尺度上不成立（终点收益多数为负）。<b>两者并不矛盾：反弹和反转是两件事。</b>如果你的判断是"短期有反弹"，数据支持你；如果判断是"这里是底"，数据既不支持也不否定——它只是没有足够样本，而唯一能类比的那两次（2012 年初、2024 年初）在 250 日后都创过新低。
</div>
</section>

<hr class="sec">
<section id="s4">
<h2><span class="num">0 4</span>形态同构性：它像哪一段</h2>
<p>按"跌幅 ≥30% 进入熊市段、自低点反弹 ≥20% 结束"的摆动点规则，16 年可以拆出 9 段真熊市。当前这段是第 9 段，仍在进行中：</p>
<table>
<thead><tr><th>熊市段</th><th class="num">跌幅</th><th class="num">历时</th><th class="num">速度</th><th class="num">年化波动</th><th class="num">量能萎缩</th></tr></thead>
<tbody>{rows_l}</tbody></table>
{chart_legs()}
<figcaption>每一个空心点对应上表的一段熊市（共九段，按时间顺序与表格一一对应）。横向是跌了多久，纵向是跌了多深：快速崩盘集中在左上（2015 年 6–7 月，23 个交易日跌 40.9%）；慢熊在右下（2016–2018，612 个交易日跌 48.2%）。当前段孤立在中间偏左上。</figcaption>

<p><b>同构性结论有三条，都指向"不能简单类比"：</b></p>
<ol class="steps">
<li><div class="t">速度是历史均值的三到六倍</div><div class="d">当前段 −10.1%/月。慢熊（2016–2018、2022–2024）是 −1.6 至 −2.4%/月，2015 年 6–7 月是 −35.6%/月。你这段既不是阴跌，也不是断崖，是一种历史上只出现过一两次的中等斜率崩塌。</div></li>
<li><div class="t">波动率处于高位而非底部</div><div class="d">当前段年化波动 43.1%，接近 2015 年的 51%–69%，远高于 2018、2022、2024 那几段慢熊的 20%–26%。<b>底部通常伴随波动率衰减</b>；现在还没有这个特征。</div></li>
<li><div class="t">量能已在萎缩，但幅度中和</div><div class="d">当前段末 60 日均量 / 峰值前 60 日均量 = 0.81x。历史上 0.77x–0.80x 的那几次（2010、2015-11、2016）后续都还有下跌，1.1–1.3x 的反而见过快速反弹。<b>缩量在这里不是见底信号。</b></div></li>
</ol>
<p>形态向量最近的三段是：{sim_txt}。注意这份"相似"只基于深度、历时、波动、量能四个价格维度，<b>不含宏观驱动</b>——而驱动恰恰决定后续分布，这部分按约定留给完整版。</p>
</section>

<hr class="sec">
<section id="s5">
<h2><span class="num">0 5</span>最近的那一次：2012 年 2 月</h2>
<p>如果非要找一个"最像今天"的时刻，是 <b>2012-02-01</b>：连跌 10 周、60 日跌幅 −23.69%。当时的状态比你更极端（周数更长），但 60 日深度略浅。</p>
<table>
<thead><tr><th>2012-02-01 之后</th><th class="num">20 日</th><th class="num">60 日</th><th class="num">120 日</th><th class="num">250 日</th></tr></thead>
<tbody>
<tr><td>最大涨幅</td><td class="num">+17.1%</td><td class="num">+21.8%</td><td class="num">+21.8%</td><td class="num">+21.8%</td></tr>
<tr><td>最大回撤</td><td class="num">+2.3%</td><td class="num">+2.3%</td><td class="num">+2.3%</td><td class="num neg">−8.8%</td></tr>
<tr><td>终点收益</td><td class="num pos">+13.0%</td><td class="num pos">+6.6%</td><td class="num pos">+8.6%</td><td class="num pos">+20.0%</td></tr>
<tr><td>是否跌破前低</td><td class="num">否</td><td class="num">否</td><td class="num">否</td><td class="num neg">是</td></tr>
</tbody></table>
<p>这是一条对多头很友好的样本：买入后几乎没再跌，20 天涨 17%。<b>但它只有一个。</b>同期还有一个不那么友好的样本：2024-02-02（连跌 5 周、60 日 −23.19%）之后 20 日涨 21.9%，同样漂亮——可是这两次的共同点是<b>政策强力介入</b>（2012 年初的降准与养老金入市表态、2024 年 2 月的汇金增持与交易监管干预）。这一点必须记账：样本里那些"快速反弹"的案例，多数不是估值自发修复，而是外生力量打断。</p>
<div class="note">
<div class="h">给 完 整 版 留 的 钩 子</div>
这条观察如果成立，就把问题从"跌多了会弹吗"改写成"外生干预到位了吗"。这是一个可以证伪的命题，也是我认为下一阶段最值得做的一件事——但需要宏观与政策数据，不在这一版范围内。
</div>
</section>

<hr class="sec">
<section id="s6">
<h2><span class="num">0 6</span>对你"加仓博弈"的含义</h2>
<p>先说清楚：<b>以下是历史分布，不是操作建议。</b>概率是客观的，仓位是主观的，只有你能定。</p>
<table>
<thead><tr><th>维度</th><th>历史告诉你的</th><th>含义</th></tr></thead>
<tbody>
<tr><td>20 日内反弹 ≥5%</td><td>约 49%（区间 31–68%）</td><td>比抛硬币略好，不足以支撑"重仓押注"的确定性</td></tr>
<tr><td>20 日内先跌 5% 以上</td><td>4 次类比里 1 次先跌 14.1%</td><td>约四分之一的概率你会先浮亏两位数</td></tr>
<tr><td>60 日终点为正</td><td>4 次里 1 次</td><td>中期维度上，历史并不站在"这就是底"一边</td></tr>
<tr><td>波动率位置</td><td>43% 年化，历史 83 分位</td><td>底部特征通常伴随波动衰减，目前未见</td></tr>
<tr><td>无先例状态</td><td>C5 条件历史上从未出现</td><td>任何"历史上类似情况都如何"的说法，在这里都没有样本基础</td></tr>
</tbody></table>
<p>如果一定要把这份数据转成决策语言，它支持的是一句话：<b>"值得用小仓位参与，但不值得用大仓位确信。"</b>历史给的赔率是"五成概率赚 5%–20%，四分之一概率先亏 14%"，这个赔率结构对分批建仓友好，对一次性打满不友好。</p>
<p>另外提醒一个容易犯的错：<b>把"反弹概率 49%"当成"上涨概率 49%"</b>。反弹的定义是"窗口内最高点曾达到 +5%"，它并不要求你在那个最高点卖出。20 日终点的中位数在历史样本里只有 +0.23%。<b>能弹到 +5% 和你能把这 5% 拿到手，是两件不同的事。</b></p>
</section>

<hr class="sec">
<section id="s7">
<h2><span class="num">0 7</span>失效条件：什么情况下这份报告作废</h2>
<p>这些在跑数之前就写进预注册清单了，现在照抄，不做事后修改：</p>
<ul class="tight">
<li><b>流动性或信用事件驱动。</b>若下跌主因是流动性枯竭、信用违约、被动平仓，均值回归统计整体失效，历史类比会系统性低估下跌深度（2024 年 2 月的小微盘流动性危机就是例子，当时跌到 −40% 之后还继续跌）。</li>
<li><b>制度变化。</b>涨跌幅、T+0、减持或退市规则调整，会改变整个收益分布的形状。</li>
<li><b>编制规则大幅调整。</b>指数成分与加权方式变化后，历史点位与今日不可比。</li>
<li><b>单日跳空 >7%。</b>样本内不存在这种冲击，模型外推无效。</li>
</ul>
<h3>这一版已知的缺陷</h3>
<ul class="tight">
<li><b>样本量是硬伤。</b>C1 只有 4 个样本，C2 只有 3 个。任何区间都宽到无法支撑精确判断，这不是方法问题，是历史只发生了这么多次。</li>
<li><b>没有做多重比较矫正。</b>5 个条件 × 4 个网格 = 20 个检验，纯随机也会出现约 1 个"显著"。所以我没有单独挑出任何一个"显著"结果做结论，全部按收缩后的值报。</li>
<li><b>同构性只做了价格形态。</b>不含宏观、流动性、估值分位。这是与你有约在先的取舍，也是最可能改变结论的一块。</li>
<li><b>基准日取 10-29 收盘。</b>今日（10-30）收盘后数字会小幅变化，同一脚本重跑即可，参数不变。</li>
<li><b>不含分红、费用、冲击成本。</b>指数收益与你的实际持仓收益之间有摩擦。</li>
</ul>
</section>

<hr class="sec">
<section id="s8">
<h2><span class="num">0 8</span>方法与声明</h2>
<p><b>数据</b>：创业板指（399006）日收盘价，2010-06-02 至 2026-10-29，共 3,983 个交易日。腾讯财经 ifzq 接口取原始数据，新浪财经在 1,023 个重叠交易日上逐日比对，收盘价差异 >0.05 元的天数为 0。</p>
<p><b>方法</b>：事件研究 + Wilson 区间 + Beta 先验贝叶斯收缩（n₀=15）+ 摆动点熊市段识别（30%/20%）+ 等权 z 分数形态距离。全部参数在执行前写入《预注册清单_2026-10-30.md》。脚本可复现：<code>scripts/analyze.py</code>。完整概率矩阵见 <code>out/probability_table.csv</code>。</p>
<p><b>核心局限再强调一次</b>：4 个样本推不出精确概率。这份报告的价值不在于那个 49%，而在于它把"能弹"和"见底"分开、把"五五开"和"确定"分开、并明确告诉你哪些结论在样本外会失效。</p>
<p><b>声明</b>：本文为历史统计研究，<b>不构成投资建议</b>，不预示未来收益。历史基准率不保证重现，极端行情下统计规律可能整体失效。据此操作，风险自担。</p>
</section>

<footer>
<p>数据截止 2026-10-29 收盘 · 生成于 {R['meta']['generated']} · 单文件离线文档，图表为内联 SVG</p>
<p>样本 3,983 交易日 · 条件冷却期 60 交易日 · 先验强度 n₀=15 · 主口径 H=20 日 / Y=5%</p>
</footer>

</main></div>
<script>
(function(){{
 var bar=document.getElementById('bar');
 var links=[].slice.call(document.querySelectorAll('#toc a'));
 var secs=links.map(function(a){{return document.getElementById(a.getAttribute('href').slice(1));}});
 function onScroll(){{
   var h=document.documentElement;
   var p=h.scrollTop/(h.scrollHeight-h.clientHeight||1);
   bar.style.width=(p*100).toFixed(2)+'%';
   var idx=0;
   for(var i=0;i<secs.length;i++){{ if(secs[i]&&secs[i].getBoundingClientRect().top<160) idx=i; }}
   links.forEach(function(a,i){{a.classList.toggle('on',i===idx);}});
 }}
 document.addEventListener('scroll',onScroll,{{passive:true}});onScroll();
}})();
</script>
</body></html>"""

    html = html.replace("{{", "{").replace("}}", "}")
    html = cjk_quotes(html)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print("written: %s (%.1f KB)" % (OUT, len(html) / 1024))


if __name__ == "__main__":
    main()
