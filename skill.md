# erp-query

ERP 人話查詢系統完整操作與維護說明。
支援介面：Streamlit 網頁 + Telegram Bot
模型：claude-haiku-4-5 + SQL Server (casper linked server)

---

## 本機啟動

### Streamlit 網頁介面
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

---

## Telegram Bot 建立步驟

1. 在 Telegram 搜尋 **@BotFather**
2. 傳送 `/newbot`
3. 輸入 Bot 名稱與帳號（帳號須以 `_bot` 結尾）
4. 取得 Token，格式：`1234567890:AAHxxx...`
5. 設定環境變數 `TELEGRAM_BOT_TOKEN` 後執行 `python telegram_bot.py`

**限制授權使用者（選填）：**
```bash
set ALLOWED_TELEGRAM_USERS=123456789,987654321
```
取得 user_id：在 Telegram 搜尋 @userinfobot，傳任何訊息即可得知。

---

## Zeabur 部署

1. 登入 [zeabur.com](https://zeabur.com)
2. **New Project → Add Service → Git → CGU2**
3. **Variables** 新增：
   - `ANTHROPIC_API_KEY` = `sk-ant-api03-...`
   - `TELEGRAM_BOT_TOKEN` = `8984039998:AAF5w24C19Ld...`
4. 等待建置（約 5 分鐘，含安裝 ODBC Driver 17）
5. **Networking → Generate Domain** 取得 Streamlit 網址

---

## 主管使用方式

### Telegram
搜尋 `@CompanyERP_bot`，直接傳中文問題：

| 問題範例 | 查詢工具 |
|---------|---------|
| 下周有多少廠商的貨要進來？ | query_purchase_orders |
| 銀行帳戶目前有多少錢？ | query_account_balance |
| 本年度的銷售收入是多少？ | query_gl |
| 哪些客戶還有未收帳款？ | query_ar |
| 本月進貨總金額是多少？ | query_purchase_receipts |

指令：`/start` 開始、`/help` 說明

### Streamlit 網頁
開啟網址後，點左側欄快速按鈕，或直接在底部輸入框打問題。

---

## Claude Agentic Loop（claude_service.py）

```
ask_erp(question)
  ├─ messages = [{role:user, content:question}]
  ├─ loop（最多 10 輪）:
  │   ├─ Claude API（haiku-4-5 + tools + messages）
  │   ├─ end_turn   → 回傳文字答案
  │   └─ tool_use   → dispatch_tool() → tool_result → 繼續
  └─ 回傳最終自然語言答案
```

---

## 新增查詢工具（tools.py）

### Step 1 — Pydantic 輸入參數
```python
class NewToolInput(BaseModel):
    date_from: str | None = None   # yyyymmdd
    keyword:   str | None = None
```

### Step 2 — SQL 執行函式
```python
def run_new_tool(params: NewToolInput) -> str:
    conn = get_conn()
    cur  = conn.cursor()
    sql  = "SELECT TOP 50 col1, col2 FROM casper.dbo.table WHERE 1=1"
    args = []
    if params.date_from:
        sql += " AND date_col >= ?"
        args.append(params.date_from)
    cur.execute(sql, args)
    rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]
    conn.close()
    return json.dumps({"data": rows, "count": len(rows)}, ensure_ascii=False, default=str)
```

### Step 3 — Tool Schema
```python
{
    "name": "new_tool",
    "description": "查詢 XXX 資料，可依日期或關鍵字篩選",
    "input_schema": {
        "type": "object",
        "properties": {
            "date_from": {"type": "string", "description": "起始日期 yyyymmdd"},
            "keyword":   {"type": "string", "description": "關鍵字"}
        }
    }
}
```

### Step 4 — 加入 dispatcher
```python
elif name == "new_tool":
    return run_new_tool(NewToolInput(**inputs))
```

---

## 已知 ERP 資料表

| 資料表 | 說明 | 關鍵欄位 |
|--------|------|---------|
| `casper.dbo.pod` | 採購訂單 | pono, podate, podatew（預計到貨）, factno, factnm |
| `casper.dbo.pud` | 進貨明細 | puno, pudate, factno, factnm, itemno, itemnm, puamt |
| `casper.dbo.acci` | 科目餘額 | accino（11開頭=現金銀行）, accinm, amt |
| `casper.dbo.RZH` | 應收帳款 | rzno, rzdate, custno, custnm, db_amt, raamounta |
| `casper.dbo.slis` | 分類帳 | slipno, accino（4=收入,5=成本,6=費用）, cr_amt, db_amt |

---

## 資料庫規則

| 規則 | 說明 |
|------|------|
| 日期格式 | yyyymmdd 字串（非 DATE 型態）|
| 金額型態 | Decimal → 需轉 float 才能 JSON 序列化 |
| 查詢上限 | TOP 50，超過回傳 `truncated: true` |
| 參數化查詢 | 一律用 `?` 佔位符，禁止字串拼接 |
| 跨資料庫 | ERP 資料在 `casper.dbo.*`（linked server）|
| View 名稱 | 避免直接用中文 View 名稱（Big5 編碼問題）|

---

## 推送到 GitHub

```bash
git add .
git commit -m "說明變更內容"
git push
```

---

## 常見問題排查

| 問題 | 原因 | 解法 |
|------|------|------|
| `ODBC Driver not found` | 未安裝驅動 | 安裝 ODBC Driver 17 for SQL Server |
| `AuthenticationError` | API Key 未設定 | 設定 `ANTHROPIC_API_KEY` |
| Bot 無回應 | Token 錯誤或未啟動 | 確認 `TELEGRAM_BOT_TOKEN` 並重啟 |
| Bot 回「沒有權限」 | user_id 不在白名單 | 清空 `ALLOWED_TELEGRAM_USERS` 或加入該 id |
| Port 衝突 | 已有其他服務佔用 | 改用 `--server.port 8503` |
| 回答不準確 | 問題太模糊 | 加上時間範圍或具體條件 |
