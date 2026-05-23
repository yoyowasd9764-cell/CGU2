# erp-query

ERP 人話查詢系統的完整建置、維護與操作說明。

---

## 專案初始化

```bash
git clone https://github.com/tocasper-eng/cgu2.git 人話查詢
cd 人話查詢
pip install -r requirements.txt
```

---

## 環境設定

### Windows 本機

```bash
set ANTHROPIC_API_KEY=sk-ant-api03-...
uvicorn main:app --host 0.0.0.0 --port 8001
```

### Linux / Docker

```bash
export ANTHROPIC_API_KEY=sk-ant-api03-...
uvicorn main:app --host 0.0.0.0 --port 8080
```

---

## Zeabur 部署

1. 登入 [zeabur.com](https://zeabur.com)
2. **New Project → Add Service → Git → CGU2**
3. **Variables** 新增：
   - `ANTHROPIC_API_KEY` = `sk-ant-api03-...`
4. 等待建置（約 5 分鐘，含安裝 ODBC Driver 17）
5. **Networking → Generate Domain** 取得網址

---

## 新增查詢工具

當需要擴充新的 ERP 查詢功能時，在 `tools.py` 新增：

### Step 1 — 定義 Pydantic 輸入參數

```python
class NewToolInput(BaseModel):
    date_from: str | None = None   # yyyymmdd
    keyword:   str | None = None
```

### Step 2 — 撰寫 SQL 函式

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

### Step 3 — 加入 Tool Schema

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

在 `dispatch_tool()` 函式中新增：
```python
elif name == "new_tool":
    return run_new_tool(NewToolInput(**inputs))
```

---

## 資料庫規則

| 規則 | 說明 |
|------|------|
| 日期格式 | yyyymmdd 字串（非 DATE 型態）|
| 金額型態 | Decimal，需轉 float 才能 JSON 序列化 |
| 查詢上限 | TOP 50，超過時回傳 `truncated: true` |
| 參數化查詢 | 一律用 `?` 佔位符，禁止字串拼接 |
| 跨資料庫 | ERP 資料在 `casper.dbo.*`（linked server）|

---

## 已知 ERP 資料表

| 資料表 | 說明 | 關鍵欄位 |
|--------|------|---------|
| `casper.dbo.pod` | 採購訂單 | pono, podate, podatew（預計到貨）, factno, factnm |
| `casper.dbo.pud` | 進貨明細 | puno, pudate, factno, factnm, itemno, itemnm, puamt |
| `casper.dbo.acci` | 科目餘額 | accino（11=現金銀行）, accinm, amt |
| `casper.dbo.RZH` | 應收帳款 | rzno, rzdate, custno, custnm, db_amt, raamounta |
| `casper.dbo.slis` | 分類帳 | slipno, accino（4=收入,5=成本,6=費用）, cr_amt, db_amt |

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
| `Port already in use` | Port 衝突 | 改用其他 port，例如 `--port 8002` |
| 查詢結果亂碼 | DB 為 Big5 | 已用英文欄位別名，勿直接查 view 名稱 |
| 回答不準確 | 問題太模糊 | 在問題中加上時間範圍或具體條件 |
