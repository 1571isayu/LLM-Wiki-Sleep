"""Post-generation check: does every slide say only what the wiki's raw sources support?

  C1 a cited source ID does not exist in raw/
  C2 a number on a slide cannot be found in the raw file(s) of the sources cited in that block
     (blocks without their own citation fall back to the slide's data-src)
  C3 a C-grade source is cited on a slide that is not a myth slide
  C4 the slide's data-src does not match the citations actually shown
  C5 a phrase the wiki marked as forbidden appears (e.g. a single-number half-life)
Blocks inside [data-nocheck] are illustrative (charts, formula-based estimates) and skipped.
"""
import re, sys
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
raw = {p.name[:3]: p.read_text(encoding="utf-8") for p in (ROOT / "raw").glob("S0*.md")}
grade = {k: re.search(r"^grade:\s*([ABC])", v, re.M).group(1) for k, v in raw.items()}
soup = BeautifulSoup((ROOT / "slides/sleep-slides.html").read_text(encoding="utf-8"), "html.parser")
FORBID = [(r"半衰期[^。]{0,6}(約|是|為)\s*\d+\s*小時", "single-number half-life"),
          (r"週期\s*(=|就是|剛好是)\s*90", "cycle stated as exactly 90"),
          (r"平均\s*5\s*小時", "unsourced 'average 5 hours'")]
NUM = re.compile(r"(?<![A-Za-z0-9.,])(\d+(?:,\d{3})*(?:\.\d+)?)(?![A-Za-z0-9])")
issues = []
for idx, s in enumerate(soup.select("section.slide"), 1):
    for nc in s.select("[data-nocheck]"):
        nc.decompose()
    slide_src = s.get("data-src", "").split()
    shown = set()
    for blk in s.select("li, p, h2, h3, .big, .verdict"):
        if blk.find(["li", "p"]):
            continue
        cites = [c.get_text(strip=True) for c in blk.select(".cite")]
        shown.update(cites)
        for c in blk.select(".cite, .tag"):
            c.extract()
        text = blk.get_text(" ", strip=True)
        if blk.get("class") and "big" in blk["class"]:
            sib = blk.find_next_sibling()
            cites = cites or [c for c in re.findall(r"S0\d", str(sib))]
        for c in cites:
            if c not in raw:
                issues.append((idx, "C1", f"cites missing {c}"))
        pool = cites or slide_src
        rawtext = " ".join(raw.get(c, "") for c in pool)
        for n in NUM.findall(text):
            if not pool:
                issues.append((idx, "C2", f"number {n} with no source: {text[:40]}"))
            elif n not in rawtext:
                issues.append((idx, "C2", f"number {n} not in {'/'.join(pool)}: {text[:40]}"))
        for pat, why in FORBID:
            if re.search(pat, text):
                issues.append((idx, "C5", f"{why}: {text[:40]}"))
    for c in shown:
        if grade.get(c) == "C" and not s.get("data-wiki", "").startswith("myths/"):
            issues.append((idx, "C3", f"C-grade {c} on non-myth slide"))
    if set(slide_src) != shown and slide_src:
        issues.append((idx, "C4", f"data-src {sorted(slide_src)} vs shown {sorted(shown)}"))
for i in issues:
    print(f"slide {i[0]:>2}  {i[1]}  {i[2]}")
print(f"\n{len(issues)} issue(s)")
sys.exit(1 if issues else 0)
