# CONTRIBUTING.md — 貢獻指南

感謝你有興趣貢獻 sexline！以下是參與開發的規範。

---

## 🧭 開發流程

1. **Fork Repository** →  Clone → 開 Branch
2. **讀完 AGENTS.md** → 了解 AI 開發者規範
3. **讀完 PROJECT_CONTEXT.md** → 了解技術細節
4. **實作** → **測試** → **Commit**
5. **開 Pull Request** → 等待 review

---

## 📐 程式碼規範

### 後端（Python）

- Python 3.11+
- 使用 `.venv/` 虛擬環境
- import 順序：標準函式庫 → 第三方 → 本地
- 型別提示（type hints）為必要
- 函式與類別加上 docstring

### 前端（HTML/CSS/JS）

- 純靜態，零框架
- LINE 風格一致
- 手機/電腦皆需支援
- CSS class 命名採用 BEM 風格

---

## 📝 Commit Message 規範

```
<type>: <簡短說明>

<選擇性詳細說明>
```

**type 列表：**
- `feat` — 新功能
- `fix` — 修正 bug
- `refactor` — 重構（不改變功能）
- `docs` — 文件
- `style` — 樣式、格式
- `chore` — 雜項（CI、設定）
- `perf` — 效能
- `test` — 測試

**範例：**
```
feat: 新增貼圖發送功能

實作貼圖選擇器、貼圖 API 端點、資料庫欄位。
```

---

## 🔄 PR 流程

1. PR title 格式同 Commit Message
2. 描述中註明 Closes/Fixes 哪個 Issue
3. 確保 CI（GitHub Actions）通過
4. 至少 1 人 review 後合併

---

## 🧪 測試

目前無自動化測試框架。  
貢獻時請手動驗證：

- [ ] 後端 `GET /health` 回傳 200
- [ ] 前端正確渲染聊天畫面
- [ ] 發送訊息正常扣鑽石
- [ ] 角色切換正常
- [ ] 手機瀏覽器排版正確

---

## ❓ 有問題？

開 Issue 或直接聯絡 lil yo。
