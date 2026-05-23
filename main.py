"""
main.py - FastAPI 應用程式
提供 REST API 和 HTML 問答介面
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from claude_service import ask_erp

app = FastAPI(title="ERP 人話查詢系統", version="2.0.0")


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    answer: str


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="問題不能為空")
    try:
        answer = await ask_erp(request.question)
        return AnswerResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢失敗：{str(e)}")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def home():
    html = r"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ERP 智慧查詢</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
  :root {
    --bg: #0d1117;
    --sidebar: #161b22;
    --border: #30363d;
    --accent: #2f81f7;
    --accent2: #1f6feb;
    --text: #e6edf3;
    --muted: #8b949e;
    --user-bubble: #1f6feb;
    --ai-bubble: #21262d;
    --hover: #21262d;
    --radius: 12px;
    --shadow: 0 8px 32px rgba(0,0,0,.4);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; font-family: 'Microsoft JhengHei','PingFang TC','Segoe UI',sans-serif; background: var(--bg); color: var(--text); }

  /* ── 版面 ── */
  .layout { display: flex; height: 100vh; }

  /* ── 側欄 ── */
  .sidebar {
    width: 260px; min-width: 260px;
    background: var(--sidebar);
    border-right: 1px solid var(--border);
    display: flex; flex-direction: column;
    padding: 20px 14px;
    gap: 8px;
  }
  .sidebar-logo {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 6px 16px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 8px;
  }
  .sidebar-logo .icon { font-size: 1.6rem; }
  .sidebar-logo .title { font-size: 1rem; font-weight: 700; line-height: 1.2; }
  .sidebar-logo .sub { font-size: .72rem; color: var(--muted); }
  .section-label { font-size: .72rem; color: var(--muted); letter-spacing: 1px; padding: 4px 6px; text-transform: uppercase; }
  .quick-btn {
    display: flex; align-items: center; gap: 8px;
    padding: 9px 10px; border-radius: 8px;
    cursor: pointer; font-size: .85rem; color: var(--text);
    transition: background .15s;
    border: none; background: transparent; text-align: left; width: 100%;
  }
  .quick-btn:hover { background: var(--hover); }
  .quick-btn .q-icon { font-size: 1rem; width: 20px; text-align: center; flex-shrink: 0; }
  .sidebar-footer { margin-top: auto; font-size: .72rem; color: var(--muted); padding: 8px 6px; border-top: 1px solid var(--border); }

  /* ── 主區 ── */
  .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

  /* 頂欄 */
  .topbar {
    padding: 14px 24px; border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
    background: var(--sidebar);
  }
  .topbar-title { font-size: 1rem; font-weight: 600; }
  .topbar-badge { font-size: .72rem; background: var(--accent); color: #fff; padding: 2px 8px; border-radius: 20px; }

  /* 對話區 */
  .chat-area { flex: 1; overflow-y: auto; padding: 28px 0; scroll-behavior: smooth; }
  .chat-inner { max-width: 760px; margin: 0 auto; padding: 0 24px; display: flex; flex-direction: column; gap: 24px; }

  /* 歡迎畫面 */
  .welcome {
    text-align: center; padding: 60px 20px;
    display: flex; flex-direction: column; align-items: center; gap: 14px;
  }
  .welcome .w-icon { font-size: 3.5rem; }
  .welcome h2 { font-size: 1.5rem; font-weight: 700; }
  .welcome p { color: var(--muted); font-size: .92rem; }
  .welcome-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 16px; width: 100%; max-width: 520px; }
  .welcome-card {
    background: var(--ai-bubble); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 14px;
    cursor: pointer; text-align: left; transition: border-color .2s, background .2s;
    font-size: .85rem; color: var(--text);
  }
  .welcome-card:hover { border-color: var(--accent); background: #1c2128; }
  .welcome-card .wc-icon { font-size: 1.2rem; margin-bottom: 6px; }
  .welcome-card .wc-text { color: var(--muted); font-size: .78rem; margin-top: 3px; }

  /* 訊息氣泡 */
  .msg { display: flex; gap: 12px; align-items: flex-start; }
  .msg.user { flex-direction: row-reverse; }
  .avatar {
    width: 34px; height: 34px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0;
  }
  .avatar.ai { background: linear-gradient(135deg,#2f81f7,#8b5cf6); }
  .avatar.user { background: linear-gradient(135deg,#f97316,#ec4899); }
  .bubble {
    max-width: 82%; padding: 13px 16px; border-radius: var(--radius);
    line-height: 1.7; font-size: .93rem;
  }
  .msg.user .bubble { background: var(--user-bubble); border-radius: var(--radius) 4px var(--radius) var(--radius); }
  .msg.ai  .bubble { background: var(--ai-bubble); border: 1px solid var(--border); border-radius: 4px var(--radius) var(--radius) var(--radius); }

  /* Markdown 樣式 */
  .bubble h1,.bubble h2,.bubble h3 { margin: 12px 0 6px; }
  .bubble h2 { font-size: 1rem; color: #79c0ff; border-bottom: 1px solid var(--border); padding-bottom: 4px; }
  .bubble h3 { font-size: .92rem; color: #d2a8ff; }
  .bubble p  { margin: 6px 0; }
  .bubble ul,.bubble ol { padding-left: 20px; margin: 6px 0; }
  .bubble li { margin: 3px 0; }
  .bubble strong { color: #ffa657; }
  .bubble code { background: #0d1117; border: 1px solid var(--border); border-radius: 4px; padding: 1px 5px; font-size: .85em; }
  .bubble table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: .85rem; }
  .bubble th { background: #1c2128; padding: 6px 10px; text-align: left; border: 1px solid var(--border); }
  .bubble td { padding: 5px 10px; border: 1px solid var(--border); }

  /* 思考中 */
  .thinking { display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: .87rem; }
  .dots { display: flex; gap: 4px; }
  .dots span { width: 6px; height: 6px; background: var(--accent); border-radius: 50%; animation: blink 1.2s ease-in-out infinite; }
  .dots span:nth-child(2) { animation-delay: .2s; }
  .dots span:nth-child(3) { animation-delay: .4s; }
  @keyframes blink { 0%,80%,100%{opacity:.2} 40%{opacity:1} }

  /* 輸入列 */
  .input-bar {
    padding: 16px 24px 20px;
    border-top: 1px solid var(--border);
    background: var(--sidebar);
  }
  .input-inner {
    max-width: 760px; margin: 0 auto;
    display: flex; gap: 10px; align-items: flex-end;
  }
  .input-wrap { flex: 1; position: relative; }
  textarea#q {
    width: 100%; padding: 12px 16px;
    background: var(--ai-bubble); border: 1px solid var(--border);
    border-radius: var(--radius); color: var(--text);
    font-family: inherit; font-size: .95rem; resize: none;
    min-height: 50px; max-height: 160px; line-height: 1.5;
    outline: none; transition: border-color .2s;
  }
  textarea#q:focus { border-color: var(--accent); }
  textarea#q::placeholder { color: var(--muted); }
  .send-btn {
    width: 46px; height: 46px; border-radius: 10px;
    background: var(--accent); border: none;
    color: #fff; font-size: 1.2rem; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; transition: background .15s, transform .1s;
  }
  .send-btn:hover:not(:disabled) { background: var(--accent2); transform: scale(1.05); }
  .send-btn:disabled { opacity: .45; cursor: not-allowed; transform: none; }
  .input-hint { text-align: center; color: var(--muted); font-size: .72rem; margin-top: 8px; }

  /* 手機響應 */
  @media(max-width: 640px) {
    .sidebar { display: none; }
    .welcome-grid { grid-template-columns: 1fr; }
  }
  @media(max-width: 480px) {
    .chat-inner, .input-inner { padding: 0 14px; }
  }

  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
</head>
<body>
<div class="layout">

  <!-- 側欄 -->
  <div class="sidebar">
    <div class="sidebar-logo">
      <div class="icon">🏭</div>
      <div>
        <div class="title">ERP 智慧查詢</div>
        <div class="sub">Natural Language ERP</div>
      </div>
    </div>

    <div class="section-label">常用查詢</div>
    <button class="quick-btn" onclick="send('下周有多少廠商的貨要進來？')"><span class="q-icon">📦</span>下周到貨清單</button>
    <button class="quick-btn" onclick="send('銀行帳戶目前有多少錢？')"><span class="q-icon">🏦</span>銀行帳戶餘額</button>
    <button class="quick-btn" onclick="send('本年度的銷售收入是多少？')"><span class="q-icon">📊</span>年度銷售收入</button>
    <button class="quick-btn" onclick="send('目前有哪些未收的應收帳款？')"><span class="q-icon">💰</span>應收帳款明細</button>
    <button class="quick-btn" onclick="send('本月的進貨總金額是多少？')"><span class="q-icon">🚚</span>本月進貨總額</button>
    <button class="quick-btn" onclick="send('有哪些採購訂單還有未到貨數量？')"><span class="q-icon">📋</span>未到貨採購單</button>
    <button class="quick-btn" onclick="send('現金及銀行存款的科目餘額？')"><span class="q-icon">💳</span>現金銀行科目</button>
    <button class="quick-btn" onclick="send('本年度的費用支出是多少？')"><span class="q-icon">📉</span>年度費用支出</button>

    <div class="sidebar-footer">
      Powered by Claude Haiku 4.5<br>+ SQL Server ERP
    </div>
  </div>

  <!-- 主區 -->
  <div class="main">
    <div class="topbar">
      <span class="topbar-title">🤖 AI 查詢助理</span>
      <span class="topbar-badge">claude-haiku-4-5</span>
    </div>

    <div class="chat-area" id="chatArea">
      <div class="chat-inner" id="chatInner">
        <!-- 歡迎畫面 -->
        <div class="welcome" id="welcome">
          <div class="w-icon">🏭</div>
          <h2>您好，請問有什麼可以幫您查詢的？</h2>
          <p>用自然語言詢問財務、採購、應收帳款等任何 ERP 資料</p>
          <div class="welcome-grid">
            <div class="welcome-card" onclick="send('下周有多少廠商的貨要進來？')">
              <div class="wc-icon">📦</div>
              <div>下周到貨清單</div>
              <div class="wc-text">查詢採購訂單預計到貨</div>
            </div>
            <div class="welcome-card" onclick="send('銀行帳戶目前有多少錢？')">
              <div class="wc-icon">🏦</div>
              <div>銀行帳戶餘額</div>
              <div class="wc-text">查詢現金及銀行存款</div>
            </div>
            <div class="welcome-card" onclick="send('本年度的銷售收入是多少？')">
              <div class="wc-icon">📊</div>
              <div>年度銷售收入</div>
              <div class="wc-text">查詢分類帳收入科目</div>
            </div>
            <div class="welcome-card" onclick="send('目前有哪些未收的應收帳款？')">
              <div class="wc-icon">💰</div>
              <div>應收帳款明細</div>
              <div class="wc-text">查詢客戶未收款項</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="input-bar">
      <div class="input-inner">
        <div class="input-wrap">
          <textarea id="q" rows="1" placeholder="請輸入問題，例如：下周有多少廠商的貨要進來？" oninput="autoResize(this)"></textarea>
        </div>
        <button class="send-btn" id="sendBtn" onclick="submit()" title="送出 (Ctrl+Enter)">➤</button>
      </div>
      <div class="input-hint">Ctrl + Enter 送出</div>
    </div>
  </div>
</div>

<script>
const chatInner = document.getElementById('chatInner');
const welcome   = document.getElementById('welcome');
const chatArea  = document.getElementById('chatArea');
const qEl       = document.getElementById('q');
const sendBtn   = document.getElementById('sendBtn');

// Ctrl+Enter
qEl.addEventListener('keydown', e => {
  if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); submit(); }
});

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 160) + 'px';
}

function send(text) {
  qEl.value = text;
  autoResize(qEl);
  submit();
}

function addMsg(role, html) {
  if (role === 'user' && welcome) welcome.style.display = 'none';
  const isUser = role === 'user';
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  div.innerHTML = `
    <div class="avatar ${role}">${isUser ? '👤' : '🤖'}</div>
    <div class="bubble">${html}</div>
  `;
  chatInner.appendChild(div);
  chatArea.scrollTop = chatArea.scrollHeight;
  return div;
}

function addThinking() {
  const div = document.createElement('div');
  div.className = 'msg ai';
  div.id = 'thinking';
  div.innerHTML = `
    <div class="avatar ai">🤖</div>
    <div class="bubble thinking">
      <div class="dots"><span></span><span></span><span></span></div>
      <span>AI 正在查詢資料庫...</span>
    </div>`;
  chatInner.appendChild(div);
  chatArea.scrollTop = chatArea.scrollHeight;
  return div;
}

async function submit() {
  const q = qEl.value.trim();
  if (!q || sendBtn.disabled) return;

  addMsg('user', escHtml(q));
  qEl.value = ''; qEl.style.height = 'auto';

  sendBtn.disabled = true;
  const thinking = addThinking();

  try {
    const res  = await fetch('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q })
    });
    const data = await res.json();
    thinking.remove();
    if (!res.ok) throw new Error(data.detail || '查詢失敗');
    addMsg('ai', marked.parse(data.answer));
  } catch(err) {
    thinking.remove();
    addMsg('ai', `<span style="color:#f85149">❌ ${escHtml(err.message)}</span>`);
  } finally {
    sendBtn.disabled = false;
    qEl.focus();
    chatArea.scrollTop = chatArea.scrollHeight;
  }
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>');
}
</script>
</body>
</html>"""
    return HTMLResponse(content=html)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
