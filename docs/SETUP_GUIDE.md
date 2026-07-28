# 🚀 Autonomous DevOps — Setup Guide

## Step-by-Step Installation & Configuration

---

## 📦 Step 1: Install Prerequisites

### Python 3.10+

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git

# Verify
python3 --version  # Should be 3.10 or higher
```

### Node.js 18+

```bash
# Using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
nvm install 18
nvm use 18

# Verify
node --version
```

### Docker & Docker Compose

| Platform | Instructions |
|----------|-------------|
| **macOS** | Download [Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| **Windows** | Download [Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| **Linux** | Follow [Docker Engine install](https://docs.docker.com/engine/install/) |

```bash
# Verify
docker --version
docker compose version
```

---

## 🔑 Step 2: Generate API Keys

### OpenAI API Key

1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click **Create new secret key**
3. Copy the key — you won't be able to see it again!

### GitHub Personal Access Token

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click **Generate new token (classic)**
3. Select scope: `repo` (full control)
4. Copy the token

### Langfuse (Optional — for Tracing)

1. Go to [langfuse.com](https://langfuse.com)
2. Create an account and project
3. Copy **Public Key** and **Secret Key**

---

## 🚀 Step 3: Run the Application

### Option A: Docker Compose (Easiest)

```bash
# 1. Clone the repo
git clone https://github.com/Sarancoding/Autonomous-DevOps.git
cd Autonomous-DevOps

# 2. Set environment variables (optional — can also set via UI)
export LLM_API_KEY=sk-your-key-here
export GITHUB_TOKEN=ghp_your-token-here

# 3. Start all services
docker compose up --build
```

This starts:
- ✅ Backend API → `http://localhost:8000`
- ✅ Frontend Dashboard → `http://localhost:5173`
- ✅ Redis → `localhost:6379`

### Option B: Manual (for Development)

**Terminal 1 — Backend:**
```bash
cd Autonomous-DevOps/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd Autonomous-DevOps/frontend
npm install
npm run dev
```

---

## 🎯 Step 4: Configure the Dashboard

1. **Open the app** → [http://localhost:5173](http://localhost:5173)

2. **Go to Settings** (sidebar bottom)
   ![Settings page showing API key inputs]
   
3. **Enter your API keys:**
   - LLM API Key (OpenAI or OpenRouter)
   - GitHub Personal Access Token
   
4. **Click "Save Keys"** — your session is now configured

---

## 🧪 Step 5: Test with a Sample Run

### Get a Sample Failing Test

Here's a simple Python test that will trigger a failure:

```python
# test_math.py
def test_divide():
    assert 10 / 2 == 5
    assert 10 / 0 == 0  # This will fail!
```

Run it locally to get the stack trace:
```bash
pytest test_math.py --tb=long
```

### Trigger the Agent

1. Go to **Dashboard**
2. Enter a repository URL (any GitHub repo)
3. Paste the failure log / stack trace
4. Click **Run Agent**

### Watch the Magic

The dashboard will show:
1. 🔍 **Analyze Failure** — Parsing the stack trace
2. 📂 **Retrieve Context** — Reading the error file
3. 🧠 **Generate Fix** — LLM creating a patch
4. 🧪 **Sandbox Verify** — Running tests in isolation
5. 🚀 **Submit PR** — Creating a GitHub pull request

---

## 🌐 Step 6: Configure GitHub Webhook (Optional)

For automatic triggering on CI failures:

1. Go to your repo → **Settings** → **Webhooks** → **Add webhook**
2. **Payload URL**: `https://your-domain.com/webhook/github`
3. **Content type**: `application/json`
4. **Secret**: A random string (match `GITHUB_WEBHOOK_SECRET` in backend config)
5. **Events**: Select:
   - ✔ Check runs
   - ✔ Push events
   - ✔ Workflow runs
6. **Active**: ✅
7. Click **Add webhook**

Now whenever a CI check fails, the agent will automatically:
- Parse the failure
- Generate a fix
- Verify it
- Submit a PR!

---

## 📊 Step 7: Monitor Your Agents

### Dashboard Overview
The dashboard shows:
- Total jobs and success rate
- Live agent execution timeline
- Real-time logs via WebSocket

### Analytics Page
- Token usage and cost estimates
- Success/failure distribution
- Agent performance metrics

---

## 🔧 Troubleshooting

### "Cannot connect to backend"

```bash
# Check if the backend is running
curl http://localhost:8000/api/status
```

Expected response:
```json
{"status": "ok", "version": "1.0.0", "jobs_running": 0}
```

### "Docker not available"

If Docker is not installed, the sandbox verification step will be skipped:
- Set `DOCKER_ENABLED=false` in `.env`
- The agent will still generate and submit fixes, but without verification

### "LLM API key invalid"

1. Go to **Settings** page
2. Re-enter your API key
3. Ensure it's for the correct model (GPT-4o requires access)

### "GitHub token permissions"

Ensure your PAT has the `repo` scope:
1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Edit your token
3. Select `repo` (all checked)

### "WebSocket disconnected"

- Check CORS settings in backend config
- Ensure the frontend proxy is configured correctly
- Try refreshing the page

---

## 📈 Performance Optimization Tips

| Optimization | Impact | How |
|-------------|--------|-----|
| Use cheap model for analysis | ⚡ Reduces cost 10x | Set `LLM_CHEAP_MODEL=gpt-4o-mini` |
| Lower max attempts | ⚡ Faster runs | Set `max_attempts: 2` |
| Increase sandbox timeout | 🔧 Handles larger repos | Set `SANDBOX_TIMEOUT: 300` |
| Enable Langfuse | 📊 Track spending | Set `LANGFUSE_*` env vars |
| Use Redis | 💪 Persistent state | Set `REDIS_URL` |

---

## 🚢 Production Deployment Checklist

- [ ] Use HTTPS (TLS certificate)
- [ ] Set strong `GITHUB_WEBHOOK_SECRET`
- [ ] Configure database-backed job persistence
- [ ] Set up proper secrets management (Vault)
- [ ] Enable monitoring (Prometheus/Grafana)
- [ ] Set resource limits in Docker Compose
- [ ] Configure log rotation
- [ ] Regular key rotation schedule

---

## ❓ FAQ

### Q: Does the agent have access to my source code?
**A:** Yes, temporarily. Code is cloned to a temporary directory and deleted after the job completes. Never share API keys that have access to sensitive repositories.

### Q: What LLM providers are supported?
**A:** Any OpenAI-compatible API. This includes OpenAI, OpenRouter, Azure OpenAI, and local LLMs via vLLM or Ollama.

### Q: Can I use a local LLM instead of OpenAI?
**A:** Yes! Set `LLM_API_BASE` to your local endpoint (e.g., `http://localhost:1234/v1` for LM Studio).

### Q: How are tokens counted and optimized?
**A:** The agent only sends ±10 lines of code context per prompt, prunes history to 5 entries, and uses cheap models for analysis tasks. Observation via Langfuse tracks all token usage.

### Q: Can I customize the fix prompt?
**A:** Yes. Modify the system prompts in `backend/services/llm_service.py` to adjust fix generation behavior.

---

<p align="center">
  Need help? <a href="https://github.com/Sarancoding/Autonomous-DevOps/issues">Open an issue</a><br/>
  Built with ❤️ by Sarancoding
</p>
