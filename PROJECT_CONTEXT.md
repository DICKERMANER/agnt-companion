# PROJECT_CONTEXT.md — sexline 技術大腦

> 所有技術細節的唯一真實來源（Single Source of Truth）。  
> 其他文件引用這裡，這裡不引用其他地方。

---

## 🏗 系統架構

```
📱 用戶端         🖥 前端 :5500      ⚙ 後端 :8002       🧠 AI 引擎          💾 資料庫
┌──────┐     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐
│ 瀏覽器 │────▶│ HTML/CSS/JS  │──▶│   FastAPI    │──▶│ Ollama 本地   │  │ SQLite   │
│ 手機  │     │ LINE 風格 UI │  │  14 個端點   │  │ OpenRouter   │  │ sexline   │
└──────┘     │ npx http-srv │  │  Uvicorn     │  │ Gemini / xAI │  │ .db      │
             └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘
```

### 技術棧

| 層 | 技術 |
|----|------|
| 後端 | Python 3.11 · FastAPI · SQLAlchemy · SQLite |
| 前端 | 純 HTML/CSS/JS（零框架）· LINE 風格 UI |
| AI | Ollama 本地模型 · OpenRouter API · Gemini · xAI · DeepSeek |
| 部署 | GitHub Pages（前端）+ Cloudflare Tunnel（後端穿透） |

---

## 📡 API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| `GET` | `/health` | 健康檢查 |
| `GET` | `/state/{user_id}` | 查用戶狀態（鑽石、好感、關係） |
| `POST` | `/state/{user_id}/diamonds` | 設定鑽石 |
| `GET` | `/models` | AI 模型清單 |
| `GET` | `/souls` | 所有角色清單 |
| `GET` | `/souls/{soul_id}` | 角色詳情 + Soul.md |
| `POST` | `/souls` | 建立/更新角色 |
| `POST` | `/souls/import` | 匯入 Soul.md |
| `DELETE` | `/souls/{soul_id}` | 刪除角色 |
| `GET` | `/model` | 當前模型 |
| `POST` | `/model` | 切換模型 |
| `POST` | `/persona` | 儲存人格 |
| `GET` | `/persona` | 讀取人格 |
| `POST` | `/webhook/chat` | **主聊天**（扣 1 💎） |

---

## 💾 資料庫結構

### User 表

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | Integer PK | 自動遞增 |
| user_id | String Unique | 用戶識別碼 |
| diamonds | Integer | 鑽石餘額（預設 20） |
| relationship_score | Integer | 好感度 0–100 |
| relationship_stage | String | cold/flirty/devoted/lover |
| current_soul_id | String | 當前角色 ID |
| created_at | DateTime | 建立時間 |

### Companion 表

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | Integer PK | 自動遞增 |
| user_id | String FK | 關聯 User |
| soul_id | String | 角色 ID |
| name | String | 角色名稱 |
| affinity | Integer | 好感度（0–100） |
| is_active | Boolean | 是否啟用 |
| last_interaction | DateTime | 最後互動時間 |

---

## 💰 計費機制

- 每條對話 **扣 1 顆鑽石**
- 新用戶預設 **20 顆鑽石**
- 餘額不足 → 回傳 `INSUFFICIENT_BALANCE_MESSAGE`
- 實作在 `backend/monetization.py`

---

## ❤️ 好感度系統

```
好感度 0 ───── 25 ───── 50 ───── 75 ───── 100
  冷靜觀察期 → 曖昧試探期 → 深度依賴期 → 熱戀陪伴期
  (cold)      (flirty)     (devoted)    (lover)
```

- AI 根據關係階段自動調整語氣和回應深度
- 實作在 `backend/ai_engine.py`（`map_relationship_stage`, `build_dynamic_system_prompt`）

---

## 🎭 角色系統

- 角色靈魂以 `.md` 格式儲存在 `backend/souls/`
- 可在 UI「人格後宮」面板自訂、匯入/匯出
- 實作在 `backend/soul_manager.py`

### 內建角色

| 角色 | 風格 |
|------|------|
| 🌹 Rosé (Rose) | 金髮女神、感性浪漫、偶像靈魂 |
| ✨ Nova | 原創 AI 伴侶 |
| 🌟 Stellar | 星空系角色 |

---

## 📂 專案結構

```
sexline/
├── README.md               ← 專案簡介
├── AGENTS.md               ← AI 開發者指引（你該先讀這個）
├── PROJECT_CONTEXT.md      ← 所有技術細節（就是這裡）
├── CONTRIBUTING.md         ← 貢獻指南
├── LICENSE                 ← MIT License
├── CLAUDE_HANDOFF.md       ← 舊版（已轉移到 AGENTS.md）
├── .gitignore
├── .github/workflows/
│   └── deploy.yml          ← GitHub Actions 自動部署
├── backend/
│   ├── main.py             ← FastAPI 主程式（14 個端點）
│   ├── ai_engine.py        ← AI 模型呼叫層
│   ├── database.py         ← SQLAlchemy 模型
│   ├── model_registry.py   ← 模型清單
│   ├── monetization.py     ← 鑽石計費
│   ├── soul_manager.py     ← 角色管理
│   ├── persona_store.py    ← 人格儲存
│   ├── requirements.txt    ← Python 依賴
│   └── souls/              ← 角色靈魂檔
│       ├── rose.md
│       ├── nova.md
│       └── stellar.md
├── frontend/
│   ├── index.html          ← 開發用主頁面
│   ├── app.js              ← 前端邏輯
│   ├── styles.css          ← LINE 風格樣式
│   ├── manifest.json       ← PWA 設定
│   ├── deploy/             ← GitHub Pages 部署用（獨立副本）
│   │   ├── index.html
│   │   ├── app.js
│   │   ├── styles.css
│   │   ├── manifest.json
│   │   ├── robots.txt
│   │   └── sitemap.xml
│   ├── assets/
│   │   ├── icons/
│   │   └── avatars/
│   └── feature_tests.js
```

---

## 🚀 部署

### 前端（GitHub Pages）

`git push origin main` → GitHub Actions 自動將 `frontend/deploy/` 部署到 GitHub Pages。  
部署流程定義在 `.github/workflows/deploy.yml`。

### 後端（Cloudflare Tunnel）

本地開發模式：啟動後端 → Cloudflare Tunnel 建立公開網址 → 前端 API_BASE 自動切換。

### API_BASE 自動偵測邏輯

```
本地開發 → http://127.0.0.1:8002
區網同 WiFi → http://192.168.31.13:8002
GitHub Pages → CYBER_COMPANION_BACKEND 環境變數
```

---

## ⚠️ 已知問題與坑

1. **Tunnel 斷線**：Cloudflare Tunnel 約 27 小時斷線一次，需重啟並更新前端
2. **前端部署副本**：`frontend/deploy/` 是獨立的副本，修改 `frontend/` 後需同步到 `frontend/deploy/`
3. **Qwen reasoning**：Qwen 模型 reasoning_content 可能為空，需 fallback
4. **port 爭議**：後端統一使用 8002，前端使用 5500
5. **Windows 防火牆**：需執行 `open_firewall.bat` 允許 8002/5500 端口

---

## 🔧 開發環境

- **OS**：Windows 10（Git Bash 環境）
- **後端**：Python 3.11, `.venv/` 虛擬環境
- **前端**：純靜態，`npx http-server` 啟動
- **Git**：`master` = `main` 同指 `origin`

---

## 🗺 開發路線

| 階段 | 時間 | 內容 |
|------|------|------|
| Beta v0.2 | 2026/06 | 文字聊天、角色系統、鑽石、好感 ✅ |
| Beta v0.3 | 2026/07 | 貼圖、拍照、檔案上傳、手機優化 |
| Beta v0.4 | 2026/08 | 語音、瑟瑟分級、VIP、金流 |
| Beta v0.5 | 2026/09 | 角色商城、語音通話、封測 |
| v1.0 | 2026/10 | 正式上線 🎉 |
