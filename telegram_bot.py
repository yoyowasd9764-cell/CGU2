"""
telegram_bot.py - ERP 人話查詢 Telegram Bot
主管透過 Telegram 用自然語言查詢 ERP 資料
"""
import os
import asyncio
import logging
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.constants import ChatAction
from claude_service import ask_erp

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# 選填：限制允許的 Telegram user_id，空白表示不限制
ALLOWED_USERS_RAW = os.environ.get("ALLOWED_TELEGRAM_USERS", "")
ALLOWED_USERS = set(
    int(uid.strip()) for uid in ALLOWED_USERS_RAW.split(",") if uid.strip().isdigit()
)

WELCOME_MSG = """👋 您好！我是 **ERP 智慧查詢助理**

您可以直接用中文問我任何 ERP 問題，例如：

📦 *下周有多少廠商的貨要進來？*
🏦 *銀行帳戶目前有多少錢？*
📊 *本年度的銷售收入是多少？*
💰 *目前有哪些未收的應收帳款？*
🚚 *本月的進貨總金額是多少？*
📋 *有哪些採購訂單還有未到貨數量？*

直接輸入問題即可，不需要任何指令！"""

HELP_MSG = """📖 **使用說明**

直接輸入問題，例如：
• 下周有多少廠商的貨要進來？
• 銀行帳戶目前有多少錢？
• 本年度銷售收入是多少？
• 哪些客戶還有未收帳款？
• 本月進貨總金額？

⚡ 查詢需要 5–15 秒，請耐心等候。

📌 指令：
/start — 開始使用
/help  — 顯示此說明"""


def check_allowed(user_id: int) -> bool:
    if not ALLOWED_USERS:
        return True
    return user_id in ALLOWED_USERS


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_allowed(update.effective_user.id):
        await update.message.reply_text("⛔ 您沒有使用此系統的權限。")
        return
    await update.message.reply_text(WELCOME_MSG, parse_mode="Markdown")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_allowed(update.effective_user.id):
        await update.message.reply_text("⛔ 您沒有使用此系統的權限。")
        return
    await update.message.reply_text(HELP_MSG, parse_mode="Markdown")


async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_allowed(user.id):
        await update.message.reply_text("⛔ 您沒有使用此系統的權限。")
        return

    question = update.message.text.strip()
    if not question:
        return

    logger.info(f"[{user.id}] {user.full_name}: {question}")

    # 顯示「正在輸入中...」
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    # 送出等待提示
    wait_msg = await update.message.reply_text("🔍 正在查詢資料庫，請稍候...")

    try:
        answer = await ask_erp(question)
    except Exception as e:
        logger.error(f"ask_erp error: {e}")
        answer = f"❌ 查詢失敗：{e}"

    # 刪除等待提示，送出答案
    await wait_msg.delete()
    await update.message.reply_text(answer, parse_mode="Markdown")


async def post_init(app):
    await app.bot.set_my_commands([
        BotCommand("start", "開始使用"),
        BotCommand("help",  "使用說明"),
    ])
    info = await app.bot.get_me()
    logger.info(f"Bot 已啟動：@{info.username}")


def main():
    if not BOT_TOKEN:
        raise ValueError("請設定環境變數 TELEGRAM_BOT_TOKEN")

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))

    logger.info("Polling 模式啟動中...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
