# -*- coding: utf-8 -*-
"""生成《历次熊底后的行业反弹顺序》单文件 HTML（含热力图）。

数据：data/sectors_daily.csv（10 个中证全指一级行业 + 沪深300 + 创业板指）
      data/new_boards_daily.csv（科创50、科创50ETF、双创ETF、创业板50ETF、芯片ETF、中证TMT）
底部：创业板指自峰值跌 >=30% 进入熊市段，自低点反弹 >=20% 结束，取该段低点。
"""
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out", "行业反弹顺序_2026-11.html")

PAPER, INK, MUTED = "#f7f5f1", "#17181a", "#6f6a61"
TEAL, RUST, GOLD = "#0b6e6e", "#b4462f", "#a67c1f"
RULE = "#d9d4cb"

px = pd.read_csv(os.path.join(BASE, "data", "sectors_daily.csv"), parse_dates=["date"]).set_index("date")
nb = pd.read_csv(os.path.join(BASE, "data", "new_boards_daily.csv"), parse_dates=["date"]).set_index("date")
alldf = px.join(nb, how="outer").sort_index().ffill()

SECTORS = ["能源", "材料", "工业", "可选消费", "主要消费", "医药", "金融", "信息", "通信", "公用事业"]
NEWB = ["科创50", "科创50ETF", "双创ETF", "创业板50ETF", "芯片ETF", "中证TMT"]

hs = alldf["创业板指"].values
n = len(hs)
legs, state, peak, trough = [], "bull", 0, None
for i in range(1, n):
    if state == "bull":
        if hs[i] > hs[peak]:
            peak = i
        if hs[i] / hs[peak] - 1 <= -0.30:
            state, trough = "bear", i
    else:
        if hs[i] < hs[trough]:
            trough = i
        if hs[i] / hs[trough] - 1 >= 0.20:
            legs.append((peak, trough))
            state = "bull"
            peak = trough + int(np.argmax(hs[trough:i + 1]))
if state == "bear":
    legs.append((peak, trough))

MAXH = 120
bottoms = [(p, t) for p, t in legs if t + MAXH < n]
bdate = [alldf.index[t].strftime("%Y-%m-%d") for _, t in bottoms]


def fwd(col, t, H):
    s = alldf[col].values
    if t + H >= len(s) or np.isnan(s[t]) or np.isnan(s[t + H]):
        return np.nan
    return s[t + H] / s[t] - 1


rank = {}
for bd, (p, t) in zip(bdate, bottoms):
    v = pd.Series({nm: fwd(nm, t, 20) for nm in SECTORS}).dropna()
    rank[bd] = v.rank(ascending=False)
rt = pd.DataFrame(rank)
avg = rt.mean(axis=1).sort_values()
sd = rt.std(axis=1)

# 时代切分
pre_cols = [c for c in rt.columns if c < "2020"]
post_cols = [c for c in rt.columns if c >= "2020"]
pre = rt[pre_cols].mean(axis=1)
post = rt[post_cols].mean(axis=1)

# 排序相关
cc = rt.corr(method="spearman")
blk1 = cc.loc[pre_cols, pre_cols].values[np.triu_indices(len(pre_cols), k=1)]
blk2 = cc.loc[post_cols, post_cols].values[np.triu_indices(len(post_cols), k=1)]
cross = cc.loc[pre_cols, post_cols].values.ravel()
r_in_pre, r_in_post, r_cross = np.nanmean(blk1), np.nanmean(blk2), np.nanmean(cross)

# 新板块：仅最近两个底部
recent = [c for c in rt.columns if c >= "2022"][:2]
new_rank = {}
for bd in recent:
    t = int(alldf.index.searchsorted(pd.Timestamp(bd)))
    v = pd.Series({nm: fwd(nm, t, 20) for nm in SECTORS + NEWB}).dropna()
    new_rank[bd] = v.rank(ascending=False).sort_values()


def cell_class(r):
    r = int(round(r))
    return "r%d" % max(1, min(10, r))


rows_hm = ""
for nm in avg.index:
    cells = "".join('<td class="%s">%d</td>' % (cell_class(rt.loc[nm, c]), rt.loc[nm, c]) for c in rt.columns)
    tag = "稳定" if sd[nm] <= 1.65 else ("轮动" if sd[nm] >= 2.2 else "半稳定")
    cls = "tag-s" if tag == "稳定" else ("tag-r" if tag == "轮动" else "tag-m")
    rows_hm += ('<tr><td class="nm">%s</td>%s<td class="avg">%.1f</td>'
                '<td class="sd">%.1f</td><td class="%s">%s</td></tr>'
                % (nm, cells, avg[nm], sd[nm], cls, tag))

rows_era = ""
for nm in avg.index:
    d = post[nm] - pre[nm]
    cls = "neg" if d > 1.5 else ("pos" if d < -1.5 else "")
    rows_era += ('<tr><td class="nm">%s</td><td class="num">%.1f</td><td class="num">%.1f</td>'
                 '<td class="num %s">%+.1f</td></tr>' % (nm, pre[nm], post[nm], cls, d))

rows_new = ""
for nm in SECTORS + NEWB:
    a = new_rank[recent[0]].get(nm, np.nan)
    b = new_rank[recent[1]].get(nm, np.nan)
    star = " new" if nm in NEWB else ""
    rows_new += ('<tr class="%s"><td class="nm">%s</td><td class="num">%s</td><td class="num">%s</td></tr>'
                 % (star.strip(), nm, "%d" % a if not np.isnan(a) else "—",
                    "%d" % b if not np.isnan(b) else "—"))

collist = "".join("<th>%s</th>" % c[2:] for c in rt.columns)
nbot = len(rt.columns)

html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>历次熊底后的行业反弹顺序 · 2026-11</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:{PAPER};color:{INK};
 font:16px/1.75 -apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
 -webkit-font-smoothing:antialiased}}
.wrap{{max-width:980px;margin:0 auto;padding:56px 32px 100px}}
.kicker{{font-size:12px;letter-spacing:.2em;color:{RUST};margin-bottom:18px}}
h1{{font-size:clamp(28px,4vw,42px);line-height:1.22;margin:0 0 18px;letter-spacing:-.02em}}
.sub{{font-size:18px;color:#4a453f;line-height:1.72;max-width:42em;margin:0 0 26px}}
.meta{{display:flex;flex-wrap:wrap;gap:26px;font-size:13px;color:{MUTED};
 border-top:1px solid {RULE};border-bottom:1px solid {RULE};padding:14px 0;margin-bottom:8px}}
.meta b{{color:{INK};font-weight:600;display:block;font-size:15px}}
h2{{font-size:22px;margin:56px 0 6px;font-weight:700}}
h2 .num{{font-size:12px;letter-spacing:.16em;color:{RUST};display:block;margin-bottom:7px;font-weight:600}}
p{{margin:13px 0}}
.note{{background:rgba(11,110,110,.055);border:1px solid rgba(11,110,110,.18);padding:16px 20px;margin:22px 0;font-size:15px}}
.note .h{{font-size:11px;letter-spacing:.16em;color:{TEAL};margin-bottom:7px;font-weight:600}}
.warn{{background:rgba(166,124,31,.07);border:1px solid rgba(166,124,31,.25);padding:16px 20px;margin:22px 0;font-size:15px}}
.warn .h{{font-size:11px;letter-spacing:.16em;color:#7d5c14;margin-bottom:7px;font-weight:600}}
table{{width:100%;border-collapse:collapse;margin:20px 0;font-size:14px}}
th{{text-align:left;font-size:11.5px;letter-spacing:.06em;color:{MUTED};font-weight:600;
 border-bottom:1.5px solid #c9c3b9;padding:8px 6px;white-space:nowrap}}
th:not(:first-child){{text-align:center}}
td{{padding:6px;border-bottom:1px solid #e6e1d8;font-variant-numeric:tabular-nums}}
td.nm{{font-weight:600;white-space:nowrap}}
td.num{{text-align:right;white-space:nowrap}}
table.hm td:not(.nm):not(.avg):not(.sd):not(.tag-s):not(.tag-r):not(.tag-m){{
 text-align:center;width:58px;font-weight:600;color:{INK}}}
table.hm td.avg,table.hm td.sd{{text-align:center;color:{MUTED};width:56px}}
.r1{{background:rgba(11,110,110,.80);color:#fff!important}}
.r2{{background:rgba(11,110,110,.58);color:#fff!important}}
.r3{{background:rgba(11,110,110,.34);color:{INK}!important}}
.r4,.r5,.r6,.r7{{background:rgba(23,24,26,.05);color:{INK}!important}}
.r8{{background:rgba(180,70,47,.16);color:{INK}!important}}
.r9{{background:rgba(180,70,47,.32);color:{INK}!important}}
.r10{{background:rgba(180,70,47,.50);color:#fff!important}}
.tag-s{{color:{TEAL};text-align:center;font-size:12px}}
.tag-m{{color:{MUTED};text-align:center;font-size:12px}}
.tag-r{{color:{RUST};text-align:center;font-size:12px}}
.neg{{color:{RUST}}} .pos{{color:{TEAL}}}
tr.new td{{background:rgba(166,124,31,.07)}}
figcaption,.cap{{font-size:12.5px;color:{MUTED};margin:2px 0 24px}}
ul.tight{{margin:10px 0;padding-left:20px}}
ul.tight li{{margin:8px 0}}
ol.steps{{counter-reset:s;list-style:none;padding:0;margin:18px 0}}
ol.steps>li{{counter-increment:s;position:relative;padding:12px 0 12px 42px;border-bottom:1px solid #e6e1d8}}
ol.steps>li::before{{content:counter(s);position:absolute;left:0;top:12px;width:24px;height:24px;
 border:1px solid {TEAL};color:{TEAL};border-radius:50%;display:flex;align-items:center;
 justify-content:center;font-size:12px;font-weight:600}}
footer{{border-top:1px solid {RULE};margin-top:56px;padding-top:20px;font-size:12.5px;color:{MUTED};line-height:1.7}}
@media (max-width:760px){{
 .wrap{{padding:36px 18px 70px}}
 table{{font-size:12px}} th,td{{padding:4px 3px}}
 table.hm td:not(.nm){{
   width:auto}}
}}
@media print{{
 body{{background:#fff;font-size:10pt}}
 h2{{page-break-after:avoid}}
 table,.note,.warn{{page-break-inside:avoid}}
 @page{{size:A4;margin:14mm}}
}}
</style></head>
<body><div class="wrap">

<div class="kicker">历 史 统 计 · 不 构 成 投 资 建 议</div>
<h1>熊底之后，谁先反弹？</h1>
<p class="sub">创业板指 6 次熊底之后，10 个中证一级行业的 20 日涨幅排名。<b>结论是：两端稳定，中间随主线轮动。</b>没有一条固定的"操作顺序"。</p>
<div class="meta">
  <div><b>{nbot}</b>次熊底</div>
  <div><b>10</b>个行业指数</div>
  <div><b>2015-07 → 2024-02</b>样本区间</div>
  <div><b>{alldf.index[0].date()} → {alldf.index[-1].date()}</b>数据区间</div>
</div>

<h2><span class="num">0 1</span>先看结论</h2>
<ol class="steps">
<li><div><b>稳定的只有两端。</b>信息（平均第 3）、工业（第 3）长期靠前；<b>金融（第 9.2）稳定垫底</b>。中间 6 个行业的位置由当期主线决定。</div></li>
<li><div><b>"抄底先买券商"在这份数据里站不住。</b>金融行业指数六次里四次排最后，两次在 120 日内都没涨到 +10%。（注：全指金融里银行占大头，不能完全代表券商。）</div></li>
<li><div><b>顺序随市场结构变化。</b>2015–2018 与 2022–2024 两个时代的排序相关系数只有 <b>{r_cross:.2f}</b>，而同代内部是 {r_in_pre:.2f} / {r_in_post:.2f}。能源从第 9 升到第 4，材料升 3 位——那是商品周期的功劳，不是"规律"。</div></li>
</ol>

<h2><span class="num">0 2</span>热力图：谁强谁弱，一眼可见</h2>
<table class="hm">
<thead><tr><th>行业</th>{collist}<th>平均</th><th>标准差</th><th>性质</th></tr></thead>
<tbody>{rows_hm}</tbody></table>
<p class="cap">单元格内为按 20 日涨幅的排名（1 = 最强，10 = 最弱）。绿色系 = 前三，红色系 = 后三。<b>标准差小</b>说明该行业的名次稳定，<b>大</b>说明随行情变化。</p>

<div class="note">
<div class="h">怎 么 读</div>
工业的标准差只有 1.1、金融 1.6——这两头的名次几乎可以预期。而信息的标准差 2.9：它在 2015-07 排第 8，在之后五次里四次进前二。<b>均值掩盖了它的跳跃性</b>，只看"平均排名"会误判。
</div>

<h2><span class="num">0 3</span>两个时代：顺序不是常量</h2>
<table>
<thead><tr><th>行业</th><th class="num">2015–2018 平均</th><th class="num">2022–2024 平均</th><th class="num">变化</th></tr></thead>
<tbody>{rows_era}</tbody></table>
<p class="cap">负值 = 在新时期名次上升（更强）；正值 = 名次下降。能源 −5.0、材料 −3.0 是最大的两处位移，对应 2021–22 年商品周期。</p>

<h2><span class="num">0 4</span>加上科创板与双创</h2>
<p>科创板 2019 年才开市，只有 2022-04 和 2024-02 两个熊底可对照。把新板块放进同一张排序表：</p>
<table>
<thead><tr><th>标的</th><th class="num">{recent[0]}</th><th class="num">{recent[1] if len(recent)>1 else '—'}</th></tr></thead>
<tbody>{rows_new}</tbody></table>
<p class="cap">带底色的行为新增的科创板/双创标的。两次差异极大：2022 年科技内部严重分化（芯片第 4、科创50 第 5，但双创与创业板50 掉到第 12–13）；2024 年科技全线包揽前八。</p>

<div class="warn">
<div class="h">新 板 块 是 放 大 器，不 是 导 航 仪</div>
2024-02 底部之后，科创50 前 5 日 +13.4%（快于创业板指 +12.6%），但 60 日只有 +13.4%，而创业板指是 +20.0%。<b>它放大当期主线的涨幅，不决定顺序。</b>押"顺序"不如押"主线"。
</div>

<h2><span class="num">0 5</span>局限：这份分析能支撑什么</h2>
<ul class="tight">
<li><b>只有 {nbot} 个熊底。</b>2015 年占了其中两个（7 月 7 日、9 月 15 日），独立事件实际只有 5 个左右。任何"规律"都应视为倾向而非规律。</li>
<li><b>排序相关性 {r_cross:.2f}（跨时代）</b>低于常用的 0.5 门槛。样本内一致性尚可，外推能力有限。</li>
<li><b>金融 ≠ 券商。</b>中证全指金融由银行主导，"券商先动"的传说需要单独用券商 ETF 验证（512880 自 2016 年起，只覆盖 3 个底部）。</li>
<li><b>只看 20 日。</b>换成 60 日或 120 日，排序会变——短期反弹的领跑者未必是中期赢家。</li>
<li><b>底部由规则定义</b>（创业板跌 30% / 反弹 20%），换阈值底部日期会变，结论可能随之变化。</li>
</ul>

<div class="note">
<div class="h">对 实 际 操 作 的 含 义</div>
先判断当期主线是什么，再选板块：主线是 AI/半导体，科创50、芯片靠前（如 2024）；主线是资源/实物资产，能源、材料靠前（如 2022）。<b>"按固定顺序操作"没有数据支持。</b>
</div>

<footer>
<p><b>数据</b>：中证全指一级行业指数（000986–000995）10 个；科创50（000688）、科创50ETF（588000）、双创ETF（159781）、创业板50ETF（159949）、芯片ETF（512760）、中证TMT（000998）；基准为创业板指（399006）。行情经腾讯 ifzq 接口取得，前复权。</p>
<p><b>口径</b>：熊底 = 创业板指自峰值下跌 ≥30% 进入熊市段、自低点反弹 ≥20% 结束，取该段最低收盘日；收益 = 底部收盘至第 20 个交易日收盘。</p>
<p><b>声明</b>：历史统计，不构成投资建议。样本量极小，排序结果可能由随机性主导。</p>
</footer>
</div></body></html>"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("written:", OUT)
print("熊底:", bdate)
print("跨时代相关 %.2f | 组内 %.2f / %.2f" % (r_cross, r_in_pre, r_in_post))
