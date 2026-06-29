# cyber_companion_saas

沉浸式 AI 戀愛陪伴養成平台（PWA + Web + Desktop 包裝可延伸）。

## 功能摘要
- FastAPI 後端大腦中樞（Webhook 路由）
- SQLite + SQLAlchemy（User / Companion）
- 每句扣 1 鑽石，餘額不足即攔截
- 情緒評判 Hook：正/負向對話影響好感度
- 動態 Prompt 注入：依好感度切換關係階段
- 前端賽博毛玻璃 UI（鑽石餘額、好感度進度條、快捷鍵注入）
- iOS PWA（Safari 加入主畫面 -> standalone）

## 專案結構
- `backend/`：API、資料庫、AI 引擎、變現鎖
- `frontend/`：PWA 頁面與互動
- `shared/`：前後端共用 schema

## 本地啟動
```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

另開一個終端：
```bash
cd frontend
python -m http.server 5500
```

瀏覽：
- 前端：`http://127.0.0.1:5500`
- API 健康檢查：`http://127.0.0.1:8000/health`
