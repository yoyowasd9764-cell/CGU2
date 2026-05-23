"""
claude_service.py - Claude API agentic loop
實作多輪 tool_use，直到 Claude 回傳 end_turn 為止
"""
import asyncio
from datetime import date
import anthropic
from tools import ALL_TOOLS, dispatch_tool

import os
CLAUDE_MODEL = "claude-opus-4-7"
CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = f"""你是一個 ERP 查詢助理，幫主管查詢公司的財務和採購資料。
今天的日期是 {date.today().strftime('%Y/%m/%d')}。

回答規則：
1. 使用繁體中文回答
2. 數字要加千分位（例如 1,234,567）
3. 金額要加「元」（例如 1,234,567 元）
4. 日期要格式化為 yyyy/mm/dd（例如 2026/05/23）
5. 回答要簡潔清楚，重點優先
6. 若有多筆資料，用條列方式整理
7. 若查詢結果被截斷（truncated=true），要在答案中說明「以下為前50筆資料」

你可以使用以下工具查詢資料庫：
- query_purchase_orders：查詢採購訂單（預計到貨）
- query_purchase_receipts：查詢實際進貨明細
- query_account_balance：查詢科目餘額（銀行存款等）
- query_ar：查詢應收帳款
- query_gl：查詢分類帳（收入/成本/費用）

日期計算說明：
- 「下周」= 下個星期一到下個星期日
- 「本周」= 本星期一到本星期日
- 「本月」= 當月1日到當月最後一天
- 日期格式統一用 yyyymmdd 傳入工具
"""


async def ask_erp(question: str) -> str:
    """
    主要入口：接收自然語言問題，回傳自然語言答案
    實作 agentic loop，支援多輪 tool_use
    """
    client = anthropic.AsyncAnthropic(api_key=CLAUDE_API_KEY)

    messages = [{"role": "user", "content": question}]

    # agentic loop
    for _ in range(10):  # 最多 10 輪防止無限迴圈
        response = await client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=ALL_TOOLS,
            messages=messages,
        )

        # 將 assistant 回應加入 messages
        messages.append({"role": "assistant", "content": response.content})

        # 若 stop_reason 是 end_turn，表示 Claude 已完成回答
        if response.stop_reason == "end_turn":
            # 取出最後的文字回應
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return "（無文字回應）"

        # 若 stop_reason 是 tool_use，執行工具並把結果傳回
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_result_content = dispatch_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_result_content,
                    })

            if tool_results:
                messages.append({"role": "user", "content": tool_results})
            continue

        # 其他 stop_reason（例如 max_tokens）
        break

    # 若迴圈結束仍無 end_turn，嘗試取最後一段文字
    if messages and messages[-1]["role"] == "assistant":
        content = messages[-1]["content"]
        if isinstance(content, list):
            for block in content:
                if hasattr(block, "text"):
                    return block.text
    return "查詢逾時或發生未知錯誤，請稍後再試。"


if __name__ == "__main__":
    import sys
    question = sys.argv[1] if len(sys.argv) > 1 else "銀行帳戶目前有多少錢？"
    answer = asyncio.run(ask_erp(question))
    print("\n=== 答案 ===")
    print(answer)
