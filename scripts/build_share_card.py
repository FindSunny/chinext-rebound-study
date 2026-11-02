# -*- coding: utf-8 -*-
"""分享卡片：4 次跌破 -40% 的历史 + 本次预期（1080x1440）。"""
import os, json, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = os.path.join(BASE, "data", "analysis_result.json")
WB = (len(sys.argv) > 1 and sys.argv[1] == "weibo")
_OUTNAME = ("创业板反弹概率_分享图_微博版_2026-10.html" if WB
            else "创业板反弹概率_分享图_2026-10.html")
OUT = os.path.join(BASE, "out", _OUTNAME)
R = json.load(open(J, encoding="utf-8"))

DESC = {"2011-12-27": "熊市末段", "2015-07-07": "股灾第一波",
        "2015-10-21": "反弹途中二次触线", "2024-02-02": "流动性危机"}

PAPER, INK, MUTED = "#f7f5f1", "#17181a", "#6f6a61"
TEAL, RUST = "#0b6e6e", "#b4462f"
CHAR, RULE = "#3a3630", "#d9d4cb"

h = [dict(date=a["touch_date"], r20=a["f20"]["terminal"], r60=a["f60"]["terminal"],
          desc=DESC.get(a["touch_date"], ""))
     for a in R["analogs"]]
med20, med60 = 0.1087, -0.0641        # 4 次中位数
prob, plo, phi = 0.4912, 0.3074, 0.6761

W, H = 1080, 1440
PL, PR, PT, PB = 150, 84, 476, 1100
ylo, yhi = -10.5, 25.0

# ---- 合规变体文案（微博版：降级为历史复盘，不做预测表述）----
TOPRIGHT = "16 年 · 4 次 · 非预测" if WB else "16 年 · 仅 4 次"
STRIP_K = "历史参考" if WB else "短期空间"
LEG5 = "历史参考" if WB else "本次预期"
COL_EV = "历史参考" if WB else "本次预期"
COL_EVD = "四次中间水平" if WB else "中间水平 · 第 5 次"
CAP_TXT = ("2010–2026 历史统计 · 非预测　纵轴：结算收益　横轴：4 次触发时点" if WB
           else "纵轴：跌破后的结算收益　横轴：4 次触发时点 + 本次")
DISC = ("本图仅整理历史数据，不含预测，不构成投资建议 · 数据：创业板指 2010-06 至 2026-10-30"
        if WB else "数据：创业板指 2010-06 至 2026-10-30 · 历史统计，不构成投资建议")


def Y(v):
    return PT + (PB - PT) * (1 - (v - ylo) / (yhi - ylo))


n = 5
step = (W - PR - PL) / n
cx = [PL + step * (i + 0.5) for i in range(n)]

S = [f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg">']
for g in (20, 10, 0, -10):
    y = Y(g)
    strong = (g == 0)
    S.append(f'<line x1="{PL-26}" y1="{y:.1f}" x2="{W-PR}" y2="{y:.1f}" '
             f'stroke="{INK if strong else RULE}" stroke-width="{1.6 if strong else 1}"/>')
    lab = "0" if g == 0 else ("+%d%%" % g if g > 0 else "−%d%%" % abs(g))
    S.append(f'<text x="{PL-36}" y="{y+6:.1f}" text-anchor="end" class="ax">{lab}</text>')

# 历史 4 列
for i, p in enumerate(h):
    x = cx[i]
    y20, y60 = Y(p["r20"] * 100), Y(p["r60"] * 100)
    flip = p["r20"] > 0 and p["r60"] < 0
    S.append(f'<line x1="{x:.1f}" y1="{y20:.1f}" x2="{x:.1f}" y2="{y60:.1f}" '
             f'stroke="{RUST if flip else "#cdc6b9"}" stroke-width="{2.6 if flip else 2}" '
             f'stroke-dasharray="{"6 5" if flip else "3 4"}" opacity=".85"/>')
    S.append(f'<circle cx="{x:.1f}" cy="{y20:.1f}" r="8.5" fill="{TEAL}"/>')
    S.append(f'<circle cx="{x:.1f}" cy="{y60:.1f}" r="8.5" fill="{CHAR}"/>')
    S.append(f'<text x="{x-17:.1f}" y="{y20+6:.1f}" text-anchor="end" class="val t">{p["r20"]*100:+.1f}%</text>')
    S.append(f'<text x="{x+17:.1f}" y="{y60+6:.1f}" class="val c">{p["r60"]*100:+.1f}%</text>')
    S.append(f'<text x="{x:.1f}" y="{PB+34}" text-anchor="middle" class="ev">{p["date"]}</text>')
    S.append(f'<text x="{x:.1f}" y="{PB+60}" text-anchor="middle" class="evd">{p["desc"]}</text>')

# 分隔线 + 本次预期列
sep = (cx[3] + cx[4]) / 2
S.append(f'<line x1="{sep:.1f}" y1="{PT-10}" x2="{sep:.1f}" y2="{PB+4}" stroke="#c9c2b5" stroke-width="1.2" stroke-dasharray="4 5"/>')
x = cx[4]
y20, y60 = Y(med20 * 100), Y(med60 * 100)
S.append(f'<line x1="{x:.1f}" y1="{y20:.1f}" x2="{x:.1f}" y2="{y60:.1f}" stroke="{RUST}" '
         f'stroke-width="2.4" stroke-dasharray="6 5" opacity=".5"/>')
S.append(f'<circle cx="{x:.1f}" cy="{y20:.1f}" r="8.5" fill="none" stroke="{TEAL}" stroke-width="2.8"/>')
S.append(f'<circle cx="{x:.1f}" cy="{y60:.1f}" r="8.5" fill="none" stroke="{CHAR}" stroke-width="2.8"/>')
S.append(f'<text x="{x-17:.1f}" y="{y20+6:.1f}" text-anchor="end" class="val t">+10.9%</text>')
S.append(f'<text x="{x+17:.1f}" y="{y60+6:.1f}" class="val c">−6.4%</text>')
S.append(f'<text x="{x:.1f}" y="{PB+34}" text-anchor="middle" class="ev cur">{COL_EV}</text>')
S.append(f'<text x="{x:.1f}" y="{PB+60}" text-anchor="middle" class="evd">{COL_EVD}</text>')
S.append("</svg>")
S = "\n".join(S)

html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>反弹是真的，见底是例外</title>
<style>
html,body{{margin:0;padding:0;width:{W}px;height:{H}px;overflow:hidden}}
body{{background:{PAPER};color:{INK};
 font-family:-apple-system,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
 -webkit-font-smoothing:antialiased}}
.card{{position:relative;width:{W}px;height:{H}px;box-sizing:border-box;padding:60px 72px}}
.top{{display:flex;justify-content:space-between;align-items:baseline;
 font-size:20px;letter-spacing:.14em;color:{MUTED}}}
.top b{{color:{RUST};font-weight:600;letter-spacing:.14em}}
h1{{margin:36px 0 0;font-size:66px;line-height:1.24;font-weight:800;letter-spacing:-.02em}}
h1 .hl{{color:{RUST}}}
.sub{{margin-top:16px;font-size:20px;line-height:1.6;color:#3a3630}}
.sub b{{font-weight:700}}
.sub .tl{{color:{TEAL}}} .sub .hl{{color:{RUST}}}
.sub .sm{{display:block;margin-top:5px;font-size:16px;color:{MUTED}}}

.chead{{position:absolute;left:72px;right:72px;top:404px;display:flex;justify-content:space-between;
 align-items:baseline;border-bottom:1px solid {RULE};padding-bottom:11px}}
.chead .cap{{font-size:15px;color:{MUTED}}}
.chead .lg{{font-size:14px;color:{MUTED};display:flex;gap:15px;align-items:center}}
.chead .lg i{{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:6px;vertical-align:-1px}}
.chead .lg .d20{{background:{TEAL}}} .chead .lg .d60{{background:{CHAR}}}
.chead .lg .dfc{{background:none;border:2.4px solid {TEAL};width:8px;height:8px}}
.chead .lg .ln{{display:inline-block;width:22px;height:0;border-top:2.6px dashed {RUST};margin-right:6px;vertical-align:3px}}

.chart{{position:absolute;left:0;top:0;width:{W}px;height:{H}px}}
.chart .ax{{font:16px/1 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;fill:{MUTED}}}
.chart .val{{font:600 17px/1 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;font-variant-numeric:tabular-nums;paint-order:stroke;stroke:#f7f5f1;stroke-width:4px;stroke-linejoin:round}}
.chart .val.t{{fill:{TEAL}}} .chart .val.c{{fill:{CHAR}}}
.chart .ev{{font:600 17px/1 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;fill:{INK}}}
.chart .ev.cur{{fill:{RUST}}}
.chart .evd{{font:14px/1 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;fill:{MUTED}}}

.odds{{position:absolute;left:72px;right:72px;top:1192px;display:flex;align-items:baseline;gap:14px}}
.odds .k{{font-size:13px;color:{RUST};font-weight:700;letter-spacing:.18em;padding-right:2px}}
.odds .v{{font-size:34px;font-weight:700;color:{TEAL};line-height:1;font-variant-numeric:tabular-nums;letter-spacing:-.02em}}
.odds .r{{font-size:14px;color:{MUTED}}}

.foot{{position:absolute;left:72px;right:72px;bottom:44px;border-top:1px solid {RULE};padding-top:15px}}
.foot p{{margin:0 0 5px;font-size:14px;line-height:1.54;color:{MUTED}}}
.foot p:last-child{{margin-bottom:0}}
.foot b{{color:{CHAR};font-weight:600}}
.foot .disc{{color:#8b857c;font-size:12.5px;margin-top:6px}}
</style></head>
<body>
<div class="card">
  <div class="top"><span>创业板指 · 399006</span><b>{TOPRIGHT}</b></div>
  <h1>反弹是真的，<br>见底是<span class="hl">例外</span>。</h1>
  <div class="sub">
    4 次跌破 −40%：一个月内 <b class="tl">3 次涨超 19%</b>，3 个月后 <b class="hl">3 次倒亏</b>。
    <span class="sm">同一批样本，只把结算点从 1 个月挪到 3 个月，结论就反转。</span>
  </div>

  <div class="chead">
    <div class="cap">{CAP_TXT}</div>
    <div class="lg">
      <span><i class="d20"></i>1 个月后</span>
      <span><i class="d60"></i>3 个月后</span>
      <span><i class="dfc"></i>{LEG5}</span>
      <span><i class="ln"></i>由正转负</span>
    </div>
  </div>

  <div class="chart">{S}</div>

  <div class="odds">
    <span class="k">{STRIP_K}</span>
    <span class="v">+10.9%</span>
    <span class="r">一个月后结算的中间水平 · 4 次里 3 次为正</span>
  </div>

  <div class="foot">
    <p><b>口径</b>　跌破 = 收盘价自 250 日最高收盘回撤 −40% 的首次触及日；结算 = 其后第 20 / 60 个交易日的收盘收益。</p>
    <p><b>本次</b>　空心点为 4 次结算收益的中间水平（中位数），区间 −8.5% ~ +21.9%（1 个月）、−7.2% ~ +20.0%（3 个月）。</p>
    <p><b>当前</b>　10-22 首破 −40%，10-30 收 2,413.63（−44.8%），20 日后续数据尚未产生。</p>
    <p class="disc">{DISC}</p>
  </div>
</div>
</body></html>"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("written:", OUT)
