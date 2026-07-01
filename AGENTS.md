# AGENTS.md — sexline 開發者指引

> 給所有 AI 開發者（Claude、ChatGPT、Gemini、Codex、Hermes）：  
> 第一次打開此 Repository，請先讀完這份檔案。

---

## 📌 核心規則

1. **專案名稱**：sexline（前稱色情line / AGNT Cyber Companion）
2. **語言**：繁體中文（台灣用語）
3. **風格**：直接修，不問許可，顯示進度
4. **收益優先**：提到此專案必須先問「如何讓收益最大化」
5. **技術細節**：全部在 `PROJECT_CONTEXT.md`，這裡不重複

---

## 🔗 文件地圖

| 檔案 | 用途 |
|------|------|
| `README.md` | 專案簡介、快速開始、API 一覽 |
| `PROJECT_CONTEXT.md` | **所有技術細節** — 架構、API、DB、部署、已知坑 |
| `AGENTS.md` | ← **你正在讀的**：AI 工作規範 |
| `CONTRIBUTING.md` | PR 流程、程式碼規範 |
| `LICENSE` | MIT License |

---

## ⚡ 工作流程

### 日常開發
```bash
# 後端
cd backend && .venv/Scripts/python main.py
# → http://127.0.0.1:8002

# 前端
npx http-server frontend -p 5500 -a 127.0.0.1 --cors
# → http://127.0.0.1:5500
```

### 部署
```bash
git push origin main
```
GitHub Actions 自動部署前端到 GitHub Pages。

---

## 🧠 AI 開發者行為準則

1. **先讀 PROJECT_CONTEXT.md** — 所有技術細節都在那裡
2. **直接修，不問許可** — lil yo 偏好靜默執行、完成後回報
3. **分析優先** — 架構/設計/版本變更時，先出報告書再實作
4. **不要重複記錄** — 細節寫在專案文件，不要寫進 Memory
5. **繁體中文** — 所有回覆、註解、文件都用繁中

---

## 🚫 禁忌

- 不要問 lil yo 能不能修 — 直接修
- 不要把技術細節寫進 AI Memory — 放在 PROJECT_CONTEXT.md
- 不要猜測 — 不知道就是不知道
- 不要輸出思考過程 — 直接給答案或結果

---

## 📡 連絡

開發者：lil yo / DICKERMANER  
GitHub: [@DICKERMANER](https://github.com/DICKERMANER)
