#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按「出血框」裁图：把生成图当相框，裁掉四周的出血区，得到精确比例 + 无水印。

两种用法：

  1) 只裁水印（比例会变）
     python strip_watermark.py <目录> --bottom 88

  2) 出血框，裁完是精确 3:4（推荐）
     python strip_watermark.py <目录> --ratio 3:4

出血规格（1024×1536 画布 → 3:4）：
    目标高 = 1024 / (3/4) = 1365
    总裁剪 = 1536 - 1365 = 171
    下裁 87（水印上沿在 y≈1466，裁完底边 1449，留 17px 余量）
    上裁 84（标题必须从 y≥84 开始，否则会被切）
    结果 1024×1365，比例 0.7502

⚠️ 前提：提示词里必须先写「上下各留 10% 空白、内容集中在中间 80%」。
   先裁后补提示词，一定切到字。

合规提醒：
    裁掉平台水印后，发布文案里补一句「配图由 AI 生成」。
    《人工智能生成合成内容标识办法》要求显式标识。不要用模糊涂抹去水印。
"""
import argparse
import pathlib
import sys

from PIL import Image

WM_MIN_BOTTOM = 70   # 水印至少要裁掉这么多


def plan(w, h, ratio, top, bottom):
    """算出 top/bottom 的裁切量。"""
    if ratio:
        num, den = [float(x) for x in ratio.split(":")]
        target_h = round(w * den / num)
        total = h - target_h
        if total < WM_MIN_BOTTOM:
            sys.exit(f"比例 {ratio} 只裁 {total}px，不够盖住水印（需 ≥{WM_MIN_BOTTOM}）")
        bottom = max(WM_MIN_BOTTOM, min(total, bottom or total))
        top = total - bottom
    return int(top or 0), int(bottom or 0)


def run(p, top, bottom, dry):
    im = Image.open(p)
    w, h = im.size
    if h - top - bottom < 200:
        print(f"  跳过（太矮）：{p.name}")
        return None
    box = (0, top, w, h - bottom)
    new = im.crop(box)
    nw, nh = new.size
    r = nw / nh
    tag = "%.4f" % r
    if not dry:
        out = p.with_name(p.stem + "-clean" + p.suffix)
        new.save(out)
        print(f"  {p.name}  {w}x{h} -上{top}/下{bottom} → {nw}x{nh}  比例 {tag}  →  {out.name}")
        return out
    print(f"  {p.name}  {w}x{h} -上{top}/下{bottom} → {nw}x{nh}  比例 {tag}（dry-run）")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--ratio", help="目标比例，如 3:4。给了就自动算上下裁切量")
    ap.add_argument("--top", type=int, default=0)
    ap.add_argument("--bottom", type=int, default=88)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    p = pathlib.Path(a.path)
    files = (sorted(p.glob("*.png")) + sorted(p.glob("*.jpg"))) if p.is_dir() else [p]
    files = [f for f in files if "-clean" not in f.stem and not f.name.startswith("_")]
    if not files:
        sys.exit("没找到图片")

    w0, h0 = Image.open(files[0]).size
    top, bottom = plan(w0, h0, a.ratio, a.top, a.bottom)
    print(f"出血框：画布 {w0}x{h0}｜上裁 {top}｜下裁 {bottom}｜{len(files)} 张")
    if a.ratio:
        print(f"目标 {a.ratio}｜结果 {w0}x{h0-top-bottom}｜比例 {(w0/(h0-top-bottom)):.4f}")
    if top >= 60:
        print(f"⚠️  要上裁 {top}px。标题大概率被切 —— 模型总把字画在最顶上。")
        print(f"   建议改用 1024x1440 画布重出，那样上裁为 0。")

    done = 0
    for f in files:
        if run(f, top, bottom, a.dry_run):
            done += 1
    print(f"完成 {done} 张")
    print("提醒：发布文案里补一句「配图由 AI 生成」")


if __name__ == "__main__":
    main()
