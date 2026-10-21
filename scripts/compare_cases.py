#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对比不同月份案例库的原型分布，看规律有没有变。

用法:
    python scripts/compare_cases.py                 # 看全部月份的分布
    python scripts/compare_cases.py 2026-10 2026-11 # 两个月对比

为什么要有这个脚本:
    拆解结论是快照。三个月后再搜，同一个题头部会换人。
    这个脚本把「结论」变成可重跑的对照实验：
    如果 A 型占比突然涨了，说明观点卡在变强；如果 C 型跌了，说明资料型在退潮。
    不重跑，就永远在用一份过期的经验。
"""
import json
import pathlib
import sys
from collections import Counter

def load(month=None):
    root = pathlib.Path("cases")
    dirs = [root/month] if month else sorted(p for p in root.iterdir() if p.is_dir())
    rows = []
    for d in dirs:
        for f in sorted(d.glob("*/meta.json")):
            try:
                m = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            proto = (m.get("结构原型") or "待判定").split()[0]
            rows.append({
                "month": d.name, "proto": proto,
                "imgs": m.get("图数") or 0,
                "desc": m.get("正文长度") or 0,
                "title": m.get("标题") or "",
            })
    return rows

def report(rows, label):
    if not rows:
        print(f"{label}: 没有数据")
        return
    c = Counter(r["proto"] for r in rows)
    total = len(rows)
    print(f"\n{label}｜共 {total} 条")
    for proto, n in sorted(c.items()):
        sub = [r for r in rows if r["proto"] == proto]
        avg_img = sum(r["imgs"] for r in sub) / len(sub)
        avg_desc = sum(r["desc"] for r in sub) / len(sub)
        print(f"  {proto}: {n} 条（{n/total:.0%}）｜平均 {avg_img:.1f} 图 / {avg_desc:.0f} 字")

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        a, b = load(sys.argv[1]), load(sys.argv[2])
        report(a, sys.argv[1]); report(b, sys.argv[2])
        ca = Counter(r["proto"] for r in a); cb = Counter(r["proto"] for r in b)
        print("\n变化：")
        for proto in sorted(set(ca) | set(cb)):
            pa = ca.get(proto, 0) / len(a) * 100 if a else 0
            pb = cb.get(proto, 0) / len(b) * 100 if b else 0
            arrow = "↑" if pb > pa + 5 else ("↓" if pb < pa - 5 else "→")
            print(f"  {proto}: {pa:.0f}% → {pb:.0f}%  {arrow}")
    else:
        rows = load()
        for m in sorted({r["month"] for r in rows}):
            report([r for r in rows if r["month"] == m], m)
        report(rows, "全部")
