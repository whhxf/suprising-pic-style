#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图文结构机检：图数 / 正文长度 / 标题 / 收藏动机，四项对齐。

依据：2026-10-21 对 7 条图文爆款的拆解（见仓库 docs/内容结构拆解.md）。
三种原型的参数区间是从样本里量出来的，不是拍的。

用法:
    python structure_check.py cards.md --proto B --desc-len 391
    python structure_check.py cards.md --proto auto --desc-len 391

cards.md 里要有一行：
    收藏动机：以后要查

检查项:
  1. 图数落在原型的区间内
  2. 正文长度落在原型的区间内
  3. 标题含具体量词（数字 / 几个 / 几层 / 几步）
  4. 标题落在「降预期」或「提承诺」某一侧，不在中间
  5. 写了收藏动机
  6. 致命组合：图少 + 正文也短（读者拿不走东西）

退出码 0 = 通过，1 = 有问题。
"""
import argparse
import pathlib
import re
import sys

# 区间来自 2026-10 的 7 条图文爆款实测
PROTO = {
    "A": {"name": "观点卡",   "imgs": (1, 1), "desc": (850, 1100),
          "note": "1 张图，正文是内容本体"},
    "B": {"name": "清单图鉴", "imgs": (4, 9), "desc": (450, 800),
          "note": "每页一层，正文把条目名重述一遍给搜索用"},
    "C": {"name": "资料截图", "imgs": (3, 9), "desc": (0, 800),
          "note": "文档长图，正文可极短"},
}

# 降预期 / 提承诺，二选一
LOWER = ["真诚", "没有标题党", "不吹", "平平无奇", "亲测", "踩坑", "失败", "翻车", "普通"]
RAISE = ["一图看懂", "保姆级", "吃透", "万能", "底层", "完整", "全部", "合集", "清单", "全套", "一次讲清"]

QTY = re.compile(r"(\d+\s*(个|层|种|步|条|招|张|天|次|年|大|件|套))|([一二三四五六七八九十两]+(个|层|种|步|条|招|张))|这\s*[几\d]+\s*(位|个|种|家)")


def parse_cards(md):
    cards = re.findall(r"^##\s*\d+", md, re.M)
    m = re.search(r"收藏动机[：:]\s*(\S.*)", md)
    motive = m.group(1).strip() if m else ""
    t = re.search(r"标题[：:]\s*(\S.*)", md)
    title = t.group(1).strip() if t else ""
    return len(cards), title, motive


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--proto", default="auto", choices=["A", "B", "C", "auto"])
    ap.add_argument("--desc-len", type=int, default=-1, help="发布用描述的字数")
    a = ap.parse_args()

    md = pathlib.Path(a.path).read_text(encoding="utf-8")
    n, title, motive = parse_cards(md)
    if n == 0:
        sys.exit("没解析到卡片（每张用 ## 1 开头）")

    proto = a.proto
    if proto == "auto":
        # 按图数猜一个，再让区间去判
        proto = "A" if n == 1 else ("B" if n <= 9 else "C")
        print(f"按图数自动判定原型：{proto}")

    p = PROTO[proto]
    errs, warns = [], []

    lo, hi = p["imgs"]
    if not (lo <= n <= hi):
        errs.append(f"图数 {n}，{proto} 型应在 {lo}–{hi} 张")

    if a.desc_len >= 0:
        dlo, dhi = p["desc"]
        if not (dlo <= a.desc_len <= dhi):
            errs.append(f"正文 {a.desc_len} 字，{proto} 型应在 {dlo}–{dhi} 字")
        # 致命组合：图少 + 正文短
        if n <= 2 and a.desc_len < 700:
            errs.append(f"致命组合：只有 {n} 张图，正文才 {a.desc_len} 字 —— 读者拿不走东西")
    else:
        warns.append("没传 --desc-len，跳过正文长度检查")

    if title:
        if not QTY.search(title):
            errs.append(f"标题没有具体量词：「{title}」")
        hit_l = [w for w in LOWER if w in title]
        hit_r = [w for w in RAISE if w in title]
        if not hit_l and not hit_r:
            errs.append("标题既没降预期也没提承诺 —— 中间地带没人去")
        elif hit_l and hit_r:
            warns.append("标题同时降预期和提承诺，可能互相抵消")
    else:
        warns.append("没写「标题：」行，跳过标题检查")

    if not motive:
        errs.append("没写「收藏动机：」—— 答不上来就别做图文")

    print(f"原型 {proto} {p['name']}｜{n} 张图｜正文 {a.desc_len if a.desc_len >= 0 else '?'} 字")
    for w in warns:
        print("  ⚠️ ", w)
    for e in errs:
        print("  ✗ ", e)
    if not errs:
        print("  结构通过")
    sys.exit(0 if not errs else 1)


if __name__ == "__main__":
    main()
