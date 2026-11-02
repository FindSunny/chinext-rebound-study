# -*- coding: utf-8 -*-
"""表头/单元格对齐检查器 v2。

把 th / td 的 class 归类为三种对齐意图：
  num  -> 右对齐
  ctr  -> 居中（含 ctr / tag-* / 热力图 r1..r10）
  txt  -> 左对齐（无类）
逐列比较表头与单元格的对齐意图，不一致即报错。
"""
import re
import lxml.html as LH

DEFAULT_FILES = [
    r"C:\SuoJianfei\deepseekharness\default\创业板反弹概率研究_2026-10\out\创业板反弹概率_快速版_2026-10.html",
    r"C:\SuoJianfei\deepseekharness\default\创业板反弹概率研究_2026-10\out\创业板反弹概率预测方案_2026-10.html",
    r"C:\SuoJianfei\deepseekharness\default\创业板反弹概率研究_2026-10\out\行业反弹顺序_2026-11.html",
]


def cat(cls):
    cls = cls or ""
    parts = cls.split()
    if "num" in parts:
        return "num"
    if "ctr" in parts:
        return "ctr"
    if any(p.startswith("tag-") for p in parts):
        return "ctr"
    if any(re.fullmatch(r"r\d+", p) for p in parts):
        return "ctr"
    return "txt"


def check(path):
    doc = LH.parse(path).getroot()
    name = path.split("\\")[-1]
    print("\n==", name)
    issues = 0
    for ti, t in enumerate(doc.iter("table")):
        heads = t.xpath(".//thead//th")
        rows = t.xpath(".//tbody/tr")
        if not heads:
            continue
        bad = []
        for ci, th in enumerate(heads):
            h = cat(th.get("class"))
            tcats = set()
            for r in rows:
                tds = r.findall("td")
                if ci < len(tds):
                    tcats.add(cat(tds[ci].get("class")))
            for c in tcats:
                if c != h:
                    bad.append((ci + 1, (th.text or "").strip()[:12], h, c))
                    break
        status = "OK" if not bad else "MISMATCH"
        print("   table%d  %d列 x %d行  %s" % (ti, len(heads), len(rows), status))
        if bad:
            issues += len(bad)
            for ci, txt, h, c in bad:
                print("      第 %d 列「%s」: 表头=%s, 内容=%s" % (ci, txt, h, c))
    return issues


total = sum(check(p) for p in DEFAULT_FILES)
print("\n" + ("全部对齐 ✓" if total == 0 else "共 %d 处不一致 ✗" % total))
