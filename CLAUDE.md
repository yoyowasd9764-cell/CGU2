# ERP 人話查詢系統 (CGU2)

## 專案概述

讓主管用自然語言查詢公司 ERP 資料，支援 **Streamlit 網頁** 與 **Telegram Bot** 兩種介面。

## 系統流程

```
主管問問題
  ├─ Streamlit 網頁 (main.py)
  └─ Telegram Bot (telegram_bot.py)
        ↓
  claude_service.py
        ↓
  Claude API claude-haiku-4-5（tool_use）
        ↓
  tools.py（5 個查詢工具）
        ↓
  SQL Server（casper linked server）
        ↓
  結果回 Claude → 自然語言總結 → 回傳給主管
```

## 檔案結構

| 檔案 | 說明 |
|------|------|
| `main.py` | Streamlit 網頁介面，含側欄快速按鈕 + 對話介面 |
| `telegram_bot.py` | Telegram Bot，Polling 模式，主管直接傳訊查詢 |
| `claude_service.py` | Claude agentic loop，支援多輪 tool_use |
| `tools.py` | 5 個 ERP 查詢工具（Pydantic + SQL） |
| `db.py` | pyodbc 連線 helper |
| `Dockerfile` | Zeabur / Docker 部署用，含 ODBC Driver 17 |
| `requirements.txt` | 所有套件清單 |
| `skill.md` | 完整操作與維護說明 |

## 資料庫設定

| 項目 | 值 |
|------|-----|
| Server | 43.153.159.36,30147 |
| Database | gemio |
| ERP 資料 | casper linked server（casper.dbo.xxx） |
| User | sa |

## 五個查詢工具

| Tool | 資料表 | 可回答的問題 |
|------|--------|------------|
| `query_purchase_orders` | casper.dbo.pod | 下周有多少廠商的貨要進來？ |
| `query_purchase_receipts` | casper.dbo.pud | 本月進貨總金額是多少？ |
| `query_account_balance` | casper.dbo.acci | 銀行帳戶有多少錢？ |
| `query_ar` | casper.dbo.RZH | 哪些客戶還有未收帳款？ |
| `query_gl` | casper.dbo.slis | 本年度銷售收入是多少？ |

## 環境變數

| 變數 | 說明 | 必填 |
|------|------|------|
| `ANTHROPIC_API_KEY` | Claude API 金鑰 | ✅ |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | Telegram 功能必填 |
| `ALLOWED_TELEGRAM_USERS` | 允許的 user_id，逗號分隔（空白=不限制） | 選填 |

## 本機啟動

### Streamlit 網頁
```bash
pip install -r requirements.txt
set ANTHROPIC_API_KEY=sk-ant-api03-...
python -m streamlit run main.py --server.port 8502
```
開啟 http://localhost:8502

### Telegram Bot
```bash
set ANTHROPIC_API_KEY=sk-ant-api03-...
set TELEGRAM_BOT_TOKEN=8984039998:AAF5w24C19Ld...
python telegram_bot.py
```

## Telegram Bot 說明

- Bot 帳號：`@CompanyERP_bot`
- 指令：`/start`、`/help`
- 主管直接傳中文問題，Bot 自動查詢 ERP 並回答
- 支援 `ALLOWED_TELEGRAM_USERS` 限制授權主管名單

## Zeabur 部署

1. Zeabur → New Project → Add Service → Git → 選 CGU2
2. Variables 新增：
   - `ANTHROPIC_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
3. 等待建置（約 5 分鐘）
4. Networking → Generate Domain（Streamlit 用）

## GitHub

https://github.com/yoyowasd9764-cell/CGU2

## 規則

- 所有 SQL 使用參數化查詢（`?` 佔位符），禁止字串拼接
- 日期欄位格式為 `yyyymmdd` 字串
- 查詢超過 50 筆自動截斷並通知 Claude
- Decimal 金額自動轉 float
- 模型：claude-haiku-4-5
- 前端：Streamlit（網頁）+ Telegram Bot（手機）
