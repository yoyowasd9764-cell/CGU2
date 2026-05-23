"""
tools.py - 定義 5 個 ERP 查詢 Tool
每個 Tool 包含：
  - Pydantic 輸入 model
  - 執行 SQL 的函式 (回傳 list[dict])
  - Anthropic tool schema (name, description, input_schema)
"""
import json
from typing import Optional
from pydantic import BaseModel, Field
from db import execute_query

MAX_ROWS = 50  # 超過此筆數只傳前 MAX_ROWS 筆並說明截斷


def _truncate_result(rows: list[dict]) -> dict:
    """若結果超過 MAX_ROWS，截斷並附加說明"""
    total = len(rows)
    if total > MAX_ROWS:
        return {
            "data": rows[:MAX_ROWS],
            "truncated": True,
            "total_count": total,
            "note": f"查詢結果共 {total} 筆，僅顯示前 {MAX_ROWS} 筆",
        }
    return {"data": rows, "truncated": False, "total_count": total}


# ─────────────────────────────────────────────
# Tool 1: query_purchase_orders (採購訂單)
# ─────────────────────────────────────────────

class QueryPurchaseOrdersInput(BaseModel):
    delivery_date_from: Optional[str] = Field(None, description="預計到貨日期起 (yyyymmdd)")
    delivery_date_to: Optional[str] = Field(None, description="預計到貨日期迄 (yyyymmdd)")
    vendor_name: Optional[str] = Field(None, description="廠商名稱關鍵字")
    pending_only: bool = Field(True, description="是否只查尚未到齊的訂單")


def query_purchase_orders(params: dict) -> list[dict]:
    inp = QueryPurchaseOrdersInput(**params)
    conditions = []
    args = []

    if inp.delivery_date_from:
        conditions.append("podatew >= ?")
        args.append(inp.delivery_date_from)
    if inp.delivery_date_to:
        conditions.append("podatew <= ?")
        args.append(inp.delivery_date_to)
    if inp.vendor_name:
        conditions.append("factnm LIKE ?")
        args.append(f"%{inp.vendor_name}%")
    if inp.pending_only:
        conditions.append(
            "(ISNULL(poqty,0)-ISNULL(poqty_pu,0)-ISNULL(poqty_pox,0)) > 0"
        )

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"""
        SELECT pono, podate, podatew, itemno, itemnm,
               ISNULL(poqty,0) AS qty,
               ISNULL(poqty_pu,0) AS recv_qty,
               ISNULL(poqty,0)-ISNULL(poqty_pu,0)-ISNULL(poqty_pox,0) AS pending_qty,
               factnm
        FROM casper.dbo.pod
        {where}
        ORDER BY podatew
    """
    rows = execute_query(sql, tuple(args))
    result = _truncate_result(rows)
    return result


TOOL_PURCHASE_ORDERS = {
    "name": "query_purchase_orders",
    "description": (
        "查詢採購訂單，可篩選預計到貨日期範圍，回答「下周有多少廠商的貨要進來」等問題。"
        "podatew 是預計到貨日期，格式 yyyymmdd。"
        "pending_only=True 時只回傳尚未到齊的訂單。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "delivery_date_from": {
                "type": "string",
                "description": "預計到貨日期起，格式 yyyymmdd，例如 '20260526'",
            },
            "delivery_date_to": {
                "type": "string",
                "description": "預計到貨日期迄，格式 yyyymmdd，例如 '20260601'",
            },
            "vendor_name": {
                "type": "string",
                "description": "廠商名稱關鍵字（模糊比對）",
            },
            "pending_only": {
                "type": "boolean",
                "description": "是否只查尚未到齊的訂單，預設 true",
            },
        },
        "required": [],
    },
}


# ─────────────────────────────────────────────
# Tool 2: query_purchase_receipts (進貨明細)
# ─────────────────────────────────────────────

class QueryPurchaseReceiptsInput(BaseModel):
    date_from: Optional[str] = Field(None, description="進貨日期起 (yyyymmdd)")
    date_to: Optional[str] = Field(None, description="進貨日期迄 (yyyymmdd)")
    vendor_name: Optional[str] = Field(None, description="廠商名稱關鍵字")
    item_name: Optional[str] = Field(None, description="品項名稱關鍵字")


def query_purchase_receipts(params: dict) -> dict:
    inp = QueryPurchaseReceiptsInput(**params)
    conditions = []
    args = []

    if inp.date_from:
        conditions.append("pudate >= ?")
        args.append(inp.date_from)
    if inp.date_to:
        conditions.append("pudate <= ?")
        args.append(inp.date_to)
    if inp.vendor_name:
        conditions.append("factnm LIKE ?")
        args.append(f"%{inp.vendor_name}%")
    if inp.item_name:
        conditions.append("itemnm LIKE ?")
        args.append(f"%{inp.item_name}%")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"""
        SELECT puno, pudate, factno, factnm, itemno, itemnm,
               ISNULL(puqtyr,0) AS qty,
               ISNULL(puprir,0) AS price,
               ISNULL(puamt,0) AS amt
        FROM casper.dbo.pud
        {where}
        ORDER BY pudate DESC
    """
    rows = execute_query(sql, tuple(args))
    return _truncate_result(rows)


TOOL_PURCHASE_RECEIPTS = {
    "name": "query_purchase_receipts",
    "description": (
        "查詢實際進貨明細記錄，可依日期範圍、廠商名稱、品項名稱篩選。"
        "pudate 是進貨日期，格式 yyyymmdd。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "date_from": {
                "type": "string",
                "description": "進貨日期起，格式 yyyymmdd",
            },
            "date_to": {
                "type": "string",
                "description": "進貨日期迄，格式 yyyymmdd",
            },
            "vendor_name": {
                "type": "string",
                "description": "廠商名稱關鍵字（模糊比對）",
            },
            "item_name": {
                "type": "string",
                "description": "品項名稱關鍵字（模糊比對）",
            },
        },
        "required": [],
    },
}


# ─────────────────────────────────────────────
# Tool 3: query_account_balance (科目餘額)
# ─────────────────────────────────────────────

class QueryAccountBalanceInput(BaseModel):
    account_code_prefix: Optional[str] = Field(
        None, description="科目代碼前綴，例如 '11' 查現金銀行類"
    )
    account_name_like: Optional[str] = Field(None, description="科目名稱關鍵字")


def query_account_balance(params: dict) -> dict:
    inp = QueryAccountBalanceInput(**params)
    conditions = []
    args = []

    if inp.account_code_prefix:
        conditions.append("accino LIKE ?")
        args.append(f"{inp.account_code_prefix}%")
    if inp.account_name_like:
        conditions.append("accinm LIKE ?")
        args.append(f"%{inp.account_name_like}%")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"""
        SELECT accino, accinm, ISNULL(amt,0) AS amt
        FROM casper.dbo.acci
        {where}
        ORDER BY accino
    """
    rows = execute_query(sql, tuple(args))

    # 加總
    total = sum(r["amt"] for r in rows)
    result = _truncate_result(rows)
    result["summary_total"] = total
    return result


TOOL_ACCOUNT_BALANCE = {
    "name": "query_account_balance",
    "description": (
        "查詢會計科目餘額，可查銀行存款、現金、應收帳款等各科目餘額。"
        "銀行帳戶的 accino 開頭為 '11'（流動資產現金類）。"
        "回傳各科目明細及合計金額。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "account_code_prefix": {
                "type": "string",
                "description": "科目代碼前綴，例如 '11' 查現金銀行類，'12' 查應收帳款類",
            },
            "account_name_like": {
                "type": "string",
                "description": "科目名稱關鍵字（模糊比對）",
            },
        },
        "required": [],
    },
}


# ─────────────────────────────────────────────
# Tool 4: query_ar (應收帳款)
# ─────────────────────────────────────────────

class QueryARInput(BaseModel):
    customer_name: Optional[str] = Field(None, description="客戶名稱關鍵字")
    date_from: Optional[str] = Field(None, description="帳款日期起 (yyyymmdd)")
    date_to: Optional[str] = Field(None, description="帳款日期迄 (yyyymmdd)")
    overdue_only: bool = Field(False, description="是否只查逾期帳款")


def query_ar(params: dict) -> dict:
    inp = QueryARInput(**params)
    conditions = ["ISNULL(code_z,'N')<>'V'"]
    args = []

    if inp.customer_name:
        conditions.append("custnm LIKE ?")
        args.append(f"%{inp.customer_name}%")
    if inp.date_from:
        conditions.append("rzdate >= ?")
        args.append(inp.date_from)
    if inp.date_to:
        conditions.append("rzdate <= ?")
        args.append(inp.date_to)
    if inp.overdue_only:
        # 到期日早於今日且尚未收齊
        from datetime import date
        today = date.today().strftime("%Y%m%d")
        conditions.append("date1 < ?")
        args.append(today)
        conditions.append("ISNULL(db_amt,0) > ISNULL(raamounta,0)")

    where = "WHERE " + " AND ".join(conditions)
    sql = f"""
        SELECT rzno, rzdate, sdno, yyyymm, custno, custnm,
               ISNULL(db_amt,0) AS ar_amt,
               date1 AS due_date,
               ISNULL(raamounta,0) AS collected
        FROM casper.dbo.RZH
        {where}
        ORDER BY rzdate DESC
    """
    rows = execute_query(sql, tuple(args))

    total_ar = sum(r["ar_amt"] for r in rows)
    total_collected = sum(r["collected"] for r in rows)
    result = _truncate_result(rows)
    result["summary_total_ar"] = total_ar
    result["summary_total_collected"] = total_collected
    result["summary_outstanding"] = total_ar - total_collected
    return result


TOOL_AR = {
    "name": "query_ar",
    "description": (
        "查詢應收帳款，可依客戶名稱、帳款日期範圍篩選，也可只查逾期帳款。"
        "回傳應收金額、已收金額、未收餘額的彙總。"
        "rzdate 是帳款日期，date1 是到期日，格式均為 yyyymmdd。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "customer_name": {
                "type": "string",
                "description": "客戶名稱關鍵字（模糊比對）",
            },
            "date_from": {
                "type": "string",
                "description": "帳款日期起，格式 yyyymmdd",
            },
            "date_to": {
                "type": "string",
                "description": "帳款日期迄，格式 yyyymmdd",
            },
            "overdue_only": {
                "type": "boolean",
                "description": "是否只查逾期（到期日已過且未收齊）的帳款，預設 false",
            },
        },
        "required": [],
    },
}


# ─────────────────────────────────────────────
# Tool 5: query_gl (分類帳)
# ─────────────────────────────────────────────

class QueryGLInput(BaseModel):
    year_month: Optional[str] = Field(None, description="年月 (yyyymm)，查特定月份")
    year: Optional[str] = Field(None, description="年度 (yyyy)，查整年")
    account_type: Optional[str] = Field(
        None, description="科目類型：4=收入, 5=成本, 6=費用"
    )
    account_code_prefix: Optional[str] = Field(None, description="科目代碼前綴")


def query_gl(params: dict) -> dict:
    inp = QueryGLInput(**params)
    conditions = [
        "SUBSTRING(accino,1,1) IN ('4','5','6','7','8','9')",
        "ISNULL(stz,'')='Y'",
        "ISNULL(swt3,'')<>'Y'",
    ]
    args = []

    if inp.year_month:
        conditions.append("SUBSTRING(slipno,1,6) = ?")
        args.append(inp.year_month)
    elif inp.year:
        conditions.append("SUBSTRING(slipno,1,4) = ?")
        args.append(inp.year)

    if inp.account_type:
        conditions.append("SUBSTRING(accino,1,1) = ?")
        args.append(inp.account_type)

    if inp.account_code_prefix:
        conditions.append("accino LIKE ?")
        args.append(f"{inp.account_code_prefix}%")

    where = "WHERE " + " AND ".join(conditions)
    sql = f"""
        SELECT
            SUBSTRING(slipno,1,6) AS yyyymm,
            accino,
            accinm,
            SUBSTRING(accino,1,1) AS acc_type,
            SUM(ISNULL(cr_amt,0)-ISNULL(db_amt,0)) AS balance
        FROM casper.dbo.slis
        {where}
        GROUP BY SUBSTRING(slipno,1,6), accino, accinm, SUBSTRING(accino,1,1)
        ORDER BY SUBSTRING(slipno,1,6), accino
    """
    rows = execute_query(sql, tuple(args))

    # 依科目類型彙總
    type_map = {"4": "收入", "5": "成本", "6": "費用", "7": "營業外收入", "8": "營業外費用", "9": "稅"}
    summary_by_type: dict = {}
    for r in rows:
        t = r.get("acc_type", "")
        label = type_map.get(t, t)
        summary_by_type[label] = summary_by_type.get(label, 0) + r["balance"]

    result = _truncate_result(rows)
    result["summary_by_type"] = summary_by_type
    return result


TOOL_GL = {
    "name": "query_gl",
    "description": (
        "查詢分類帳，可查收入/成本/費用，回答「本年度銷售金額是多少」等問題。"
        "slipno 前6碼是 yyyymm，acc_type: 4=收入, 5=成本, 6=費用。"
        "回傳各科目餘額及依類型的彙總。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "year_month": {
                "type": "string",
                "description": "查特定月份，格式 yyyymm，例如 '202601'",
            },
            "year": {
                "type": "string",
                "description": "查整年，格式 yyyy，例如 '2026'",
            },
            "account_type": {
                "type": "string",
                "description": "科目類型：4=收入, 5=成本, 6=費用",
                "enum": ["4", "5", "6", "7", "8", "9"],
            },
            "account_code_prefix": {
                "type": "string",
                "description": "科目代碼前綴（更精細篩選）",
            },
        },
        "required": [],
    },
}


# ─────────────────────────────────────────────
# 工具登錄表 & dispatcher
# ─────────────────────────────────────────────

ALL_TOOLS = [
    TOOL_PURCHASE_ORDERS,
    TOOL_PURCHASE_RECEIPTS,
    TOOL_ACCOUNT_BALANCE,
    TOOL_AR,
    TOOL_GL,
]

TOOL_FUNCTIONS = {
    "query_purchase_orders": query_purchase_orders,
    "query_purchase_receipts": query_purchase_receipts,
    "query_account_balance": query_account_balance,
    "query_ar": query_ar,
    "query_gl": query_gl,
}


def dispatch_tool(tool_name: str, tool_input: dict) -> str:
    """呼叫對應的 tool function，回傳 JSON 字串供 Claude 使用"""
    if tool_name not in TOOL_FUNCTIONS:
        return json.dumps({"error": f"未知的 tool: {tool_name}"}, ensure_ascii=False)
    try:
        result = TOOL_FUNCTIONS[tool_name](tool_input)
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
