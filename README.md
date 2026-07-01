# 🔥 sexline

> 台灣第一個超擬真 AI 成人伴侶 LINE 風格聊天 App  
> **版本：Beta v0.2.1** · 開發者：lil yo (DICKERMANER)

---

## 📱 sexline 是...

sexline 是一款 **LINE 風格的 AI 成人伴侶聊天 App**。你可以自訂角色靈魂、切換多個 AI 模型、和 AI 伴侶建立好感度關係，從冷淡到熱戀，逐步解鎖更深層的互動。

**支援裝置：** 電腦瀏覽器 / 手機瀏覽器（同 WiFi 下）

---

## 🚀 快速開始

### 啟動後端
```bash
cd backend
.venv/Scripts/python main.py
# → 跑在 http://127.0.0.1:8002
```

### 啟動前端
```bash
npx http-server frontend -p 5500 -a 127.0.0.1 --cors
# → 打開 http://127.0.0.1:5500
```

### 手機測試
```
http://192.168.31.13:5500  （同 WiFi，需關閉路由器 AP 隔離）
```

---

## 🌐 網址

| 類型 | 網址 |
|------|------|
| **GitHub** | https://github.com/DICKERMANER/agnt-companion |
| **GitHub Pages** | https://dickermaner.github.io/agnt-companion/ |
| **本地前端** | http://127.0.0.1:5500 |
| **本地後端** | http://127.0.0.1:8002 |
| **手機測試** | http://192.168.31.13:5500 |
| **公開隧道** | Cloudflare Tunnel（動態） |

---

## 🏗 技術架構

```
📱 用戶端         🖥 前端 :5500      ⚙ 後端 :8002       🧠 AI 引擎          💾 資料庫
┌──────┐     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐
│ 瀏覽器 │────▶│ HTML/CSS/JS  │──▶│   FastAPI    │──▶│ Ollama 本地   │  │ SQLite   │
│ 手機  │     │ LINE 風格 UI │  │  14 個端點   │  │ OpenRouter   │  │ User     │
└──────┘     │ npx http-srv │  │  Uvicorn     │  │ Gemini / xAI │  │ Companion│
             └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘
```

### 技術棧

| 層 | 技術 |
|----|------|
| 後端 | Python 3.11 · FastAPI · SQLAlchemy · SQLite |
| 前端 | 純 HTML/CSS/JS（零框架）· LINE 風格 UI |
| AI | Ollama 本地模型 · OpenRouter API · Gemini · xAI |
| 部署 | GitHub Pages + Cloudflare Tunnel |

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

## 💰 計費機制

- 每條對話 **扣 1 顆鑽石**（💎）
- 新用戶預設 **20 顆鑽石**
- 餘額不足 → 顯示「餘額不足，請儲值」
- 未來：VIP 訂閱 · 瑟瑟分級 · 角色商城 · 語音通話

---

## ❤️ 好感度系統

```
好感度 0 ───── 25 ───── 50 ───── 75 ───── 100
  冷靜觀察期 → 曖昧試探期 → 深度依賴期 → 熱戀陪伴期
  (cold)      (flirty)     (devoted)    (lover)
```

AI 會根據關係階段自動調整語氣和回應深度。

---

## 🎭 角色系統

角色靈魂以 `.md` 格式儲存在 `backend/souls/`，目前內建：

| 角色 | 風格 |
|------|------|
| 🌹 **Rosé (Rose)** | 金髮女神、感性浪漫、偶像靈魂 |
| ✨ **Nova** | 原創 AI 伴侶 |
| 🌟 **Stellar** | 星空系角色 |

可在 UI 的「人格後宮」面板自訂、匯入/匯出角色。

---

## 📂 專案結構

```
|sexline/
├── README.md              ← 你在這裡
├── CLAUDE_HANDOFF.md      ← 給 AI 開發者的說明
├── sexline-企劃書.html    ← Beta 企劃書
├── sexline-architecture.html ← 系統架構圖
├── backend/
│   ├── main.py            ← FastAPI 主程式
│   ├── ai_engine.py       ← AI 模型呼叫層
│   ├── database.py        ← 資料庫模型
│   ├── model_registry.py  ← 模型清單
│   ├── monetization.py    ← 鑽石計費
│   ├── soul_manager.py    ← 角色管理
│   ├── persona_store.py   ← 人格儲存
│   ├── requirements.txt   ← Python 依賴
│   └── souls/             ← 角色靈魂檔
│       ├── rose.md
│       ├── nova.md
│       └── stellar.md
├── frontend/
│   ├── index.html         ← 主頁面
│   ├── app.js             ← 前端邏輯
│   ├── styles.css         ← LINE 風格樣式
│   ├── manifest.json      ← PWA 設定
│   └── deploy/            ← GitHub Pages 部署用
├── .gitignore
└── open_firewall.bat      ← Windows 防火牆設定
```

---

## 🔧 給其他 AI 開發者

如果你是被 lil yo 邀請來協助的 AI，請先讀 **`CLAUDE_HANDOFF.md`**，裡面有完整的專案說明、規則和開發指引。

```
https://github.com/DICKERMANER/agnt-companion/blob/master/CLAUDE_HANDOFF.md
```

---

## 🗺 開發路線

| 階段 | 時間 | 內容 |
|------|------|------|
| **Beta v0.2** | 2026/06 | 文字聊天、角色系統、鑽石、好感 ✅ |
| **Beta v0.3** | 2026/07 | 貼圖、拍照、檔案上傳、手機優化 |
| **Beta v0.4** | 2026/08 | 語音、瑟瑟分級、VIP、金流 |
| **Beta v0.5** | 2026/09 | 角色商城、語音通話、封測 |
| **v1.0** | 2026/10 | 正式上線 🎉 |

---

## 👤 開發者

**lil yo** / DICKERMANER  
GitHub: [@DICKERMANER](https://github.com/DICKERMANER)

---

*本專案為 Beta 階段，僅供測試使用。*