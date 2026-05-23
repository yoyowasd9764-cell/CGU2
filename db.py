"""
db.py - pyodbc connection helper
每次呼叫建立新連線，不使用 connection pool
"""
import pyodbc

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=43.153.159.36,30147;"
    "DATABASE=gemio;"
    "UID=sa;"
    "PWD=7TH5AIxg3N9jBcXsdJqZ4o6V82t10mpv;"
    "TrustServerCertificate=yes;"
)


def get_connection():
    """建立並回傳新的資料庫連線"""
    try:
        conn = pyodbc.connect(CONNECTION_STRING, timeout=30)
        return conn
    except pyodbc.Error as e:
        raise RuntimeError(f"資料庫連線失敗: {e}") from e


def execute_query(sql: str, params: tuple = ()) -> list[dict]:
    """
    執行 SQL 查詢，回傳 list[dict]
    自動處理 Decimal -> float 轉換
    """
    from decimal import Decimal

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        result = []
        for row in rows:
            record = {}
            for col, val in zip(columns, row):
                if isinstance(val, Decimal):
                    val = float(val)
                record[col] = val
            result.append(record)
        return result
    finally:
        conn.close()
