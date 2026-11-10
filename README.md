# 睡眠科學 LLM Wiki × 教學 HTML 簡報

TAICA 生成式 AI 作業：先建立一個 LLM Wiki，再用它當知識庫，生成一份給沒有生物背景的大學生看的教學 HTML 簡報。

- 教學簡報：https://1571isayu.github.io/LLM-Wiki-Sleep/slides/
- LLM Wiki（可瀏覽版）：https://1571isayu.github.io/LLM-Wiki-Sleep/wiki-site/

## 結構

```
llm-wiki/
├── SCHEMA.md          規範：寫作規則、來源分級、lint 檢查清單
├── raw/               8 篇來源的書目資訊與重點（自己改寫，不複製原文）
├── wiki/
│   ├── index.md       目錄與建議閱讀順序
│   ├── log.md         每次 ingest / lint / 檢查 / 修正的紀錄
│   ├── glossary.md    名詞表
│   ├── concepts/      5 個概念頁
│   ├── myths/         3 個迷思頁
│   └── sources/       8 個來源摘要頁
├── slides/            簡報大綱（query 產出）與簡報原始檔
├── lint.py            Wiki 檢查：斷連結、孤兒頁、C 級來源誤用、數字對不上來源
├── check_slides.py    簡報檢查：每張的數字都能在引用的來源找到、來源清單一致
└── build_site.py      把 Wiki 轉成可瀏覽的網頁
slides/index.html      教學簡報（GitHub Pages）
wiki-site/index.html   Wiki 網頁版（GitHub Pages）
```

## 流程

討論範圍 → SCHEMA → ① 取得資料 → ② 擷取 raw（當下對照原文）→ ③ 整合 Wiki → ④ Wiki lint（程式＋語意）→ ⑤ Query 大綱 → ⑥ 生成簡報 → ⑦ 簡報檢查（程式＋語意）→ 發布

- ①②③ 對每篇來源各跑一次（共 8 篇）
- ④ 不通過回到 ②③；⑦ 不通過回到 ⑥

完整執行與檢查紀錄見 `llm-wiki/wiki/log.md`。

## 重跑檢查

```bash
cd llm-wiki
python3 lint.py          # 需要 Python 3
pip install beautifulsoup4 markdown
python3 check_slides.py
python3 build_site.py
```
