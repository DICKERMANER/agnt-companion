# 色情line (AGNT Cyber Companion SaaS)

台灣第一個超擬真 AI 成人伴侶 LINE 風格聊天 App。

## 給 AI 開發者

你是被 lil yo 邀請來協助開發的 AI。這個專案在 Beta 階段，以下是必要資訊：

### 網址
- **GitHub**: https://github.com/DICKERMANER/agnt-companion
- **本地前端**: http://127.0.0.1:5500
- **本地後端**: http://127.0.0.1:8002
- **GitHub Pages**: https://dickermaner.github.io/agnt-companion/

### 技術棧
- **後端**: FastAPI + SQLite + SQLAlchemy (Python 3.11, .venv)
- **前端**: 純 HTML/CSS/JS，LINE 風格聊天 UI
- **AI**: Ollama 本地模型 + OpenRouter API + Gemini + xAI
- **部署**: GitHub Pages (前端) + Cloudflare Tunnel (後端穿透)

### 專案結構
```
backend/
  main.py          — FastAPI 主程式，14 個端點
  ai_engine.py     — AI 模型呼叫層 (Ollama/OpenRouter/Cloud)
  database.py      — SQLAlchemy 模型 (User + Companion)
  model_registry.py — 模型清單讀取 Hermes config
  monetization.py  — 鑽石計費 (1 條 = 1 鑽)
  soul_manager.py  — 角色 Soul 管理
  persona_store.py — 人格設定儲存
  souls/*.md       — 角色靈魂檔 (Rose, Nova, Stellar...)
frontend/
  index.html       — LINE 風格聊天 UI
  app.js           — 前端邏輯 (fetch API, 模型切換, 貼圖...)
  styles.css       — 完整 LINE 風格樣式
  deploy/          — GitHub Pages 部署用
```

### 後端 API 端點
| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | /health | 健康檢查 |
| GET | /state/{user_id} | 用戶狀態 |
| POST | /state/{user_id}/diamonds | 設定鑽石 |
| GET | /models | AI 模型清單 |
| GET/POST/DELETE | /souls | 角色 CRUD |
| GET/POST | /model | 當前模型/切換 |
| GET/POST | /persona | 人格設定 |
| POST | /webhook/chat | 主聊天端點 |

### 啟動方式
```bash
# 後端
cd backend && .venv/Scripts/python main.py

# 前端
npx http-server frontend -p 5500 -a 127.0.0.1 --cors
```

### 已知 Bug (已修復)
- app.js port 提示 8000→8002 ✅
- runtime_options 沒傳入 API ✅
- Qwen reasoning content 為空 fallback ✅
- main.py port 8001→8002 ✅

### lil yo 的規則
- 專案名稱：色情line
- 提到此專案必須先問「如何讓收益最大化」
- 風格：直接修，不問許可，顯示進度
- 語言：繁體中文
