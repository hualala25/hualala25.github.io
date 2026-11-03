#!/usr/bin/env python3
"""
docx -> Markdown 转换器（通用课程作业 / 学年论文）

从 OOXML 直接解析，不依赖 python-docx：

  * 段落层级优先用 pStyle 判定（策划案等有样式的文档）
  * 无 pStyle 时回退到 run 字号判定（学年论文等纯排版文档）
    36(18pt) -> 标题   24(12pt) -> 一级   21(10.5pt) -> 正文/二级   18(9pt) -> 小字
  * 表格按首行表头转 Markdown 表格
  * 内嵌图片按所在段落顺序编号，映射到图床 URL

用法:
  python3 docx_to_md.py <input.docx> <output.md> \\
      --title ... --summary ... --category ... --course ... --date ... \\
      --tags a,b,c --cover URL [--figure-prefix NAME] [--figure-base URL]
"""

import argparse
import html
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

SUBHEAD_RE = re.compile(r"^[（(][一二三四五六七八九十]+[)）]")
REF_RE = re.compile(r"^\[(\d+)\]\s*")


# ---------- OOXML 解析 ----------

# <w:t> 的精确匹配：不能写成 <w:t[^>]*>，否则会误抓 <w:tab/> <w:tabs> <w:tbl> 等
T_RE = re.compile(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", re.S)
# 域代码标记：目录（TOC）等自动生成内容靠它识别
FLD_RE = re.compile(r"<w:(fldChar|instrText)\b")


def para_text(p):
    """段落纯文本，保留制表符。"""
    out = []
    for node in p.iter():
        if node.tag == W + "t":
            out.append(node.text or "")
        elif node.tag == W + "tab":
            out.append("\t")
        elif node.tag in (W + "br", W + "cr"):
            out.append("\n")
    return "".join(out)


def para_size(p):
    sizes = [int(sz.get(W + "val")) for sz in p.iter(W + "sz") if sz.get(W + "val")]
    return max(sizes) if sizes else 0


def para_style(p):
    st = p.find(f"{W}pPr/{W}pStyle")
    return st.get(W + "val") if st is not None else ""


def para_runs(p):
    """返回 [(文本, 是否斜体, 是否加粗)]，用于保留真强调。"""
    runs = []
    for r in p.findall(W + "r"):
        text = para_text(r).strip()
        if not text:
            continue
        rpr = r.find(W + "rPr")
        italic = bold = False
        if rpr is not None:
            i = rpr.find(W + "i")
            italic = i is not None and i.get(W + "val") not in ("0", "false")
            b = rpr.find(W + "b")
            bold = b is not None and b.get(W + "val") not in ("0", "false")
        runs.append((text, italic, bold))
    return runs


def read_document(docx_path):
    """返回 (blocks, meta)。blocks 是结构化块列表。"""
    with zipfile.ZipFile(docx_path) as z:
        xml = z.read("word/document.xml")
        try:
            rels_xml = z.read("word/_rels/document.xml.rels").decode("utf-8")
        except KeyError:
            rels_xml = ""
    root = ET.fromstring(xml)
    body = root.find(W + "body")

    relmap = dict(re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"', rels_xml))

    blocks = []
    figures = []

    for node in body:
        if node.tag == W + "p":
            text = para_text(node).strip()
            style = para_style(node)
            size = para_size(node)
            embeds = [e.get(R + "embed") for e in node.iter() if e.get(R + "embed")]

            # 域代码段落（TOC 目录等自动生成内容）整段丢弃
            raw = ET.tostring(node, encoding="unicode")
            if FLD_RE.search(raw):
                continue

            if embeds:
                for eid in embeds:
                    target = relmap.get(eid, "")
                    fname = target.split("/")[-1]
                    if fname:
                        figures.append(fname)
                blocks.append({"type": "figure", "files": [relmap.get(e, "") for e in embeds]})
                continue

            if not text:
                continue
            blocks.append({
                "type": "p",
                "text": text,
                "style": style,
                "size": size,
                "runs": para_runs(node),
            })
        elif node.tag == W + "tbl":
            rows = []
            for tr in node.findall(W + "tr"):
                cells = []
                for tc in tr.findall(W + "tc"):
                    parts = []
                    for p in tc.findall(W + "p"):
                        t = para_text(p).strip()
                        if t:
                            parts.append(t)
                    cells.append(" / ".join(parts))
                if cells:
                    rows.append(cells)
            if rows:
                blocks.append({"type": "table", "rows": rows})

    return blocks, figures


# ---------- 层级判定 ----------

def classify(blocks):
    """把块序列切成带层级的结构。返回 (meta, items)。"""
    meta = {
        "title": "", "author": "", "student_id": "", "major": "",
        "date_text": "", "affiliation": "", "abstract": "", "keywords": [],
    }
    items = []
    cover_fields = []
    in_refs = False
    fig_no = 0
    tbl_no = 0

    for b in blocks:
        if b["type"] == "figure":
            fig_no += 1
            items.append({"level": "figure", "no": fig_no, "files": b["files"]})
            continue
        if b["type"] == "table":
            tbl_no += 1
            items.append({"level": "table", "no": tbl_no, "rows": b["rows"]})
            continue

        text, style, size = b["text"], b["style"], b["size"]

        # 封面信息块：项目类型 / 姓名 / 学号 / 专业班级 / 日期
        # 键名里的空格可能是半角或全角，统一去掉再比对
        # 这些键连续出现，靠白名单持续命中，不靠位置开关
        if size >= 21 and "：" in text:
            key, _, val = text.partition("：")
            key = re.sub(r"\s+", "", key)
            if key in ("项目类型", "姓名", "学号", "专业班级", "日期"):
                if key == "项目类型":
                    meta["project_type"] = val.strip()
                elif key == "姓名":
                    meta["author"] = val.strip()
                elif key == "学号":
                    meta["student_id"] = val.strip()
                elif key == "专业班级":
                    meta["major"] = val.strip()
                elif key == "日期":
                    meta["date_text"] = val.strip()
                cover_fields.append((key, val.strip()))
                continue

        # 标题：字号最大且带样式的第一个非空段
        if not meta["title"]:
            if (style in ("33", "a3", "Title") and len(text) < 60) or size >= 30:
                meta["title"] = text
                continue

        # 作者署名：紧跟标题之后的第一行（标题后第 1、2 段内）
        # 章节名（引言 / 结论 / 参考文献 等）不算署名
        SECTION_WORDS = {
            "引言", "绪论", "前言", "结论", "结语", "参考文献", "摘要", "目录",
            "致谢", "附录", "后记", "摘要与关键词",
        }
        if (
            meta["title"]
            and not meta["author"]
            and len(text) <= 20
            and text not in SECTION_WORDS
            and not re.search(r"[：:。，,、；;？?！!]", text)
            and not re.match(r"^[（(]", text)
            and not any(i["level"] == 2 for i in items)
        ):
            meta["author"] = text
            items.append({"level": "byline", "text": text})
            continue

        # 作者单位：紧跟署名的括号行
        if meta["author"] and not meta["affiliation"] and re.match(r"^[（(]", text) and len(text) < 60:
            meta["affiliation"] = text
            items.append({"level": "affiliation", "text": text})
            continue

        # 摘要：带「摘要：」前缀
        if text.startswith("摘要"):
            meta["abstract"] = re.sub(r"^摘要[：:]\s*", "", text).strip()
            items.append({"level": "abstract", "text": meta["abstract"]})
            continue

        # 关键词
        if text.startswith("关键词"):
            raw = re.sub(r"^关键词[：:]\s*", "", text).strip()
            meta["keywords"] = [k.strip() for k in re.split(r"[；;、,，]", raw) if k.strip()]
            items.append({"level": "keywords", "text": "；".join(meta["keywords"])})
            continue

        # 副标题
        if style in ("27", "a4") and len(text) < 80:
            items.append({"level": "subtitle", "text": text})
            continue

        # 目录标题与目录条目：站点有自己的导航，不需要文档目录
        if text.strip() in ("目录", "目 录"):
            continue
        # 目录条目样式（26/29/166/165 等 TOC 层级）带页码后缀，一律丢弃
        if style in ("26", "29", "166", "165", "25", "24a"):
            continue
        # 兜底：形如「标题 + 页码」的短行（如 "摘要1"）也判为目录条目
        if re.fullmatch(r"[^\d]{2,20}\d{1,3}", text.strip()):
            continue

        # 一级标题
        if style in ("3", "a3", "Heading1", "1") or size == 24:
            in_refs = text in ("参考文献", "参考文献：")
            items.append({"level": 2, "text": text})
            continue
        if text in ("参考文献", "参考文献："):
            in_refs = True
            items.append({"level": 2, "text": "参考文献"})
            continue

        # 二级标题
        if style in ("4", "a4", "Heading2", "2") or (size == 21 and SUBHEAD_RE.match(text)):
            items.append({"level": 3, "text": text})
            continue

        # 图题 / 表题 / 小字说明
        if style == "15":
            items.append({"level": "caption", "text": text})
            continue

        # 参考文献条目：先于 note 判定，避免被小字号规则吃掉
        if in_refs:
            items.append({"level": "ref", "text": text})
            continue

        if size == 18 and len(text) < 60:
            items.append({"level": "note", "text": text})
            continue

        items.append({"level": "p", "text": text, "runs": b.get("runs", [])})

    # 封面字段渲染为文档信息表，放在正文最前
    if cover_fields:
        info_rows = [["项目", "内容"]]
        for k, v in cover_fields:
            if k == "项目类型":
                continue
            info_rows.append([k, v])
        items.insert(0, {"level": "info", "rows": info_rows})

    return meta, items


# ---------- Markdown 渲染 ----------

def render_inline(item):
    """段落内联 Markdown：保留真斜体/加粗，通体加粗（论文排版习惯）不强调。"""
    runs = item.get("runs") or []
    if not runs:
        return item["text"]
    parts = []
    for text, italic, bold in runs:
        t = text.strip()
        if not t:
            continue
        if italic:
            parts.append(f"*{t}*")
        else:
            parts.append(t)
    joined = "".join(parts)
    return joined if joined.strip() else item["text"]


def md_table(rows):
    """Markdown 表格：首行表头，列数取各行最大值。"""
    if not rows:
        return ""
    cols = max(len(r) for r in rows)
    norm = [r + [""] * (cols - len(r)) for r in rows]
    out = ["| " + " | ".join(norm[0]) + " |"]
    out.append("| " + " | ".join(["---"] * cols) + " |")
    for r in norm[1:]:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def render(items, args):
    out = []
    for it in items:
        lvl = it["level"]
        if lvl == 2:
            out.append(f"\n## {it['text']}\n")
        elif lvl == 3:
            out.append(f"\n### {it['text']}\n")
        elif lvl == "subtitle":
            out.append(f"*{it['text']}*\n")
        elif lvl == "byline":
            out.append(f"**{it['text']}**\n")
        elif lvl == "affiliation":
            out.append(f"{it['text']}\n")
        elif lvl == "abstract":
            out.append(f"> {it['text']}\n")
        elif lvl == "keywords":
            out.append(f"**关键词**：{it['text']}\n")
        elif lvl == "caption":
            out.append(f"\n**{it['text']}**\n")
        elif lvl == "note":
            out.append(f"> {it['text']}\n")
        elif lvl == "ref":
            out.append(f"- {it['text']}")
        elif lvl == "table":
            out.append(f"\n**表 {it['no']}**\n")
            out.append(md_table(it["rows"]))
            out.append("")
        elif lvl == "info":
            out.append(md_table(it["rows"]))
            out.append("")
        elif lvl == "figure":
            base = args.figure_base.rstrip("/")
            prefix = args.figure_prefix
            for f in it["files"]:
                fname = f.split("/")[-1]
                stem = fname.rsplit(".", 1)[0]
                # image1.png -> 1；fig_02 -> fig_02；原样保留其余
                m = re.fullmatch(r"image(\d+)", stem)
                if m:
                    stem = m.group(1)
                url = f"{base}/{prefix}-fig{stem}.webp"
                out.append(f"![图 {it['no']}]({url})")
            out.append("")
        else:
            out.append(f"{render_inline(it)}\n")
    return "\n".join(out).strip() + "\n"


# ---------- YAML ----------

def yaml_scalar(v):
    s = str(v)
    need = (
        s == ""
        or s[0] in "&*!|>{}[]#?,-'\""
        or ": " in s
        or " #" in s
        or s.strip() != s
        or s.endswith(":")
        or s.startswith(" ")
    )
    if need:
        esc = s.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{esc}"'
    return s


def yaml_list(items):
    return "[" + ", ".join(yaml_scalar(i) for i in items) + "]"


def build_frontmatter(args, meta):
    lines = ["---"]
    lines.append(f"title: {yaml_scalar(args.title)}")
    lines.append(f"summary: {yaml_scalar(args.summary)}")
    lines.append(f"category: {yaml_scalar(args.category)}")
    lines.append(f"course: {yaml_scalar(args.course)}")
    lines.append(f"date: {args.date}")
    lines.append(f"tags: {yaml_list(args.tags)}")
    if args.cover:
        lines.append(f"cover: {yaml_scalar(args.cover)}")
    lines.append("---")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("out")
    ap.add_argument("--title", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--category", required=True)
    ap.add_argument("--course", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--tags", default="")
    ap.add_argument("--cover", default="")
    ap.add_argument("--figure-prefix", default="fig")
    ap.add_argument("--figure-base", default="https://hualala25.github.io/images")
    args = ap.parse_args()

    if args.tags:
        args.tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    else:
        args.tags = []

    blocks, figures = read_document(args.docx)
    meta, items = classify(blocks)
    body = render(items, args)
    fm = build_frontmatter(args, meta)

    Path(args.out).write_text(f"{fm}\n\n{body}", encoding="utf-8")

    print(f"✓ {args.out}")
    print(f"  文档标题: {meta['title'] or '(未识别)'}")
    print(f"  署名: {meta['author'] or '-'} {meta['student_id']} {meta['major']} {meta['date_text']}")
    print(f"  图表: {sum(1 for i in items if i['level']=='figure')} 组图 / {sum(1 for i in items if i['level']=='table')} 张表")
    print(f"  段落块: {len(items)}  正文长度: {len(body)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
