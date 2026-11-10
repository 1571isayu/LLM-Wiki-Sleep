"""Programmatic lint for the sleep-science LLM Wiki.

Checks (from SCHEMA.md):
  L1 broken [[links]]
  L2 orphan pages (not linked from index or any other page)
  L3 citations [Sxx] that point to a missing source
  L4 C-grade sources cited outside a myth page's "常見說法" section
  L5 numbers on concept/myth pages that cannot be found in the cited raw file(s)
  L6 concept/myth pages missing a 生活例子 section
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WIKI = ROOT / "wiki"
RAW = ROOT / "raw"

pages = {p.stem: p for p in WIKI.rglob("*.md")}
raw_by_id = {p.name[:3]: p for p in RAW.glob("S0*.md")}
grade = {}
for sid, p in raw_by_id.items():
    m = re.search(r"^grade:\s*([ABC])", p.read_text(encoding="utf-8"), re.M)
    grade[sid] = m.group(1) if m else "?"

issues = []
linked = set()

for name, path in pages.items():
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT)
    # L1
    for link in re.findall(r"\[\[([^\]]+)\]\]", text):
        linked.add(link)
        if link not in pages:
            issues.append(("L1", rel, f"broken link [[{link}]]"))
    # L3
    for sid in set(re.findall(r"\[(S0\d)\]", text)):
        if sid not in raw_by_id:
            issues.append(("L3", rel, f"cites missing source {sid}"))
    is_content = path.parent.name in ("concepts", "myths")
    if not is_content:
        continue
    # L4
    sections = re.split(r"^## ", text, flags=re.M)
    for sec in sections:
        title = sec.splitlines()[0] if sec else ""
        for sid in set(re.findall(r"\[(S0\d)\]", sec)):
            if grade.get(sid) == "C" and "常見說法" not in title:
                issues.append(("L4", rel, f"C-grade {sid} used as evidence in section '{title}'"))
    # L5 — check each line's numbers against that line's cited raw sources
    for line in text.splitlines():
        cites = re.findall(r"\[(S0\d)\]", line)
        if not cites or "推論" in line:
            continue
        nums = re.findall(r"(?<![A-Za-z0-9.])(\d+(?:\.\d+)?)(?![A-Za-z0-9])", line)
        nums = [n for n in nums if not re.fullmatch(r"0\d", n)]
        raw_text = " ".join(raw_by_id[s].read_text(encoding="utf-8") for s in cites if s in raw_by_id)
        for n in nums:
            if n not in raw_text:
                issues.append(("L5", rel, f"number {n} not found in {','.join(cites)}: {line.strip()[:60]}…"))
    # L6
    if path.parent.name == "concepts" and "生活例子" not in text:
        issues.append(("L6", rel, "no 生活例子 section"))

# L2
for name, path in pages.items():
    if name in ("index", "log"):
        continue
    if name not in linked:
        issues.append(("L2", path.relative_to(ROOT), "orphan page"))

for code, rel, msg in sorted(issues, key=lambda x: (x[0], str(x[1]))):
    print(f"{code}  {rel}  {msg}")
print(f"\n{len(issues)} issue(s)")
sys.exit(1 if issues else 0)
