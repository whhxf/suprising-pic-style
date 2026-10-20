#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验 styles.json 结构。

用法:
    python scripts/check_styles.py [path/to/styles.json]

退出码 0 = 通过，1 = 有问题。
"""
import json
import pathlib
import re
import sys

REQUIRED = ["id", "name", "when_to_use", "layout", "typography",
            "color", "elements", "prompt_template", "avoid", "needs_face"]
LIST_FIELDS = ["when_to_use", "elements", "avoid"]


def main():
    p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "styles.json")
    if not p.exists():
        sys.exit(f"找不到 {p}")

    d = json.loads(p.read_text(encoding="utf-8"))
    styles = d.get("styles") or []
    errs = []

    if not styles:
        sys.exit("styles 为空")

    ids = set()
    for i, s in enumerate(styles, 1):
        tag = s.get("id", f"#{i}")
        for k in REQUIRED:
            if k not in s:
                errs.append(f"{tag}: 缺字段 {k}")
        for k in LIST_FIELDS:
            v = s.get(k)
            if k in s and (not isinstance(v, list) or not v):
                errs.append(f"{tag}: {k} 必须是非空数组")
        if s.get("id") in ids:
            errs.append(f"{tag}: id 重复")
        ids.add(s.get("id"))
        pt = s.get("prompt_template") or ""
        if not re.search(r"\{[^}]{1,12}\}", pt):
            errs.append(f"{tag}: prompt_template 里没有可填的占位（如 {{性别}}）")
        if not isinstance(s.get("needs_face"), bool):
            errs.append(f"{tag}: needs_face 必须是布尔值")

    if not d.get("decision_tree"):
        errs.append("缺 decision_tree")

    print(f"风格 {len(styles)} 条｜问题 {len(errs)} 处")
    for e in errs:
        print("  -", e)
    if not errs:
        print("  结构通过")
    sys.exit(0 if not errs else 1)


if __name__ == "__main__":
    main()
