# -*- coding: utf-8 -*-
"""导出：1) 概率矩阵 CSV  2) DOCX 备份（便于转发）。"""
import os, csv, json
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(BASE, "data", "analysis_result.json"), encoding="utf-8"))
cur, base, conds, legs, analogs = R["current"], R["base"], R["conditions"], R["legs"], R["analogs"]
CSVOUT = os.path.join(BASE, "out", "probability_table.csv")
DOCXOUT = os.path.join(BASE, "out", "创业板反弹概率_快速版_2026-10.docx")


def f(v, d=4, sign=False):
    return "" if v is None else (("%+.*f" if sign else "%.*f") % (d, v))


# ---------------------------------------------------------------- CSV
rows = []
for gid, g in base.items():
    rows.append(dict(口径="无条件基准率", grid=gid, H=g["H"], Y=g["Y"], n=g["n"], k=g["k"],
                     p_raw=f(g["p"]), ci_lo=f(g["ci"][0]), ci_hi=f(g["ci"][1]),
                     p_post=f(g["p"]), cr_lo=f(g["ci"][0]), cr_hi=f(g["ci"][1]),
                     evidence_pp="0.0000",
                     maxdd_med="", terminal_med=f(g["terminal_median"]), newlow_p=""))
for cid in ("C1", "C2", "C3", "C4", "C5"):
    for gid, gd in conds[cid]["grids"].items():
        b = base[gid]
        rows.append(dict(口径="%s %s" % (cid, conds[cid]["label"]), grid=gid, H=b["H"], Y=b["Y"],
                         n=gd["n"], k=gd["k"],
                         p_raw=f(gd["p_raw"]), ci_lo=f(gd["ci"][0]), ci_hi=f(gd["ci"][1]),
                         p_post=f(gd["p_post"]), cr_lo=f(gd["cr"][0]), cr_hi=f(gd["cr"][1]),
                         evidence_pp=f((gd["p_post"] - b["p"]) * 100, 4, True),
                         maxdd_med=f(gd["maxdd_med"]), terminal_med=f(gd["terminal_med"]),
                         newlow_p=f(gd["newlow_p"])))

cols = ["口径", "grid", "H", "Y", "n", "k", "p_raw", "ci_lo", "ci_hi",
        "p_post", "cr_lo", "cr_hi", "evidence_pp", "maxdd_med", "terminal_med", "newlow_p"]
os.makedirs(os.path.dirname(CSVOUT), exist_ok=True)
with open(CSVOUT, "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
print("csv:", CSVOUT, len(rows), "rows")

# ---------------------------------------------------------------- DOCX
doc = Document()
st = doc.styles["Normal"]
st.font.name = "Microsoft YaHei"
st.font.size = Pt(10.5)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
for s in doc.sections:
    s.top_margin = s.bottom_margin = Cm(2.0)
    s.left_margin = s.right_margin = Cm(2.2)


def para(text, size=10.5, bold=False, color=None, space_after=6, align=None):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.bold = bold
    if color:
        r.font.color.rgb = RGBColor(*color)
    p.paragraph_format.space_after = Pt(space_after)
    if align:
        p.alignment = align
    return p


def h(text, size=14):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor(0x17, 0x18, 0x1a)
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    return p


def table(headers, data, widths=None, size=9):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, hd in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        r = cell.paragraphs[0].add_run(hd)
        r.bold = True
        r.font.size = Pt(size)
    for row in data:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v))
            r.font.size = Pt(size)
    if widths:
        for row in t.rows:
            for i, wd in enumerate(widths):
                row.cells[i].width = Cm(wd)
    return t


para("创业板反弹概率 · 快速版", 20, True, (0x17, 0x18, 0x1a), 2)
para("口径：20 个交易日内收盘反弹 ≥5%　|　基准日 2026-10-30 收盘 2,413.63　|　样本 3,984 交易日",
     9, False, (0x6f, 0x6a, 0x61), 14)

para("结论：概率约五成，但“见底”的证据不足", 13, True, (0xb4, 0x46, 0x2f), 6)
para("主口径 P(20 日内反弹 ≥5%) 收缩后约 49%，90% 可信区间 30.7%–67.6%；无条件基准率为 42.2%。"
     "20 日维度历史偏向给一次反弹，但拉到 60 日，四次历史类比里三次为负收益。短线的“会弹”与中期的“见底”是两个问题。",
     10.5, False, None, 8)
para("当前状态：距 2026-06-25 高点回撤 −44.8%（16 年第三深），已确认 6 个完整下跌周（累计 −28.44%），"
     "20 日跌幅 −26.6%（历史第 0.5 百分位），20 日年化波动率 38%（历史第 84 百分位）。", 10.5, False, None, 12)

h("一、概率矩阵")
data = [["无条件基准率", "—", "—", "3,964", "42.2%", "40.7–43.7%", "—"]]
for gid in ("G2",):
    for cid in ("C1", "C2", "C3", "C4", "C5"):
        g = conds[cid]["grids"][gid]
        if g["n"] == 0:
            data.append([conds[cid]["label"], cid, "0", "0", "无先例", "—", "—"])
            continue
        data.append([conds[cid]["label"], cid,
                     "%.1f%%" % (g["p_raw"] * 100),
                     str(g["n"]),
                     "%.1f%%" % (g["p_post"] * 100),
                     "%.1f–%.1f%%" % (g["cr"][0] * 100, g["cr"][1] * 100),
                     "%+.1fpp" % ((g["p_post"] - base["G2"]["p"]) * 100)])
table(["条件", "编号", "原始命中", "样本 n", "收缩后", "90%可信区间", "相对基准"], data,
      [6.0, 1.1, 1.9, 1.5, 1.8, 2.5, 1.6])
para("贝叶斯收缩：先验强度 n₀=15 个伪观测，先验均值取无条件基准率。收缩后所有条件收敛到 46.7%–55.9%，"
     "因为样本只有 3–16 个。C5（连跌≥5 周且 60 日≤−25%）历史上从未出现——即当前状态本身没有先例。",
     9, False, (0x4a, 0x45, 0x3f), 12)
para("敏感性：P(20 日 ≥10%) 收缩后 31.6%（基准 20.0%）；P(60 日 ≥10%) 49.4%（基准 42.6%）。", 9.5, False, None, 12)

h("二、同位置类比：回撤首次触及 −40% 之后")
d2 = []
for a in analogs:
    f20, f60, f120 = a["f20"], a["f60"], a["f120"]
    d2.append([a["touch_date"],
               "是" if f20["maxgain"] >= 0.05 else "否",
               "%+.1f%%" % (f20["maxgain"] * 100),
               "%+.1f%%" % (f20["maxdd"] * 100),
               "%+.1f%%" % (f60["terminal"] * 100) if f60 else "—",
               "%+.1f%%" % (f120["terminal"] * 100) if f120 else "—",
               "是" if f20["newlow"] else "否"])
table(["触及日", "20日涨≥5%", "20日最大涨幅", "20日最大回撤", "60日终点", "120日终点", "20日内破前低"],
      d2, [2.6, 2.0, 2.4, 2.4, 2.0, 2.0, 2.2])
para("四次里 3 次在 20 天内给到 +5% 以上；但 60 日终点 3 次为负。唯一失败的一次（2011-12-27）20 日内先跌 14.1% 并创新低。",
     9, False, (0x4a, 0x45, 0x3f), 12)

h("三、形态同构性：九段熊市")
d3 = []
for lg in legs:
    d3.append(["%s → %s" % (lg["peak"], lg["trough"]),
               "%.1f%%" % (lg["depth"] * 100), str(lg["dur_td"]),
               "%.1f%%" % (lg["speed_m"] * 100),
               "%.1f%%" % ((lg["vol_ann"] or 0) * 100),
               "%.2fx" % (lg["vol_shrink"] or 0),
               "进行中" if lg["open"] else ""])
table(["熊市段", "跌幅", "历时(交易日)", "速度(%/月)", "年化波动", "量能萎缩", "状态"],
      d3, [5.0, 1.6, 2.2, 2.2, 1.9, 1.7, 1.3])
para("当前段 −10.5%/月，快于任何一段慢熊（−1.6 至 −7.3%/月），慢于 2015 年 6–7 月的崩塌（−35.6%/月）。"
     "波动率 43.1% 仍处高位——底部通常伴随波动衰减，目前未见。缩量 0.81x 在历史上并不构成见底信号。",
     9, False, (0x4a, 0x45, 0x3f), 12)

h("四、对“加仓博弈”的含义（历史分布，非操作建议）")
table(["维度", "历史告诉你的"], [
    ["20 日内反弹 ≥5%", "约 49%（区间 31–68%），略好于抛硬币"],
    ["20 日内先跌 5% 以上", "4 次类比里 1 次先跌 14.1%"],
    ["60 日终点为正", "4 次里 1 次"],
    ["波动率位置", "38% 年化，历史 84 分位，未见衰减"],
    ["无先例状态", "C5 条件历史从未出现，任何“历史类似情况都如何”在此无样本基础"],
], [5.0, 11.4])
para("历史赔率结构是“五成概率赚 5%–20%，四分之一概率先亏 14%”，对分批建仓友好，对一次性打满不友好。"
     "另注意：反弹概率 ≠ 上涨概率。20 日终点中位数在历史样本里只有 +0.23%，能弹到 +5% 与能拿到这 5% 是两件事。",
     9.5, False, None, 12)

h("五、失效条件")
for t in ["流动性或信用事件驱动（均值回归统计整体失效，历史类比会系统性低估跌幅）；",
          "交易制度变化（涨跌幅、T+0、减持或退市规则）；",
          "指数编制规则大幅调整；",
          "单日跳空 >7%（样本内不存在，模型外推无效）。"]:
    p = doc.add_paragraph(t, style="List Bullet")
    p.paragraph_format.space_after = Pt(3)

h("六、局限与声明")
para("样本量是硬伤：C1 仅 4 个样本，C2 仅 3 个。5 条件 × 4 网格 = 20 个检验，纯随机也会出现约 1 个“显著”，"
     "因此未单独挑出任何显著结果。同构性只做价格形态，不含宏观与估值分位（按约定留给完整版）。"
     "不含分红、费用与冲击成本。", 9, False, (0x4a, 0x45, 0x3f), 6)
para("数据：创业板指 399006 日收盘，2010-06-02 至 2026-10-30，3,984 个交易日；腾讯 ifzq 取数，"
     "新浪在 1,023 个重叠交易日逐日比对，差异 >0.05 元的为 0 天。", 9, False, (0x6f, 0x6a, 0x61), 6)
para("声明：本文为历史统计研究，不构成投资建议，不预示未来收益。历史基准率不保证重现，"
     "极端行情下统计规律可能整体失效。据此操作，风险自担。", 9, True, (0xb4, 0x46, 0x2f), 6)
para("完整论证、图表与可复现脚本见 HTML 版《创业板反弹概率_快速版_2026-10.html》。", 8.5, False, (0x6f, 0x6a, 0x61), 0)

doc.save(DOCXOUT)
print("docx:", DOCXOUT)
