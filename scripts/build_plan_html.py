# -*- coding: utf-8 -*-
"""生成《创业板反弹概率预测方案》单文件 HTML（内联 SVG 图，离线可开）。

【已冻结】本文档是 2026-10-29 数据快照下的方案存档，表中数值为当时的现状。
行情更新后请勿重新运行本脚本（会重绘图表但表格仍为旧值，造成文档内不一致）；
最新数据请看《创业板反弹概率_快速版_2026-10.html》。
"""
import os, math
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(BASE, "data", "399006_daily_tencent.csv")
OUT = os.path.join(BASE, "out", "创业板反弹概率预测方案_2026-10.html")

PAPER, INK, RULE = "#f7f5f1", "#17181a", "#d9d4cb"
TEAL, RUST, GOLD = "#0b6e6e", "#b4462f", "#a67c1f"
MUTED = "#6f6a61"


def load():
    df = pd.read_csv(CSV, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    return df


# ---------------------------------------------------------------- 图1 走势
def chart_price(df):
    w = df.set_index("date")["close"].resample("W-FRI").last().dropna()
    w = w[w.index >= "2023-01-01"]
    W, H = 860, 320
    L, R, T, B = 58, 22, 26, 40
    lo, hi = w.min() * 0.96, w.max() * 1.03
    n = len(w)

    def x(i):
        return L + (W - L - R) * (i / (n - 1))

    def y(v):
        return T + (H - T - B) * (1 - (v - lo) / (hi - lo))

    pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(w.values))
    area = f"{L:.1f},{H-B:.1f} " + pts + f" {x(n-1):.1f},{H-B:.1f}"

    # 6月高点与当前点
    hi_i = int(np.argmax(w.values))
    px, py = x(n - 1), y(w.values[-1])
    hx, hy = x(hi_i), y(w.values[hi_i])
    mx, my = (hx + px) / 2, (hy + py) / 2
    ddown = (w.values[-1] / w.values[hi_i] - 1) * 100

    grid = []
    for k in range(5):
        v = lo + (hi - lo) * k / 4
        yy = y(v)
        grid.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{W-R}" y2="{yy:.1f}" stroke="{RULE}" stroke-width="1"/>')
        grid.append(f'<text x="{L-8}" y="{yy+4:.1f}" text-anchor="end" class="ax">{v:,.0f}</text>')

    ticks = []
    for i, dt in enumerate(w.index):
        if i % max(1, n // 7) == 0:
            ticks.append(f'<text x="{x(i):.1f}" y="{H-B+20:.1f}" text-anchor="middle" class="ax">{dt.strftime("%y/%m")}</text>')

    svg = f'''<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="创业板指周线走势 2023-2026">
<defs><linearGradient id="ga" x1="0" y1="0" x2="0" y2="1">
<stop offset="0%" stop-color="{TEAL}" stop-opacity="0.22"/><stop offset="100%" stop-color="{TEAL}" stop-opacity="0.02"/>
</linearGradient></defs>
{''.join(grid)}
<polygon points="{area}" fill="url(#ga)"/>
<polyline points="{pts}" fill="none" stroke="{TEAL}" stroke-width="1.8" stroke-linejoin="round"/>
<line x1="{hx:.1f}" y1="{hy:.1f}" x2="{px:.1f}" y2="{py:.1f}" stroke="{RUST}" stroke-width="1.1" stroke-dasharray="4 4"/>
<circle cx="{hx:.1f}" cy="{hy:.1f}" r="3.4" fill="{RUST}"/>
<circle cx="{px:.1f}" cy="{py:.1f}" r="4.4" fill="{RUST}" stroke="{PAPER}" stroke-width="1.6"/>
<text x="{mx+9:.1f}" y="{my+4:.1f}" class="pt rust halo">{ddown:.1f}%</text>
{''.join(ticks)}
</svg>'''
    return svg


# ---------------------------------------------------------------- 图2 概率对比
def chart_prob():
    W, H = 860, 360
    L, R, T, B = 250, 116, 30, 54
    rows = [
        ("无条件基准（任意一天起算）", 42.2, 40.7, 43.8, 3963, "base"),
        ("连跌3周 + 60日跌幅≥12%", 64.7, 41.3, 82.7, 17, "cond"),
        ("连跌4周 + 60日跌幅≥12%", 75.0, 40.9, 92.9, 8, "cond"),
        ("连跌5周 + 60日跌幅≥12%", 60.0, 23.1, 88.2, 5, "thin"),
        ("连跌6周 + 60日跌幅≥15%", 100.0, 20.7, 100.0, 1, "thin"),
    ]
    plot_w = W - L - R

    def x(p):
        return L + plot_w * (p / 100.0)

    parts = []
    for p in (0, 25, 50, 75, 100):
        xx = x(p)
        parts.append(f'<line x1="{xx:.1f}" y1="{T-6}" x2="{xx:.1f}" y2="{H-B}" stroke="{RULE}" stroke-width="1"/>')
        parts.append(f'<text x="{xx:.1f}" y="{H-B+20}" text-anchor="middle" class="ax">{p}%</text>')
    # 基准率参考带
    parts.append(f'<rect x="{x(40.7):.1f}" y="{T-6}" width="{x(43.8)-x(40.7):.1f}" height="{H-B-T+6}" fill="{TEAL}" opacity="0.10"/>')
    parts.append(f'<line x1="{x(42.2):.1f}" y1="{T-6}" x2="{x(42.2):.1f}" y2="{H-B}" stroke="{TEAL}" stroke-width="1.4" stroke-dasharray="5 3"/>')
    parts.append(f'<text x="{x(42.2):.1f}" y="{T-13}" text-anchor="middle" class="ax teal">基准 42.2%</text>')

    rh = (H - B - T) / len(rows)
    for i, (label, p, lo, hi, n, kind) in enumerate(rows):
        cy = T + rh * i + rh / 2
        col = TEAL if kind == "base" else (RUST if kind == "cond" else "#b9b2a6")
        parts.append(f'<text x="{L-12}" y="{cy+4:.1f}" text-anchor="end" class="lbl">{label}</text>')
        parts.append(f'<line x1="{x(lo):.1f}" y1="{cy:.1f}" x2="{x(hi):.1f}" y2="{cy:.1f}" stroke="{col}" stroke-width="1.6" opacity="0.55"/>')
        for e in (lo, hi):
            parts.append(f'<line x1="{x(e):.1f}" y1="{cy-6:.1f}" x2="{x(e):.1f}" y2="{cy+6:.1f}" stroke="{col}" stroke-width="1.6" opacity="0.55"/>')
        fill = col if kind != "thin" else "none"
        parts.append(f'<circle cx="{x(p):.1f}" cy="{cy:.1f}" r="5" fill="{fill}" stroke="{col}" stroke-width="1.7"/>')
        parts.append(f'<text x="{W-R+10}" y="{cy+4:.1f}" class="ax n">n={n}</text>')

    parts.append(f'<text x="{L}" y="{H-8}" class="ax">区间为 Wilson 95% 置信区间；空心点为 n≤5，不可据此下判断</text>')
    return f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="条件概率与基准率对比">{chr(10).join(parts)}</svg>'


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
    df = load()
    c1 = chart_price(df)
    c2 = chart_prob()

    css = """
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:PAPER;color:INK;font:16px/1.75 -apple-system,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;-webkit-font-smoothing:antialiased}
a{color:TEAL;text-decoration:none;border-bottom:1px solid rgba(11,110,110,.28)}
a:hover{border-bottom-color:TEAL}
.wrap{display:flex;max-width:1240px;margin:0 auto;gap:46px;padding:0 28px}
#toc{position:sticky;top:0;align-self:flex-start;width:206px;flex:0 0 206px;height:100vh;overflow:auto;padding:34px 0 40px;font-size:13.5px}
#toc .tt{font-size:11px;letter-spacing:.14em;color:MUTED;margin-bottom:14px;text-transform:uppercase}
#toc a{display:block;color:#5c5750;border:0;padding:5px 0 5px 11px;border-left:2px solid RULE;line-height:1.45}
#toc a.on{color:INK;border-left-color:TEAL;font-weight:600}
#toc a:hover{color:TEAL}
main{flex:1 1 auto;min-width:0;padding:0 0 120px}
#bar{position:fixed;top:0;left:0;height:2px;background:TEAL;width:0;z-index:99}
.cover{min-height:96vh;display:flex;flex-direction:column;justify-content:center;border-bottom:1px solid RULE;padding:60px 0 48px}
.kicker{font-size:12px;letter-spacing:.2em;color:RUST;margin-bottom:22px}
h1{font-size:clamp(30px,4.4vw,50px);line-height:1.16;margin:0 0 20px;letter-spacing:-.02em;font-weight:700}
.sub{font-size:clamp(16px,1.6vw,20px);color:#4a453f;line-height:1.7;max-width:44em;margin:0 0 34px}
.meta{display:flex;flex-wrap:wrap;gap:26px;font-size:13px;color:MUTED;border-top:1px solid RULE;padding-top:20px}
.meta b{color:INK;font-weight:600;display:block;font-size:15px;font-variant-numeric:tabular-nums}
h2{font-size:24px;margin:64px 0 6px;letter-spacing:-.01em;font-weight:700}
h2 .num{font-size:12px;letter-spacing:.16em;color:RUST;display:block;margin-bottom:8px;font-weight:600}
h3{font-size:16.5px;margin:32px 0 8px;font-weight:650}
p{margin:13px 0}
.lead{font-size:17.5px;color:#332f2a;line-height:1.8}
hr.sec{border:0;border-top:1px solid RULE;margin:0}
.verdict{background:#fff;border:1px solid RULE;border-left:3px solid RUST;padding:22px 26px;margin:28px 0;border-radius:2px}
.verdict .h{font-size:11px;letter-spacing:.16em;color:RUST;margin-bottom:10px;font-weight:600}
.verdict p{margin:8px 0}
.note{background:rgba(11,110,110,.055);border:1px solid rgba(11,110,110,.18);padding:18px 22px;border-radius:2px;margin:24px 0;font-size:15px}
.note .h{font-size:11px;letter-spacing:.16em;color:TEAL;margin-bottom:8px;font-weight:600}
table{width:100%;border-collapse:collapse;margin:20px 0;font-size:14px}
th{text-align:left;font-size:11.5px;letter-spacing:.08em;color:MUTED;font-weight:600;border-bottom:1.5px solid #c9c3b9;padding:8px 10px 8px 0;white-space:nowrap}
td{padding:9px 10px 9px 0;border-bottom:1px solid #e6e1d8;vertical-align:top;font-variant-numeric:tabular-nums}
.num{text-align:right;white-space:nowrap}
.ctr{text-align:center}
tr.hi td{background:rgba(180,70,47,.06)}
.neg{color:RUST}
.chart{width:100%;height:auto;display:block;margin:10px 0 4px;overflow:visible}
.chart .ax{font-size:11px;fill:MUTED;font-family:inherit}
.chart .lbl{font-size:12.5px;fill:#3a3630;font-family:inherit}
.chart .pt{font-size:11.5px;fill:#3a3630;font-family:inherit}
.chart .pt.strong{font-weight:700;fill:INK}
.chart .pt.rust{fill:RUST}
.chart .pt.halo{paint-order:stroke;stroke:PAPER;stroke-width:3.6px;stroke-linejoin:round}
.chart .teal{fill:TEAL}
.chart .n{fill:MUTED}
figcaption{font-size:12.5px;color:MUTED;margin:2px 0 26px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:26px}
.card{border:1px solid RULE;background:#fff;padding:18px 20px;border-radius:2px}
.card .t{font-size:13px;font-weight:650;margin-bottom:6px}
.card .d{font-size:13.5px;color:#4a453f;line-height:1.65}
ol.steps{counter-reset:s;list-style:none;padding:0;margin:20px 0}
ol.steps>li{counter-increment:s;position:relative;padding:16px 0 16px 46px;border-bottom:1px solid #e6e1d8}
ol.steps>li::before{content:counter(s);position:absolute;left:0;top:16px;width:26px;height:26px;border:1px solid TEAL;color:TEAL;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600}
ol.steps .t{font-weight:650;margin-bottom:4px}
ol.steps .d{color:#4a453f;font-size:14.5px}
ul.tight{margin:10px 0;padding-left:20px}
ul.tight li{margin:7px 0}
.q{border:1px solid RULE;border-radius:2px;margin:14px 0;background:#fff}
.q .h{background:#efece5;padding:10px 16px;font-size:13.5px;font-weight:650;border-bottom:1px solid RULE}
.q .b{padding:12px 16px;font-size:14px;color:#3a3630}
.tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:2px;letter-spacing:.04em;margin-left:6px;vertical-align:1px}
.tag.ok{background:rgba(11,110,110,.12);color:TEAL}
.tag.no{background:rgba(180,70,47,.12);color:RUST}
.tag.warn{background:rgba(166,124,31,.14);color:#7d5c14}
footer{border-top:1px solid RULE;padding:30px 0 60px;font-size:12.5px;color:MUTED;line-height:1.7}
@media (max-width:900px){
 .wrap{flex-direction:column;padding:0 18px;gap:0}
 #toc{position:static;width:100%;flex:none;height:auto;padding:20px 0;border-bottom:1px solid RULE}
 #toc a{display:inline-block;border-left:0;border-bottom:2px solid transparent;padding:3px 10px 3px 0}
 #toc a.on{border-bottom-color:TEAL}
 .cover{min-height:auto;padding:40px 0 30px}
 .grid2{grid-template-columns:1fr}
 table{font-size:12.5px}
 h2{margin-top:44px}
}
@media print{
 #toc,#bar{display:none}
 body{background:#fff;font-size:10.5pt}
 .wrap{display:block;max-width:none;padding:0}
 main{padding:0}
 .cover{min-height:auto;page-break-after:always}
 h2{page-break-after:avoid;margin-top:22pt}
 table,.chart,.verdict,.note,.card{page-break-inside:avoid}
 @page{size:A4;margin:16mm 14mm}
}
"""
    css = css.replace("PAPER", PAPER).replace("MUTED", MUTED).replace("RULE", RULE).replace("TEAL", TEAL).replace("RUST", RUST).replace("INK", INK)

    toc = [
        ("s1", "01 你的处境"),
        ("s2", "02 为什么这是弱信号"),
        ("s3", "03 方案四层"),
        ("s4", "04 数据与口径"),
        ("s5", "05 交付物"),
        ("s6", "06 障碍与风险"),
        ("s7", "07 需要你拍板"),
    ]
    toc_html = "".join(f'<a href="#{i}">{t}</a>' for i, t in toc)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>创业板反弹概率预测方案 · 2026-10</title>
<style>{css}</style></head>
<body><div id="bar"></div>
<div class="wrap">
<nav id="toc"><div class="tt">目录</div>{toc_html}</nav>
<main>

<header class="cover">
  <div class="kicker">方 案 · 待 你 确 认 后 执 行</div>
  <h1>创业板反弹概率要怎么测<br>——以及为什么答案只能是区间</h1>
  <p class="sub">你说"跌了很多、感觉要见底"。这个感觉有数据支撑：创业板指已连跌 6 周、自 6 月高点回撤 42.4%，20 日跌幅位居 16 年历史的第 0.6 百分位。但"概率"这个词，在这么极端的条件下，历史只留给我们 1 到 3 个可比样本。</p>
  <div class="meta">
    <div><b>399006</b>创业板指</div>
    <div><b>2010-06-02 → 2026-10-29</b>样本区间</div>
    <div><b>3,983</b>交易日</div>
    <div><b>2,517.59</b>最新收盘</div>
    <div><b>双源互证</b>腾讯 × 新浪，重叠 1,023 日零差异</div>
  </div>
</header>

<section id="s0">
<h2><span class="num">结 论 先 行</span>我能给你什么，给不了什么</h2>
<p class="lead">能给：一个带置信区间、带失效条件、可回测的概率结构。给不了：一个"底部概率 85%"式的确定数字——不是数据不够，是样本不够，这是数学约束而不是努力问题。</p>

<div class="verdict">
<div class="h">侦 察 级 初 判（非最终结论）</div>
<p>按"20 个交易日内、自当前收盘反弹 ≥5%"这个口径，历史基准率是 <b>42.2%</b>；把条件收紧到"接近你现在的状态"（连跌 3–4 周且 60 日跌幅 ≥12%），历史胜率升到 <b>65%–75%</b>，样本量 n=8–17，95% 置信区间宽达 <b>41%–93%</b>。</p>
<p><b>这个区间把基准率完整包含在内。</b>换句话说：以现有样本，我无法证明"跌多了"比"什么都不知道"更有用——它可能真有用，但证据强度不够把噪音排除掉。</p>
<p>同时，那些条件样本在反弹前平均还要再跌 <b>3%–5%</b>；而"连跌 6 周"这个精确条件，在 16 年里只出现过 <b>1 次</b>（不含当前这次——它还没有后续 20 日数据）。</p>
</div>
<p>这正是《信号与噪音》里最实用的一条：<b>当信号的信噪比低于某个阈值，诚实的选择是报出区间、标注不确定性、并预先写下什么情况会推翻结论</b>，而不是把噪音修饰成小数点后两位的精度。所以下面这份方案的重点，不是"我算出多少"，而是"我怎么保证算出来的东西不是自我欺骗"。</p>
</section>

<hr class="sec">
<section id="s1">
<h2><span class="num">0 1</span>你的处境：比"跌了几周"更极端</h2>
<p>先把话说准。你的直觉不是错觉，实际数据比你的描述更严重：</p>
<table>
<thead><tr><th>指标</th><th class="num">数值</th><th class="num">历史分位</th><th>口径</th></tr></thead>
<tbody>
<tr class="hi"><td>连续下跌周数</td><td class="num neg">6 周</td><td class="num">—</td><td>周线收盘，2026-09-25 → 10-30</td></tr>
<tr class="hi"><td>该段累计跌幅</td><td class="num neg">−25.35%</td><td class="num">—</td><td>自 2026-09-18 收盘（下跌前最后一周）算起</td></tr>
<tr><td>近 20 日涨跌</td><td class="num neg">−25.51%</td><td class="num">0.6%</td><td>位处历史最极端 1% 区间</td></tr>
<tr><td>近 60 日涨跌</td><td class="num neg">−25.49%</td><td class="num">1.4%</td><td>—</td></tr>
<tr><td>近 120 日涨跌</td><td class="num neg">−31.53%</td><td class="num">0.8%</td><td>—</td></tr>
<tr><td>自历史最高回撤</td><td class="num neg">−42.42%</td><td class="num">—</td><td>高点 4,371.99（2026-06-25）</td></tr>
<tr><td>20 日实现波动率</td><td class="num">37.0%</td><td class="num">83.1%</td><td>年化，情绪处于高波动状态</td></tr>
</tbody></table>
{c1}
<figcaption>创业板指周线（2023-01 → 2026-10-29）。6 月高点 4,371.99 至今回撤 42.4%，下跌集中且斜率陡——这更像"高位泡沫破裂"的形态，而不是普通的技术性回调。</figcaption>

<h3>它在历史上排第几</h3>
<p>把 16 年的峰谷全部算一遍，你这轮的位置是这样的：</p>
<table>
<thead><tr><th>排名</th><th>峰值</th><th>谷底</th><th class="num">点位</th><th class="num">深度</th></tr></thead>
<tbody>
<tr><td>1</td><td>2015-06-03</td><td>2018-10-18</td><td class="num">3,982 → 1,205</td><td class="num neg">−69.7%</td></tr>
<tr><td>2</td><td>2010-12-17</td><td>2012-12-03</td><td class="num">1,233 → 594</td><td class="num neg">−51.9%</td></tr>
<tr class="hi"><td>3</td><td>2026-06-25</td><td>2026-10-29</td><td class="num">4,372 → 2,518</td><td class="num neg">−42.4%</td></tr>
<tr><td>4</td><td>2010-06-11</td><td>2010-07-05</td><td class="num">1,122 → 862</td><td class="num neg">−23.2%</td></tr>
</tbody></table>
<p><b>这就是本项目最硬的一个约束</b>：比今天更深的回撤，历史上只有两段。也就是说，当你想问"像现在这种跌法之后会怎样"，可供类比的历史样本实质上只有 <b>2 段行情</b>——而它们的驱动因素（2015 年杠杆牛市破裂叠加去杠杆、2011–2012 年产能过剩与流动性紧缩）与今天未必同构。第 4 名往后的跌幅都只有当下的一半，形态上已不太可比。</p>
<p>这个形态还有一个含义：<b>你的问题不是"跌多了会不会弹"，而是"泡沫破裂到 42% 之后会不会弹"。</b>两者对应的样本集完全不同，所以方案里必须做"同构性识别"，而不能笼统地数"历史上跌过多少次"。</p>
</section>

<hr class="sec">
<section id="s2">
<h2><span class="num">0 2</span>为什么"跌多了会反弹"在统计上是弱信号</h2>
<p>我把你的判断直接放进了历史数据里检验。下面这张图是本方案存在的理由：</p>
{c2}
<figcaption>口径：以检测日为基准，未来 20 个交易日内最高收盘价相对基准日的涨幅 ≥5% 记为"反弹"。条件样本采用 60 个交易日冷却期，避免重叠事件重复计数。区间为 Wilson 95% 置信区间。</figcaption>

<h3>三个必须直面的问题</h3>
<p><b>一、置信区间全部覆盖基准率。</b>连跌 3 周的条件胜率 64.7%，看起来比基准 42.2% 高出一大截，但它的 95% 区间是 [41.3%, 82.7%]——下限刚好压在基准率上。n=17 时，这个"提升"完全可能是抽样误差。<b>把条件收得越紧（越接近你现在的状态），样本越少，区间越宽，结论越不可靠。</b>这不是巧合，是统计学的反比关系：精确描述当下的代价，是失去历史证据。</p>
<p><b>二、n=1 会制造 100% 的幻觉。</b>表里"连跌 6 周 + 60 日跌幅 ≥15%"给出 100% 的胜率，因为 16 年里符合这个条件的样本只有 1 个。这个 100% 的信息量约等于零，但它在任何一张 PPT 上都极具说服力。这类数字是本项目最需要防的东西——我会用贝叶斯收缩把它们拉回基准率附近，并在报告里显式标注有效样本量。</p>
<p><b>三、反弹不等于赚钱。</b>条件样本在 20 日窗口内平均先跌 3%–5%，最差的一例先跌 14%。一个 60% 的反弹概率配一次 15% 的浮亏，绝大多数人的实际结果是"在反弹前被震出去"。所以概率必须和路径风险一起报，单独报概率是有害的。</p>

<div class="note">
<div class="h">一 个 反 直 觉 的 细 节</div>
如果把"反弹"的门槛从 5% 提到 10%，条件概率从 64.7% 掉到 23.5%，而无条件基准率是 20.0%——<b>几乎完全贴合</b>。这说明历史数据里"跌多了之后大涨"的能力很弱，主要贡献的是"跌多了之后小反弹"的均值回归。<b>你想要的是哪一种反弹，直接决定答案的量级。</b>这也解释了这个领域最常见的误用：先有一个想听的答案，再去挑一个能凑出这个答案的门槛。
</div>
</section>

<hr class="sec">
<section id="s3">
<h2><span class="num">0 3</span>方案：四层结构，逐层可证伪</h2>
<p>设计原则是"先定规则，后看结果"。所有特征、门槛、验证方式在执行前写入预注册清单，执行后不允许回头调参——一旦允许，任何数据都能被调出一个漂亮结论，这就是过拟合。</p>

<ol class="steps">
<li>
<div class="t">L0 · 锁定事件定义（一切的前提）</div>
<div class="d">"反弹"必须先变成可计算的事件：<b>P(H, Y) = P( 存在 h ∈ (0, H]，使得 max(close[t+1..t+h]) / close[t0] − 1 ≥ Y )</b>。我建议主口径 <b>(H=20 交易日, Y=5%)</b>，辅以 (20, 3%)、(20, 10%)、(60, 10%) 三组做敏感性对照。基准日 t0 = 2026-10-30 收盘（今日盘后）。<br>同时输出三个路径指标：窗口内最大回撤、是否创新低、以及到 H 日的终点收益。没有这三个，概率会被误读成收益预期。</div>
</li>
<li>
<div class="t">L1 · 基准率层：不看任何信号时的答案</div>
<div class="d">全样本 3,963 个起点，算出无条件基准率与未来收益分布：P(≥3%)=57.1%、P(≥5%)=42.2%、P(≥10%)=20.0%；20 日收益均值 +0.96%、中位 +0.23%、P(收益&gt;0)=51.2%。<br><b>这一层是全案的地基和裁判。</b>后面任何模型如果在样本外打不赢这组数字，就应当直接采用基准率回答，并如实说明"信号无效"。我已经把这个可能性写进方案，它是合法结局，不是失败。</div>
</li>
<li>
<div class="t">L2 · 历史类比层：条件概率 + 贝叶斯收缩</div>
<div class="d">在 L1 基础上叠加条件：连跌 K 周（K=3..6）、近 M 日跌幅（M=20/60，X=−8%/−12%/−15%/−20%）、回撤深度分档。用 60 日冷却期保证事件不重叠，输出每个格子的 n、胜率、Wilson 区间。<br>关键处理：<b>用 Beta 先验（由 L1 基准率定参）对每个格子的概率做收缩</b>，使 n=1 的格子自动退回基准率附近，而不是输出 100%。同时按年份做子样本稳定性检验，标出 2015、2018、2024-02 三个异常期的贡献占比——如果结论主要由某一个极端年份撑起来，那它就不是规律，是一次事件。</div>
</li>
<li>
<div class="t">L3 · 特征模型层：预注册的 12 个信号</div>
<div class="d">分四类，每类最多 3 个，避免"广撒网捞显著性"：<br>
<b>价格/波动</b>：20 日实现波动率分位、距 250 日均线偏离、连跌周数<br>
<b>量能</b>：成交额 20 日均值分位、缩量比（5日/60日均额）、换手率分位<br>
<b>估值/杠杆</b>：创业板 PE 分位、两融余额/流通市值、两融环比变化<br>
<b>宏观状态</b>：10 年期国债收益率变动、政策事件哑变量（降准/降息/汇金增持表态）<br>
主模型用 <b>logistic 回归</b>（n≈4000，可解释、不易过拟合），梯度提升仅作鲁棒性对照。验证用 <b>walk-forward</b>（滚动训练、只用 t 之前的信息预测 t），报告 Brier 分数与校准曲线，并与 L1 基准率做显著性比较。</div>
</li>
<li>
<div class="t">L4 · 同构性检验与失效条件</div>
<div class="d">回答"这次像哪一次"：把当前状态（−42% 回撤、高波动、陡斜率、6 周连跌）与历史 4 个主要下跌段的<b>形态向量</b>（回撤深度/速度/波动率/量能萎缩度/估值分位）做距离匹配，取最近的 3 段，单独报它们的后续分布。<br>并预先写下失效条件：若本次下跌由流动性或信用事件驱动（而非情绪与估值修复），则基于历史分位的均值回归统计<b>整体失效</b>——这类情形下历史类比会系统性低估下跌深度。</div>
</li>
</ol>
</section>

<hr class="sec">
<section id="s4">
<h2><span class="num">0 4</span>数据与口径：已打通的和卡住的</h2>
<p>以下是我在这一小时里实测过的，不是估计：</p>
<table>
<thead><tr><th>数据</th><th>来源</th><th>状态</th><th>用途</th></tr></thead>
<tbody>
<tr><td>创业板指日线全历史</td><td>腾讯 ifzq + 新浪 双源</td><td><span class="tag ok">可用</span>3,983 日，重叠期零差异</td><td>L1/L2 主数据</td></tr>
<tr><td>深市两融余额日序列</td><td>深交所官方 1837_xxpl</td><td><span class="tag ok">可用</span>4,025 行</td><td>L3 杠杆信号</td></tr>
<tr><td>深市成交/市值总貌</td><td>深交所官方 1803_sczm</td><td><span class="tag ok">可用</span>需带 txtQueryDate</td><td>L3 量能信号</td></tr>
<tr><td>创业板指 PE/PB 历史</td><td>巨潮 / 中证指数</td><td><span class="tag warn">需换接口</span>首个试探接口参数报错</td><td>估值分位、同构性</td></tr>
<tr><td>东方财富行情/资金接口</td><td>push2his.eastmoney.com</td><td><span class="tag no">本机被拒</span>连接被对端关闭</td><td>已用腾讯替代</td></tr>
<tr><td>北向资金每日净流入</td><td>—</td><td><span class="tag no">已停止披露</span>2024-08 起</td><td>外资信号不可用，只能退化为季度持仓</td></tr>
</tbody></table>
<p>口径统一说明：价格用<b>收盘价</b>；"反弹"只用日收盘序列计算，不用盘中最高价（避免用不可交易的瞬时价抬高概率）；所有分位数均在<b>全样本 2010-06 起</b>计算；收益不含分红与费用。</p>
</section>

<hr class="sec">
<section id="s5">
<h2><span class="num">0 5</span>交付物</h2>
<p>确认后，我会在这个目录下产出（当前该目录已建好，侦察脚本与数据已在其中）：</p>
<div class="grid2">
<div class="card"><div class="t">主报告（单文件 HTML）</div><div class="d">离线可开、含封面/目录/图表/打印样式。核心是概率矩阵与它的置信区间，以及"哪一条证据最脆弱"。</div></div>
<div class="card"><div class="t">概率与情景表（CSV）</div><div class="d">(H,Y) 网格下的概率、区间、样本量、路径风险，可直接进 Excel。</div></div>
<div class="card"><div class="t">可复现脚本 + 原始数据</div><div class="d">取数、计算、回测三个脚本；数据落盘 CSV 带来源与抓取时间戳。</div></div>
<div class="card"><div class="t">预注册清单（Markdown）</div><div class="d">执行前写下特征、门槛、验证方式与失效条件，事后不可改。这是防自我欺骗的唯一硬约束。</div></div>
</div>
<p style="margin-top:22px">目录当前内容：<br>
<a href="../data/399006_daily_tencent.csv">data/399006_daily_tencent.csv</a>（3,983 日行情）·
<a href="../scripts/fetch_399006.py">scripts/fetch_399006.py</a>（取数与双源校验）·
<a href="../scripts/recon.py">scripts/recon.py</a>（侦察：跌幅、样本量、基准率）</p>
</section>

<hr class="sec">
<section id="s6">
<h2><span class="num">0 6</span>障碍与风险：你需要提前知道的八件事</h2>
<p>按严重程度排序，前三条是硬约束，无法通过更努力解决。</p>
<ul class="tight">
<li><b>1. 精度上限（硬）。</b>你要的那种条件（连跌 6 周 + 大跌 + 高位回撤 42%），在 16 年里只有 1–3 个先例。任何基于它的条件概率，95% 区间都会宽到 ±20 个百分点以上。我能给出"大概率在 45%–65% 之间"，给不出"72.3%"。如果有人给你小数点后一位的底部概率，那是把方法论当装饰。</li>
<li><b>2. 事件重叠（硬）。</b>3,983 个交易日不等于 3,983 个独立观测。连跌期间相邻两天的信息几乎相同，有效样本可能只有几十个。我已经用 60 日冷却期处理，但这会进一步压缩样本——精度和独立性是互斥的。</li>
<li><b>3. 定义敏感（硬）。</b>反弹门槛从 5% 改到 10%，答案从 64.7% 变成 23.5%。所以"反弹概率"这个说法在没有锁定 (H, Y) 之前是没有意义的。这也是它最容易被滥用的地方。</li>
<li><b>4. 结构性变化。</b>2010 年的创业板只有 100 多家公司、无涨跌幅 20% 制度、无注册制。把 2010–2015 的样本与今天同等加权，会系统性扭曲"历史分位"。处理方式：分时段加权 + 2019 年后子样本单独报一套结果（可能与你期望的方向不同）。</li>
<li><b>5. 数据缺口。</b>东财接口在本机被拒（已实测），北向资金 2024-08 起停止每日披露，创业板单板块 PE 需要换源。这意味着"外资抄底""估值见底"这两类常见论据，我只能给弱化版本或明确标注不可得。</li>
<li><b>6. 因果错位。</b>政策底通常先于市场底，"跌多了"只是价格信息，不包含流动性、信用、监管状态。历史上多次出现"跌到目标位还在跌 20%"的尾部（2024 年 2 月即典型）。模型对这类尾部天然迟钝。</li>
<li><b>7. 我的知识边界。</b>2026 年 6 月以来的这轮下跌，驱动因素不在我的训练数据里。如果 L4 的同构性检验要判断"这次像 2015 还是像 2024-02"，我需要现场检索宏观与政策信息，并对其可靠性单独标注——网上的归因文章质量参差，容易被当成事实。</li>
<li><b>8. 我不能替你定风险偏好。</b>同一个概率，对满仓和空仓的人含义完全相反，对能扛 40% 回撤和不能扛 15% 回撤的人更是两回事。概率是客观的，仓位是主观的，后者只能你定。</li>
</ul>
<div class="note">
<div class="h">关 于 结 论 可 能 不 好 看</div>
如果走完 L1–L4，模型在样本外打不赢基准率 42.2%，我会照实写"这套信号无效，可用基准率做粗略参考"。我不会为了给出一个像样的答案而放宽标准。提前说明，免得到时候你觉得我敷衍。
</div>
</section>

<hr class="sec">
<section id="s7">
<h2><span class="num">0 7</span>需要你拍板四件事</h2>
<p>这些不定下来，我算了也是白算——换一个参数，结论就换一个样子。</p>
<div class="q"><div class="h">Q1 反弹怎么定义？</div><div class="b">我建议主口径 <b>20 个交易日内、收盘反弹 ≥5%</b>，另附 3%/10% 与 60 日窗口作敏感性。<br>如果你的真实意图是"能不能回本/能不能解套"，那门槛应该按你的持仓成本设，我们得换一套算法。</div></div>
<div class="q"><div class="h">Q2 这个概率用来干什么？</div><div class="b">A. 决定现在要不要加仓 → 那我要多做风险层（先跌幅度、分批点位、最大回撤）。<br>B. 验证自己的判断对不对 → 只做 L1–L3 就够，重点是校准与证伪。<br>C. 写成给别人看的东西 → 需要额外做图表规范与免责声明。</div></div>
<div class="q"><div class="h">Q3 要不要做"这次像哪一次"的同构性分析？</div><div class="b">要做得查宏观、政策、流动性，耗时明显更长，而且归因本身有争议。不做的话，结论只能停留在"历史上类似跌幅之后如何"，会比较干。</div></div>
<div class="q"><div class="h">Q4 时间预算？</div><div class="b"><b>快速版</b>：L1 + L2 + 区间，半小时级，够你判断"感觉"值不值得下注。<br><b>完整版</b>：加 L3 模型回测与 L4 同构性，需要补齐 PE 数据与政策检索，产出更厚，但精度不会显著提升（受障碍 1 限制）。</div></div>
<p style="margin-top:24px">你回一句"按你建议的来"也可以，我就用推荐口径（20 日 / 5%，完整版，含同构性）直接开工。</p>
</section>

<footer>
<p><b>数据来源</b>：腾讯财经 ifzq.gtimg.cn（日线原始）、新浪财经（重叠期交叉校验，1,023 日收盘差异 &gt;0.05 元的为 0 日）、深圳证券交易所官方接口（两融余额、市场总貌）。<b>数据截止</b>：2026-10-29 收盘（2026-10-30 为当日盘中之前，未纳入）。<b>计算口径</b>：收盘价、前复权指数点位、不含分红与交易费用；分位数基于 2010-06-02 起全样本。</p>
<p><b>声明</b>：本文档为统计方法方案，所有数字为历史统计结果，<b>不构成投资建议</b>，也不预示未来收益。历史基准率不保证重现，极端行情下统计规律可能整体失效。投资决策及后果由投资者自行承担。</p>
<p style="margin-top:14px;color:#8b857c">生成于 2026-10-30 · 单文件离线文档 · 图表为内联 SVG，无外部依赖</p>
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
   for(var i=0;i<secs.length;i++){{
     if(secs[i]&&secs[i].getBoundingClientRect().top<160) idx=i;
   }}
   links.forEach(function(a,i){{a.classList.toggle('on',i===idx);}});
 }}
 document.addEventListener('scroll',onScroll,{{passive:true}});
 onScroll();
}})();
</script>
</body></html>"""

    html = html.replace("{{", "{").replace("}}", "}")
    html = cjk_quotes(html)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"written: {OUT}  ({len(html)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
