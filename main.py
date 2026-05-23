"""
main.py - ERP 人話查詢系統 (Streamlit 版)
"""
import asyncio
import streamlit as st
from claude_service import ask_erp

st.set_page_config(
    page_title="ERP 智慧查詢",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 自訂樣式 ──────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #161b22; }
[data-testid="stSidebarContent"] { padding-top: 1rem; }
.stChatMessage { border-radius: 12px; }
div[data-testid="stChatMessageContent"] p { line-height: 1.8; }
.stButton > button {
    width: 100%; text-align: left; border-radius: 8px;
    background: transparent; border: 1px solid #30363d;
    color: #e6edf3; font-size: 0.84rem; padding: 8px 12px;
    transition: all 0.15s;
}
.stButton > button:hover { background: #21262d; border-color: #2f81f7; color: #fff; }
</style>
""", unsafe_allow_html=True)

# ── 側欄 ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏭 ERP 智慧查詢")
    st.caption("Natural Language ERP Query")
    st.divider()

    st.markdown("**常用查詢**")

    QUICK = [
        ("📦", "下周有多少廠商的貨要進來？"),
        ("🏦", "銀行帳戶目前有多少錢？"),
        ("📊", "本年度的銷售收入是多少？"),
        ("💰", "目前有哪些未收的應收帳款？"),
        ("🚚", "本月的進貨總金額是多少？"),
        ("📋", "有哪些採購訂單還有未到貨數量？"),
        ("💳", "現金及銀行存款的科目餘額？"),
        ("📉", "本年度的費用支出是多少？"),
    ]

    for icon, q in QUICK:
        if st.button(f"{icon} {q}", key=q):
            st.session_state.pending_question = q

    st.divider()
    if st.button("🗑️ 清除對話記錄"):
        st.session_state.messages = []
        st.session_state.pop("pending_question", None)
        st.rerun()

    st.markdown("---")
    st.caption("Model: claude-haiku-4-5\nPowered by Anthropic + SQL Server")

# ── 初始化 session ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── 主標題 ────────────────────────────────────────────────
st.title("🤖 ERP 人話查詢助理")
st.caption("用自然語言詢問財務、採購、應收帳款等任何 ERP 資料")

# ── 歡迎卡片（無對話時顯示）──────────────────────────────
if not st.session_state.messages:
    st.markdown("#### 您可以這樣問：")
    c1, c2 = st.columns(2)
    examples = [
        ("📦 下周到貨", "下周有多少廠商的貨要進來？"),
        ("🏦 銀行餘額", "銀行帳戶目前有多少錢？"),
        ("📊 年度銷售", "本年度的銷售收入是多少？"),
        ("💰 應收帳款", "目前有哪些未收的應收帳款？"),
    ]
    for i, (label, q) in enumerate(examples):
        col = c1 if i % 2 == 0 else c2
        with col:
            if st.button(label, key=f"ex_{i}", use_container_width=True):
                st.session_state.pending_question = q
    st.divider()

# ── 顯示對話歷史 ───────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])

# ── 處理快速按鈕觸發 ──────────────────────────────────────
if "pending_question" in st.session_state:
    prompt = st.session_state.pop("pending_question")
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("AI 正在查詢資料庫..."):
            try:
                answer = asyncio.run(ask_erp(prompt))
            except Exception as e:
                answer = f"❌ 查詢失敗：{e}"
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})

# ── 輸入框 ────────────────────────────────────────────────
if prompt := st.chat_input("請輸入問題，例如：下周有多少廠商的貨要進來？"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("AI 正在查詢資料庫..."):
            try:
                answer = asyncio.run(ask_erp(prompt))
            except Exception as e:
                answer = f"❌ 查詢失敗：{e}"
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
