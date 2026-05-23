"""
main.py - FastAPI 應用程式
提供 REST API 和 HTML 問答介面
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from claude_service import ask_erp

app = FastAPI(title="ERP 人話查詢系統", version="1.0.0")


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    answer: str


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """接收自然語言問題，回傳自然語言答案"""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="問題不能為空")
    try:
        answer = await ask_erp(request.question)
        return AnswerResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢失敗：{str(e)}")


@app.get("/", response_class=HTMLResponse)
async def home():
    """ERP 人話查詢介面"""
    html = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ERP 人話查詢系統</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Microsoft JhengHei', 'PingFang TC', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .container {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 40px;
            width: 100%;
            max-width: 800px;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
        }

        .header {
            text-align: center;
            margin-bottom: 35px;
        }

        .header h1 {
            font-size: 2rem;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: 2px;
            text-shadow: 0 0 20px rgba(100, 200, 255, 0.5);
        }

        .header .subtitle {
            color: rgba(255,255,255,0.6);
            margin-top: 8px;
            font-size: 0.95rem;
        }

        .icon {
            font-size: 3rem;
            margin-bottom: 10px;
        }

        .examples {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 20px;
        }

        .example-btn {
            background: rgba(100, 150, 255, 0.15);
            border: 1px solid rgba(100, 150, 255, 0.3);
            color: rgba(255, 255, 255, 0.8);
            padding: 6px 14px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.85rem;
            font-family: inherit;
            transition: all 0.2s;
        }

        .example-btn:hover {
            background: rgba(100, 150, 255, 0.3);
            border-color: rgba(100, 150, 255, 0.6);
            color: white;
        }

        .input-area {
            position: relative;
            margin-bottom: 15px;
        }

        textarea {
            width: 100%;
            padding: 16px 50px 16px 18px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.08);
            color: white;
            font-size: 1rem;
            font-family: inherit;
            resize: vertical;
            min-height: 80px;
            line-height: 1.5;
            transition: border-color 0.2s;
            outline: none;
        }

        textarea::placeholder {
            color: rgba(255, 255, 255, 0.4);
        }

        textarea:focus {
            border-color: rgba(100, 150, 255, 0.6);
            background: rgba(255, 255, 255, 0.1);
        }

        .btn {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #4a90d9, #5b6abf);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1.05rem;
            font-weight: 600;
            font-family: inherit;
            cursor: pointer;
            transition: all 0.2s;
            letter-spacing: 1px;
        }

        .btn:hover:not(:disabled) {
            background: linear-gradient(135deg, #5ba3e8, #6c7bd0);
            transform: translateY(-1px);
            box-shadow: 0 8px 20px rgba(74, 144, 217, 0.3);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .loading {
            text-align: center;
            color: rgba(255,255,255,0.7);
            padding: 20px;
            display: none;
        }

        .loading-dots {
            display: inline-flex;
            gap: 6px;
            align-items: center;
        }

        .loading-dots span {
            width: 8px;
            height: 8px;
            background: #4a90d9;
            border-radius: 50%;
            animation: bounce 1.2s ease-in-out infinite;
        }

        .loading-dots span:nth-child(2) { animation-delay: 0.2s; }
        .loading-dots span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes bounce {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }

        .answer-box {
            margin-top: 25px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            padding: 20px;
            display: none;
        }

        .answer-box.show { display: block; }

        .answer-label {
            font-size: 0.8rem;
            color: rgba(100, 200, 255, 0.8);
            letter-spacing: 1px;
            margin-bottom: 10px;
            font-weight: 600;
        }

        .answer-content {
            color: rgba(255, 255, 255, 0.9);
            line-height: 1.8;
            font-size: 0.98rem;
            white-space: pre-wrap;
        }

        .error-box {
            margin-top: 15px;
            background: rgba(255, 100, 100, 0.1);
            border: 1px solid rgba(255, 100, 100, 0.3);
            border-radius: 12px;
            padding: 15px;
            color: #ff8888;
            display: none;
        }

        .error-box.show { display: block; }

        .footer {
            text-align: center;
            margin-top: 25px;
            color: rgba(255,255,255,0.3);
            font-size: 0.8rem;
        }

        .hint {
            color: rgba(255,255,255,0.4);
            font-size: 0.82rem;
            margin-top: 8px;
            text-align: right;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="icon">🤖</div>
            <h1>ERP 人話查詢系統</h1>
            <p class="subtitle">用自然語言詢問公司財務與採購資料</p>
        </div>

        <div class="examples">
            <button class="example-btn" onclick="setQuestion('下周有多少廠商的貨要進來？')">📦 下周到貨</button>
            <button class="example-btn" onclick="setQuestion('銀行帳戶目前有多少錢？')">🏦 銀行餘額</button>
            <button class="example-btn" onclick="setQuestion('本年度銷售金額是多少？')">📊 年度銷售</button>
            <button class="example-btn" onclick="setQuestion('目前有哪些未收的應收帳款？')">💰 應收帳款</button>
            <button class="example-btn" onclick="setQuestion('本月進貨總額是多少？')">🚚 本月進貨</button>
            <button class="example-btn" onclick="setQuestion('有哪些逾期未收的客戶帳款？')">⚠️ 逾期帳款</button>
        </div>

        <div class="input-area">
            <textarea
                id="question"
                placeholder="請輸入您的問題，例如：下周有多少廠商的貨要進來？"
                rows="3"
            ></textarea>
        </div>

        <p class="hint">按 Ctrl+Enter 送出 | Enter 換行</p>

        <button class="btn" id="submitBtn" onclick="submitQuestion()">
            送出查詢
        </button>

        <div class="loading" id="loading">
            <div class="loading-dots">
                <span></span><span></span><span></span>
            </div>
            <p style="margin-top: 10px;">AI 正在查詢資料庫，請稍候...</p>
        </div>

        <div class="error-box" id="errorBox"></div>

        <div class="answer-box" id="answerBox">
            <div class="answer-label">▎ AI 回答</div>
            <div class="answer-content" id="answerContent"></div>
        </div>

        <div class="footer">
            Powered by Claude claude-opus-4-7 + SQL Server ERP
        </div>
    </div>

    <script>
        const questionEl = document.getElementById('question');
        const submitBtn = document.getElementById('submitBtn');
        const loadingEl = document.getElementById('loading');
        const answerBox = document.getElementById('answerBox');
        const answerContent = document.getElementById('answerContent');
        const errorBox = document.getElementById('errorBox');

        // Ctrl+Enter 送出
        questionEl.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                submitQuestion();
            }
        });

        function setQuestion(text) {
            questionEl.value = text;
            questionEl.focus();
        }

        async function submitQuestion() {
            const question = questionEl.value.trim();
            if (!question) {
                questionEl.focus();
                return;
            }

            // Reset UI
            submitBtn.disabled = true;
            loadingEl.style.display = 'block';
            answerBox.classList.remove('show');
            errorBox.classList.remove('show');

            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question }),
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || '查詢失敗');
                }

                answerContent.textContent = data.answer;
                answerBox.classList.add('show');
            } catch (err) {
                errorBox.textContent = '❌ 錯誤：' + err.message;
                errorBox.classList.add('show');
            } finally {
                submitBtn.disabled = false;
                loadingEl.style.display = 'none';
            }
        }
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
