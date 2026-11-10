"""Render the whole LLM Wiki (SCHEMA, wiki/, raw/, check scripts) into one browsable HTML page."""
import html
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "site" / "sleep-wiki.html"
SLIDES_URL = "https://claude.ai/artifact/AugBi5TzayaHHEnjiqZRXx"


def page_id(path: Path) -> str:
    rel = path.relative_to(ROOT).with_suffix("")
    parts = list(rel.parts)
    if parts[0] == "wiki":
        parts = parts[1:]
    if parts[0] == "raw":
        return "raw-" + parts[1][:3]
    if parts[0] == "sources":
        return "src-" + parts[1]
    return "-".join(p.lower() for p in parts).replace("_", "-")


pages = []  # (group, id, title, html)
stem_to_id = {}

files = [ROOT / "SCHEMA.md"] + sorted((ROOT / "wiki").rglob("*.md")) + sorted((ROOT / "raw").glob("*.md"))
for f in files:
    stem_to_id[f.stem] = page_id(f)


def render_md(text: str) -> str:
    meta = ""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if m:
        rows = []
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                v = v.strip().strip('"')
                v = html.escape(v)
                if v.startswith("http"):
                    v = f'<a href="{v}" target="_blank" rel="noopener">{v}</a>'
                rows.append(f"<tr><th>{html.escape(k.strip())}</th><td>{v}</td></tr>")
        meta = '<div class="tablewrap"><table class="meta">' + "".join(rows) + "</table></div>"
        text = text[m.end():]

    def link(mo):
        name = mo.group(1)
        pid = stem_to_id.get(name)
        if not pid:
            return f'<span class="broken">{html.escape(name)}</span>'
        return f'<a class="wl" href="#{pid}">{html.escape(name)}</a>'

    text = re.sub(r"\[\[([^\]]+)\]\]", link, text)
    body = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    body = re.sub(r"\[(S0\d)\]", lambda mo: f'<a class="cite" href="#src-{mo.group(1)}">{mo.group(1)}</a>', body)
    body = body.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")
    return meta + body


def title_of(text: str, fallback: str) -> str:
    m = re.search(r"^title:\s*\"?(.+?)\"?$", text, re.M)
    if m:
        return m.group(1)
    m = re.search(r"^# (.+)$", text, re.M)
    return m.group(1) if m else fallback


groups = {"overview": "總覽", "concepts": "概念", "myths": "迷思", "sources": "來源摘要", "raw": "原始資料 raw/", "tools": "檢查程式"}
for f in files:
    text = f.read_text(encoding="utf-8")
    rel = f.relative_to(ROOT)
    if rel.parts[0] == "raw":
        g = "raw"
    elif len(rel.parts) > 2:
        g = rel.parts[1]
    else:
        g = "overview"
    pid = page_id(f)
    t = title_of(text, f.stem)
    if g == "raw":
        t = f"{f.name[:3]} · {t}"
    pages.append((g, pid, t, str(rel), render_md(text)))

for script in ["lint.py", "check_slides.py"]:
    code = (ROOT / script).read_text(encoding="utf-8")
    pages.append(("tools", script.replace(".py", "").replace("_", "-"), script, script,
                  f"<h1>{script}</h1><pre><code>{html.escape(code)}</code></pre>"))

order_overview = ["index", "schema", "log", "glossary"]
pages.sort(key=lambda p: (list(groups).index(p[0]), order_overview.index(p[1]) if p[1] in order_overview else 99, p[1]))

nav = []
for g, label in groups.items():
    items = [p for p in pages if p[0] == g]
    if not items:
        continue
    nav.append(f'<div class="ng"><div class="nl">{label}</div>')
    for _, pid, t, rel, _ in items:
        short = re.sub(r"^#\s*", "", t)
        nav.append(f'<a href="#{pid}" data-id="{pid}">{html.escape(short)}</a>')
    nav.append("</div>")

articles = "\n".join(
    f'<article id="{pid}" data-path="{html.escape(rel)}"{"" if i == 0 else " hidden"}><div class="path">{html.escape(rel)}</div>{body}</article>'
    for i, (_, pid, t, rel, body) in enumerate(pages)
)

TEMPLATE = (ROOT / "site" / "template.html").read_text(encoding="utf-8")
OUT.write_text(TEMPLATE.replace("{{NAV}}", "\n".join(nav)).replace("{{ARTICLES}}", articles)
               .replace("{{SLIDES_URL}}", SLIDES_URL).replace("{{COUNT}}", str(len(pages))), encoding="utf-8")
print(f"wrote {OUT} with {len(pages)} pages")
