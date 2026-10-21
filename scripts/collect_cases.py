#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""定期采集小红书爆款笔记，产出可入库的案例元数据。

依赖：本机 CDP 代理（默认 http://127.0.0.1:3456）+ 已登录的小红书浏览器会话。
     没有这个环境的话，本脚本跑不了 —— 它不是一个通用爬虫。

用法:
    python scripts/collect_cases.py --keywords "AI工具,AI教程,提示词模板" \
        --limit 26 --out cases/2026-11

做三件事：
  1. 按「最热」排序搜关键词，收集卡片（标题 / 作者 / 赞 / 带 token 的链接）
  2. 逐条打开详情，读类型、图片数、正文全文、标签、赞藏评
  3. 只保留图文笔记（type=normal），按赞排序，写成 cases/<月份>/NN-原型-标题/meta.json

⚠️ 只存元数据和正文前 200 字，不存图、不存全文。
   图是别人的版权作品，全文整段复制也不合适。要复刻请看 examples/README.md。
"""
import argparse
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:3456"

CARD_JS = """JSON.stringify([].slice.call(document.querySelectorAll("section.note-item")).map(function(s){
  var a=s.querySelector("a.cover"); var img=s.querySelector("img");
  var lines=(s.innerText||"").split("\\n").map(function(x){return x.trim();}).filter(Boolean);
  var likeEl=s.querySelector(".count");
  return {title:lines[0]||"", author:lines[1]||"", likes:likeEl?likeEl.innerText.trim():"",
          href:a?a.getAttribute("href"):"", img:img?img.src:""};
}))"""

NOTE_JS = """(function(){
  var d=window.__INITIAL_STATE__&&window.__INITIAL_STATE__.note&&window.__INITIAL_STATE__.note.noteDetailMap;
  if(!d) return JSON.stringify({err:"no-state"});
  var out=null;
  Object.keys(d).forEach(function(k){
    var n=d[k]&&d[k].note;
    if(n&&n.noteId&&!out){
      out={id:n.noteId,type:n.type,title:n.title||"",desc:n.desc||"",
           imgs:(n.imageList||[]).length,
           tags:(n.tagList||[]).map(function(t){return t.name;}),
           like:n.interactInfo&&n.interactInfo.likedCount,
           col:n.interactInfo&&n.interactInfo.collectedCount,
           cmt:n.interactInfo&&n.interactInfo.commentCount};
    }
  });
  return JSON.stringify(out||{err:"empty"});
})()"""


def _get(path, timeout=45):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _ev(target, expr, timeout=45):
    req = urllib.request.Request(BASE + "/eval?target=" + target, data=expr.encode("utf-8"),
                                 headers={"Content-Type": "text/plain;charset=utf-8"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", "replace")
    try:
        return json.loads(json.loads(raw).get("value"))
    except Exception:
        return None


def _newtab(url):
    return json.loads(_get("/new?url=" + urllib.parse.quote(url, safe=""))).get("targetId")


def _close(t):
    try:
        _get("/close?target=" + t)
    except Exception:
        pass


def _num(s):
    s = (s or "").strip()
    try:
        return int(float(s[:-1]) * 10000) if s.endswith("万") else int(s.replace(",", ""))
    except Exception:
        return 0


def collect(keywords, limit, outdir, rounds=3):
    cards = []
    for kw in keywords:
        u = ("https://www.xiaohongshu.com/search_result?keyword=%s&sort=popularity_descending"
             % urllib.parse.quote(kw))
        t = _newtab(u)
        time.sleep(7)
        for _ in range(rounds):
            r = _ev(t, CARD_JS)
            if isinstance(r, list):
                cards.extend(r)
            _ev(t, 'window.scrollBy(0,1400),"ok"')
            time.sleep(1.6)
        _close(t)
        print("  搜索 %s ok" % kw, file=sys.stderr)

    seen = {}
    for c in cards:
        h = c.get("href") or ""
        if "xsec_token=" not in h:
            continue
        n = _num(c.get("likes"))
        if h not in seen or n > seen[h]["n"]:
            seen[h] = {"n": n, **c}
    top = sorted(seen.values(), key=lambda x: -x["n"])[:limit]
    print("去重 %d，逐条判定 %d" % (len(seen), len(top)), file=sys.stderr)

    posts = []
    for i, c in enumerate(top, 1):
        t = _newtab("https://www.xiaohongshu.com" + c["href"])
        time.sleep(6.5)
        d = _ev(t, NOTE_JS)
        _close(t)
        if isinstance(d, dict) and d.get("type") == "normal":
            d["likes_card"] = c["n"]
            posts.append(d)
            print("  ✔ [%d] %d 图 %s 赞 %s" % (i, d["imgs"], c["n"], d["title"][:18]), file=sys.stderr)
        else:
            print("  · [%d] 跳过" % i, file=sys.stderr)

    posts.sort(key=lambda x: -(x.get("likes_card") or 0))
    out = pathlib.Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    for i, p in enumerate(posts, 1):
        safe = re.sub(r"[^\w\u4e00-\u9fa5]+", "-", (p["title"] or "无题"))[:20].strip("-")
        d = out / ("%02d-%s" % (i, safe or "无题"))
        d.mkdir(exist_ok=True)
        (d / "meta.json").write_text(json.dumps({
            "记录日期": time.strftime("%Y-%m-%d"),
            "平台": "小红书",
            "标题": p["title"],
            "赞": p.get("like"),
            "藏": p.get("col"),
            "评": p.get("cmt"),
            "图数": p["imgs"],
            "正文长度": len(p["desc"] or ""),
            "正文开头": (p["desc"] or "")[:200],
            "标签": p["tags"],
            "结构原型": "待判定（A 观点卡 / B 清单图鉴 / C 资料截图）",
            "来源": "站内「最热」排序",
            "图片": "不入库，版权归原作者"
        }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入 %d 条到 %s" % (len(posts), outdir))
    return posts


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--keywords", required=True, help="逗号分隔")
    ap.add_argument("--limit", type=int, default=26, help="逐条判定的上限（每条约 7 秒）")
    ap.add_argument("--out", required=True, help="如 cases/2026-11")
    a = ap.parse_args()
    collect([k.strip() for k in a.keywords.split(",") if k.strip()], a.limit, a.out)
