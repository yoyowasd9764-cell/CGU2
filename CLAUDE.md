# ERP 人話查詢系統

## 架構說明

主管用自然語言問問題 → FastAPI → Claude API (tool_use) → Python SQL函式 → SQL Server → 結果回傳 Claude 整理 → 自然語言答覆

## 檔案說明

| 檔案 | 說明 |
|------|------|
| `main.py` | FastAPI 應用，`POST /ask` + `GET /` HTML 介面 |
| `claude_service.py` | Claude agentic loop，多輪 tool_use 直到 end_turn |
| `tools.py` | 5 個 ERP 查詢工具定義（schema + SQL 執行函式） |
| `db.py` | pyodbc 連線 helper，每次建新連線 |
| `requirements.txt` | Python 套件清單 |

## 資料庫

- Server: 43.153.159.36,30147
- Database: gemio（ERP資料在 casper linked server）
- ERP 資料表都用 `casper.dbo.xxx` 存取

## 五個查詢工具

1. **query_purchase_orders** - 採購訂單（casper.dbo.pod）
   - 可查下周到貨、待收訂單等
   
2. **query_purchase_receipts** - 進貨明細（casper.dbo.pud）
   - 實際進貨記錄，可依廠商/品項篩選
   
3. **query_account_balance** - 科目餘額（casper.dbo.acci）
   - 銀行存款(11開頭)、現金等
   
4. **query_ar** - 應收帳款（casper.dbo.RZH）
   - 可查逾期帳款、客戶別餘額
   
5. **query_gl** - 分類帳（casper.dbo.slis）
   - 收入(4)/成本(5)/費用(6)，可查年度銷售

## 啟動方式

```bash
cd C:\Users\lux54\CC0523\人話查詢
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

開啟瀏覽器 http://localhost:8000

## 注意事項

- 所有 SQL 用參數化查詢（pyodbc 的 `?` 佔位符）
- 日期欄位為 yyyymmdd 字串格式
- 查詢結果超過 50 筆自動截斷，並通知 Claude
- Decimal 金額自動轉為 float
- 所有檔案 UTF-8 編碼
