# erp-query

ERP 人話查詢系統的完整建置、維護與操作說明。
技術棧：Streamlit + Claude API (claude-haiku-4-5) + SQL Server

---

## 本機啟動

```bash
pip install -r requirements.txt
set ANTHROPIC_API_KEY=sk-ant-api03-...
python -m streamlit run main.py --server.port 8502
```

開啟 http://localhost:8502

---

## Zeabur 部署

1. 登入 [zeabur.com](https://zeabur.com)
2. **New Project → Add Service → Git → CGU2**
3. **Variables** 新增：
   - `ANTHROPIC_API_KEY` = `sk-ant-api03-...`
4. 等待建置（約 5 分鐘，含安裝 ODBC Driver 17）
5. **Networking → Generate Domain** 取得公開網址

---

## 前端介面說明（main.py）

使用 Streamlit `st.chat_message` 實作對話介面：

- **左側欄** — 8 個常用快速查詢按鈕 + 清除對話
- **主區** — 仿 ChatGPT 對話，支援 Markdown 渲染
- **歡迎卡片** — 首次進入時顯示 4 個範例問題
- **對話記錄** — 存於 `st.session_state.messages`，重新整理後清除

---

## Claude Agentic Loop（claude_service.py）

```
ask_erp(question)
  ├─ 建立 messages = [{role:user, content:question}]
  ├─ loop（最多 10 輪）:
  │   ├─ 呼叫 Claude API（model + tools + messages）
  │   ├─ stop_reason == end_turn  → 回傳文字答案
  │   └─ stop_reason == tool_use  → dispatch_tool() → 加入 tool_result → 繼續
  └─ 回傳最終自然語言答案
```

模型：`claude-haiku-4-5`，max_tokens：4096

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
| `AuthenticationError` | API Key 未設定 | 設定 `ANTHROPIC_API_KEY` 環境變數 |
| `Port already in use` | Port 衝突 | 改用其他 port，例如 `--server.port 8503` |
| 回答不準確 | 問題太模糊 | 加上時間範圍或具體條件 |
| Streamlit 空白 | session_state 問題 | 按 F5 重新整理或清除對話 |
