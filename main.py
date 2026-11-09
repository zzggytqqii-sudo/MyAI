import os
import sys
import time
import random
import torch
import torch.nn as nn
import torch.nn.functional as F
import threading
import urllib.request
import json
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from duckduckgo_search import DDGS

import warnings
warnings.filterwarnings("ignore")

MODEL_FILE = "agent_checkpoint.pt"
DATA_DIR = "web_corpus"
os.makedirs(DATA_DIR, exist_ok=True)

# حالة النظام لعرضها على لوحة التحكم localhost:8080
state = {
    "step": 0,
    "loss": 0.0,
    "val_loss": 0.0,
    "vocab_size": 0,
    "generated_text": "Agent is initializing global web exploration...",
    "status": "Running Free Web Scraper & Trainer"
}
lock = threading.Lock()

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        html = f"""
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>لوحة الوكيل الحر - Global AI Agent</title>
            <style>
                body {{ background: #0f172a; color: #f8fafc; font-family: sans-serif; padding: 20px; }}
                .card {{ background: #1e293b; padding: 20px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
                h1 {{ color: #38bdf8; font-size: 22px; }}
                .stat {{ font-size: 20px; color: #4ade80; font-weight: bold; }}
                .log {{ background: #000; padding: 10px; border-radius: 6px; font-family: monospace; color: #a3e635; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <h1>🌐 لوحة التحكم بالوكيل الحر (Global Web Explorer)</h1>
            <div class="card">
                <p>حالة الوكيل: <span style="color: #38bdf8;">{state['status']}</span></p>
                <p>دورات التعلم: <span class="stat">{state['step']}</span> | معدل الخطأ: <span class="stat">{state['loss']}</span></p>
                <p>حجم المعجم: <span class="stat">{state['vocab_size']}</span> كلمة</p>
            </div>
            <div class="card">
                <h3>🧠 آخر ما استكشفه وتعلمه الوكيل:</h3>
                <div class="log">{state['generated_text']}</div>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        pass

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

def log_tv(stage, msg):
    t = time.strftime("%H:%M:%S")
    print(f"[{t}] [{stage}] {msg}")
    sys.stdout.flush()

# نموذج عصبية متطور للتعامل مع النصوص
class GlobalAgentModel(nn.Module):
    def __init__(self, vocab_size):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, 64)
        self.rnn = nn.LSTM(64, 128, num_layers=2, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(128, vocab_size)

    def forward(self, x):
        return self.fc(self.rnn(self.emb(x))[0])

def tokenize(text):
    return re.findall(r"\b\w+\b", text.lower(), re.UNICODE)

# حلقة الاستكشاف الحر عبر الويب وجوجل ومختلف المواقع
def continuous_learning_worker():
    log_tv("INIT", "Starting autonomous global web exploration worker...")
    
    # استعلامات بحث مفتوحة تغطي كل شيء في الإنترنت (جوجل، جيت هاب، أبحاث، أكواد، تقنية)
    search_queries = [
        "site:github.com python ai agent framework",
        "site:arxiv.org artificial intelligence reasoning",
        "latest programming tutorials and documentation",
        "neural network architecture implementation python",
        "advanced autonomous software development concepts"
    ]
    
    vocab = ["<unk>", "ai", "agent", "python", "data", "system"]
    stoi = {w: i for i, w in enumerate(vocab)}
    itos = {i: w for i, w in enumerate(vocab)}
    
    model = GlobalAgentModel(len(vocab))
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001)
    
    step = 0
    while True:
        try:
            step += 1
            query = random.choice(search_queries)
            log_tv("SEARCH", f"Exploring web with query: {query}")
            
            scraped_text = ""
            try:
                with DDGS() as ddgs:
                    results = [r for r in ddgs.text(query, max_results=3)]
                    for res in results:
                        link = res.get("href", "")
                        body = res.get("body", "")
                        scraped_text += f"\n{body}"
                        log_tv("FETCH", f"Visited link: {link[:50]}...")
                        
                        # محاولة سحب محتوى الصفحة الخام إذا أمكن
                        try:
                            req = urllib.request.Request(link, headers={"User-Agent": "Mozilla/5.0"})
                            with urllib.request.urlopen(req, timeout=5) as resp:
                                html_content = resp.read().decode("utf-8", errors="ignore")
                                clean_text = re.sub(r'<[^>]+>', ' ', html_content)
                                scraped_text += f"\n{clean_text[:2000]}"
                        except:
                            pass
            except Exception as e:
                log_tv("WARN", f"Search minor error: {e}")
                scraped_text = "Autonomous agent global web exploration fallback training text."

            # تحديث المعجم والكلمات بناءً على البيانات الجديدة المسحوبة من أي مكان
            new_words = tokenize(scraped_text)
            for w in new_words:
                if w not in stoi and len(vocab) < 10000:
                    stoi[w] = len(vocab)
                    itos[len(vocab)] = w
                    vocab.append(w)
            
            if len(vocab) != model.fc.out_features:
                model = GlobalAgentModel(len(vocab))
                optimizer = torch.optim.AdamW(model.parameters(), lr=0.001)

            ids = torch.tensor([stoi.get(w, 0) for w in new_words[:1000]], dtype=torch.long)
            
            if len(ids) > 16:
                x, y = ids[:-15], ids[15:]
                out = model(x[:32].unsqueeze(0))
                loss = F.cross_entropy(out.reshape(-1, len(vocab)), y[:32])
                
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                
                loss_val = round(loss.item(), 4)
                log_tv("TRAIN", f"Step {step} | Loss: {loss_val} | Vocab: {len(vocab)}")
                
                with lock:
                    state["step"] = step
                    state["loss"] = loss_val
                    state["vocab_size"] = len(vocab)
                    state["generated_text"] = scraped_text[:300]
                    state["status"] = f"Exploring: {query[:30]}..."
            
            time.sleep(5)
            
        except Exception as e:
            log_tv("ERROR", f"Worker loop error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    try:
        continuous_learning_worker()
    except KeyboardInterrupt:
        log_tv("STOP", "Agent stopped by user.")
        
