#!/usr/bin/env python3
"""Generate professional PDF documents for the Autonomous DevOps project.

Produces:
  - docs/SETUP_GUIDE.pdf   - Step-by-step installation & configuration guide
  - docs/PROJECT_DOCUMENT.pdf - Full architecture, API, and technical reference

Usage:
  python docs/generate_pdfs.py
"""

from __future__ import annotations

import os
from datetime import datetime

from fpdf import FPDF

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------

C_PRIMARY = (79, 70, 229)     # Indigo
C_SECONDARY = (139, 92, 246)  # Violet
C_SUCCESS = (16, 185, 129)    # Emerald
C_DANGER = (239, 68, 68)      # Red
C_WARNING = (245, 158, 11)    # Amber
C_DARK = (30, 41, 59)         # Slate-800
C_MID = (71, 85, 105)         # Slate-600
C_LIGHT = (100, 116, 139)     # Slate-500
C_BG_LIGHT = (248, 250, 252)  # Slate-50
C_CODE_BG = (241, 245, 249)   # Slate-100
C_WHITE = (255, 255, 255)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Custom PDF class
# ---------------------------------------------------------------------------

class DocPDF(FPDF):
    """Professional PDF document."""

    def __init__(self, title: str, subject: str = "") -> None:
        super().__init__()
        self.set_auto_page_break(auto=True, margin=25)
        self.doc_title = title
        self.set_title(title)
        self.set_subject(subject or title)
        self.set_author("Autonomous DevOps Team")

    # -- Header / Footer ------------------------------------------------ #

    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*C_LIGHT)
        self.cell(0, 8, self.doc_title, align="L")
        self.cell(0, 8, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*C_MID)
        self.line(10, 15, 200, 15)
        self.ln(4)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*C_LIGHT)
        self.cell(0, 10, f"(c) {datetime.now().year} Autonomous DevOps -- Confidential", align="C")

    # -- Styling helpers ------------------------------------------------ #

    def cover_page(self, subtitle: str, version: str = "1.0.0") -> None:
        """Render a professional cover page."""
        self.add_page()
        self.ln(50)
        # Decorative top bar
        self.set_fill_color(*C_PRIMARY)
        self.rect(0, 0, 210, 6, "F")

        # Title
        self.set_font("Helvetica", "B", 30)
        self.set_text_color(*C_PRIMARY)
        self.cell(0, 14, "Autonomous DevOps", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(*C_SECONDARY)
        self.cell(0, 12, self.doc_title, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(8)

        # Divider
        self.set_draw_color(*C_PRIMARY)
        self.set_line_width(0.6)
        self.line(65, self.get_y(), 145, self.get_y())
        self.ln(10)

        # Subtitle
        self.set_font("Helvetica", "", 11)
        self.set_text_color(*C_MID)
        self.multi_cell(0, 7, subtitle, align="C")
        self.ln(20)

        # Meta info
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*C_LIGHT)
        for line in [
            f"Version: {version}",
            f"Date: {datetime.now().strftime('%B %d, %Y')}",
            "License: MIT",
        ]:
            self.cell(0, 7, line, align="C", new_x="LMARGIN", new_y="NEXT")

        # Bottom bar
        self.set_fill_color(*C_PRIMARY)
        self.rect(0, 291, 210, 6, "F")

    def section_title(self, num: str, title: str) -> None:
        """Section heading with colored bar."""
        self.ln(4)
        # Left color bar
        self.set_fill_color(*C_PRIMARY)
        self.rect(10, self.get_y(), 2, 10, "F")
        self.set_x(14)
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(*C_PRIMARY)
        self.cell(0, 10, f"{num}. {title}", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def subsection(self, title: str) -> None:
        self.ln(2)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*C_DARK)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text: str) -> None:
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*C_MID)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def bullet(self, text: str, indent: float = 12) -> None:
        # Save current line and write bullet with proper indent
        self.set_x(self.l_margin + indent)
        self.set_font("Courier", "", 8)
        self.set_text_color(*C_PRIMARY)
        self.cell(4, 5, ">", new_x="RIGHT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*C_MID)
        w = self.w - self.get_x() - self.r_margin
        self.multi_cell(w, 5, text)

    def code_block(self, code: str) -> None:
        """Code block with background and border."""
        self.ln(2)
        lines = code.strip().split("\n")
        block_h = len(lines) * 4.5 + 5
        y_start = self.get_y()

        # Check page break
        if y_start + block_h > 270:
            self.add_page()
            y_start = self.get_y()

        # Background
        self.set_fill_color(*C_CODE_BG)
        self.set_font("Courier", "", 7)
        self.set_text_color(*C_DARK)

        for line in lines:
            self.set_x(12)
            # Escape special characters for PDF
            display_line = line.replace("\\", "\\\\")
            self.cell(186, 4.5, f"  {display_line}", fill=True, new_x="LMARGIN", new_y="NEXT")

        # Border
        self.set_draw_color(*C_MID)
        self.rect(10, y_start, 190, block_h)
        self.ln(3)

    def tip_box(self, text: str, icon: str = "[i]") -> None:
        """Info/tip box with colored background."""
        self.ln(2)
        self.set_fill_color(236, 254, 255)
        self.set_draw_color(34, 211, 238)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*C_MID)
        y = self.get_y()
        self.set_x(12)
        self.multi_cell(186, 5, f"{icon}  {text}", fill=True)
        self.set_draw_color(34, 211, 238)
        self.rect(10, y, 190, self.get_y() - y)
        self.ln(2)

    def table(self, headers: list[str], rows: list[list[str]]) -> None:
        """Simple table with header row and alternating colors."""
        col_width = 190 / len(headers)

        # Header
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(*C_PRIMARY)
        self.set_text_color(*C_WHITE)
        self.set_draw_color(*C_PRIMARY)
        for h in headers:
            self.cell(col_width, 7, f" {h}", border=1, fill=True, align="C")
        self.ln()

        # Rows
        self.set_font("Helvetica", "", 7.5)
        self.set_draw_color(200, 200, 200)
        for idx, row in enumerate(rows):
            if idx % 2 == 0:
                self.set_fill_color(248, 250, 252)
            else:
                self.set_fill_color(255, 255, 255)
            self.set_text_color(*C_MID)
            for i, cell in enumerate(row):
                self.cell(col_width, 6, f" {cell}", border=1, fill=True, align="C" if i == 1 else "L")
            self.ln()
        self.ln(3)

    def new_page(self) -> None:
        self.add_page()


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def build_setup_guide(doc: DocPDF) -> None:
    """Build the Setup Guide PDF."""
    doc.cover_page(
        subtitle="Complete step-by-step guide to install, configure, and run\nthe Self-Healing CI/CD Agent"
    )

    # 1. Prerequisites
    doc.new_page()
    doc.section_title("1", "Prerequisites")
    doc.body_text("Before you begin, ensure you have the following installed on your system:")
    doc.bullet("Python 3.10+ -- Download from python.org or use pyenv")
    doc.bullet("Node.js 18+ -- Download from nodejs.org or use nvm")
    doc.bullet("Docker 24+ -- Download from docker.com (required for sandbox verification)")
    doc.bullet("Git -- Usually pre-installed; apt install git / brew install git")

    doc.subsection("API Keys Required")
    doc.table(
        ["Service", "Purpose", "Where to Get"],
        [
            ["OpenAI / OpenRouter", "LLM for code analysis & fixes", "platform.openai.com/api-keys"],
            ["GitHub PAT", "Repo access & PR creation", "github.com/settings/tokens"],
            ["Langfuse (optional)", "Observability & tracing", "langfuse.com"],
        ],
    )

    # 2. Quick Start
    doc.new_page()
    doc.section_title("2", "Quick Start")
    doc.subsection("2.1 Clone the Repository")
    doc.code_block("git clone https://github.com/Sarancoding/Autonomous-DevOps.git\ncd Autonomous-DevOps")

    doc.subsection("2.2 Backend Setup")
    doc.code_block(
        "cd backend\n"
        "python3 -m venv .venv\n"
        "source .venv/bin/activate\n"
        "pip install -r requirements.txt"
    )

    doc.subsection("2.3 Frontend Setup")
    doc.code_block(
        "cd frontend\n"
        "npm install          # or: bun install\n"
        "npm run dev          # or: bun dev"
    )

    doc.subsection("2.4 Configure Environment")
    doc.code_block(
        "# Create .env file:\n"
        "LLM_API_KEY=sk-your-key-here\n"
        "GITHUB_TOKEN=ghp_your-token-here\n"
        "GITHUB_WEBHOOK_SECRET=your-webhook-secret"
    )

    doc.subsection("2.5 Run with Docker Compose")
    doc.code_block("docker compose up --build")
    doc.body_text("This starts: Backend (localhost:8000), Frontend (localhost:5173), Redis.")

    # 3. GitHub Webhook
    doc.new_page()
    doc.section_title("3", "GitHub Webhook Configuration")
    doc.body_text("For automatic triggering on CI failures:")
    doc.bullet("Go to Settings -> Webhooks -> Add webhook")
    doc.bullet("Payload URL: https://your-domain.com/webhook/github")
    doc.bullet("Content type: application/json")
    doc.bullet("Secret: Match GITHUB_WEBHOOK_SECRET")
    doc.bullet("Events: Check runs, Push events, Workflow runs")
    doc.tip_box("The agent will automatically parse failures, generate fixes, verify in Docker, and submit a PR.", "[AI]")

    # 4. Dashboard Walkthrough
    doc.section_title("4", "Dashboard Walkthrough")
    doc.body_text("Open http://localhost:5173 and explore:")
    doc.bullet("Settings: Enter LLM API Key and GitHub Token (BYOK)")
    doc.bullet("Dashboard: Paste repo URL + failure log, click 'Run Agent'")
    doc.bullet("Job Detail: View timeline, diff, live WebSocket logs")
    doc.bullet("Analytics: Track token usage, costs, success rates")

    # 5. Troubleshooting
    doc.new_page()
    doc.section_title("5", "Troubleshooting")
    doc.table(
        ["Problem", "Solution"],
        [
            ["Backend won't start", "Set LLM_API_KEY environment variable"],
            ["Docker sandbox fails", "Ensure Docker is running: docker info"],
            ["WebSocket not connecting", "Check CORS origins in config"],
            ["GitHub token issue", "Ensure PAT has 'repo' scope"],
            ["LLM API key invalid", "Verify key has GPT-4o access"],
        ],
    )

    # 6. Security
    doc.section_title("6", "Security Best Practices")
    doc.bullet("BYOK: API keys sent via headers, never persisted to disk")
    doc.bullet("Zero retention: Source code deleted after job completes")
    doc.bullet("Sandbox isolation: Each job in isolated Docker container, no network")
    doc.bullet("HMAC verification: Webhook signatures validated on every request")
    doc.bullet("Audit logs: All agent actions logged with timestamps")

    # 7. License
    doc.section_title("7", "License")
    doc.body_text("This project is licensed under the MIT License.")


def build_project_document(doc: DocPDF) -> None:
    """Build the Project Document PDF."""
    doc.cover_page(
        subtitle="Complete architecture, API reference, and technical documentation\nfor the LangGraph-powered Self-Healing CI/CD Agent"
    )

    # 1. Overview
    doc.new_page()
    doc.section_title("1", "Project Overview")
    doc.body_text(
        "Autonomous DevOps is a self-healing CI/CD agent that automatically detects test failures "
        "from GitHub webhooks, analyzes the root cause using LLMs, generates verified fixes, "
        "and submits pull requests -- all without human intervention."
    )
    doc.body_text(
        "The system is built on three core engineering principles: Graph Engineering (LangGraph "
        "for stateful agent workflows), Loop Engineering (resilient retry loops with confidence-based "
        "early stopping), and Zero-Trust Security (users bring their own keys, no data persistence)."
    )

    # 2. Architecture
    doc.new_page()
    doc.section_title("2", "System Architecture")
    doc.body_text(
        "The system follows a microservices architecture: FastAPI backend (orchestrator), "
        "React frontend (dashboard), and Docker sandbox (execution). Communication via REST + WebSockets."
    )

    doc.subsection("2.1 Technology Stack")
    doc.table(
        ["Layer", "Technology", "Purpose"],
        [
            ["Orchestration", "LangGraph", "State machine with typed state & edges"],
            ["Backend API", "FastAPI", "Async webhook listener & REST endpoints"],
            ["LLM Integration", "OpenAI / OpenRouter", "Code analysis & fix generation"],
            ["Sandbox", "Docker SDK", "Isolated test execution per job"],
            ["Frontend", "React 18 + Vite", "Real-time dashboard"],
            ["Styling", "TailwindCSS", "Responsive dark/light mode"],
            ["Charts", "Recharts", "Token/cost metrics visualization"],
            ["Observability", "Langfuse", "Tracing & cost monitoring"],
            ["Deployment", "Docker Compose / K8s", "Production orchestration"],
        ],
    )

    # 3. LangGraph State Machine
    doc.new_page()
    doc.section_title("3", "LangGraph State Machine")
    doc.subsection("3.1 AgentState (TypedDict)")
    doc.code_block(
        "class AgentState(TypedDict):\n"
        "    repo_url: str           # GitHub repo URL\n"
        "    commit_sha: str         # Commit SHA\n"
        "    failure_log: str        # Raw failure log\n"
        "    stack_trace: str        # Extracted trace\n"
        "    file_path: str          # Error file\n"
        "    line_number: int        # Error line\n"
        "    error_type: str         # Error type\n"
        "    proposed_fix: str       # AI-generated patch\n"
        "    code_diff: str          # Unified diff\n"
        "    test_results: dict      # Sandbox outcome\n"
        "    pr_url: Optional[str]   # PR link\n"
        "    confidence_score: float # 0.0-1.0\n"
        "    attempts: int           # Fix attempt count\n"
        "    max_attempts: int       # Retry limit\n"
        "    history: list[str]      # Loop context\n"
        "    error: Optional[str]    # Error message\n"
        "    job_id: str             # Unique ID\n"
        "    agent_thoughts: list[str] # Live stream"
    )

    doc.subsection("3.2 Graph Nodes")
    doc.table(
        ["Node", "Description"],
        [
            ["analyze_failure", "Parse logs; regex first, LLM fallback"],
            ["retrieve_context", "Clone repo, read +/-10 lines"],
            ["generate_fix", "LLM generates unified diff patch"],
            ["sandbox_verify", "Run tests in isolated Docker container"],
            ["submit_pr", "Create GitHub PR via API"],
            ["flag_for_human", "Escalate when max retries exceeded"],
        ],
    )

    doc.subsection("3.3 Conditional Routing")
    doc.body_text("After sandbox_verify:")
    doc.bullet("Tests Passed -> submit_pr (end)")
    doc.bullet("Failed & attempts < max -> generate_fix (loop)")
    doc.bullet("Failed & attempts >= max -> flag_for_human (end)")

    # 4. Loop Engineering
    doc.new_page()
    doc.section_title("4", "Loop Engineering")
    doc.subsection("4.1 Exponential Backoff")
    doc.code_block(
        "async def retry_with_backoff(op, max=3, delay=1.0):\n"
        "    for attempt in range(1, max+1):\n"
        "        try: return await op()\n"
        "        except: await asyncio.sleep(delay)\n"
        "        delay = min(delay * 2, 30.0)"
    )
    doc.subsection("4.2 Early Stopping")
    doc.body_text(
        "The fix loop stops early when:\n"
        "  * Confidence >= 0.7 (fix is good enough)\n"
        "  * Confidence drops > 0.15 in last step (getting worse)\n"
        "  * Max attempts (default 3) reached"
    )
    doc.subsection("4.3 Context Pruning")
    doc.body_text(
        "Token minimisation:\n"
        "  * Only +/-10 lines sent per prompt\n"
        "  * History trimmed to last 5 entries\n"
        "  * Cheap model for analysis (gpt-4o-mini)\n"
        "  * Capable model only for fixes (gpt-4o)"
    )

    # 5. REST API
    doc.new_page()
    doc.section_title("5", "REST API Reference")
    doc.table(
        ["Method", "Endpoint", "Description"],
        [
            ["GET", "/api/status", "Health check"],
            ["POST", "/api/trigger", "Manual agent trigger"],
            ["GET", "/api/jobs/{id}", "Job details & logs"],
            ["GET", "/api/metrics", "Aggregated metrics"],
            ["POST", "/api/config", "Update agent settings"],
            ["POST", "/api/session/keys", "Store API keys (BYOK)"],
            ["POST", "/webhook/github", "GitHub webhook receiver"],
            ["WS", "/ws/jobs/{id}", "Real-time log streaming"],
        ],
    )
    doc.subsection("5.1 Trigger Request")
    doc.code_block(
        "POST /api/trigger\n"
        '{"repo_url":"https://github.com/owner/repo",\n'
        ' "failure_log":"Error: AssertionError...",\n'
        ' "max_attempts":3,"model":"gpt-4o"}'
    )
    doc.subsection("5.2 WebSocket Protocol")
    doc.code_block(
        "// Client connects to /ws/jobs/{job_id}\n"
        "// Server pushes: {\n"
        '  "type":"log","job_id":"abc",\n'
        '  "node":"analyze_failure",\n'
        '  "message":"Analyzing...",\n'
        '  "level":"info","timestamp":"..."\n'
        "}"
    )

    # 6. Security
    doc.new_page()
    doc.section_title("6", "Security & Privacy")
    doc.subsection("6.1 BYOK")
    doc.body_text(
        "API keys are stored ephemerally in browser session memory. "
        "Keys are sent via Authorization header, never persisted to server disk."
    )
    doc.subsection("6.2 Sandbox Isolation")
    doc.body_text(
        "Each job uses a dedicated Docker container:\n"
        "  * Network disabled\n"
        "  * CPU limited to 50%\n"
        "  * Memory capped at 512MB\n"
        "  * Read-only source volume\n"
        "  * Automatic cleanup after execution"
    )
    doc.subsection("6.3 Data Retention")
    doc.body_text(
        "Zero data retention: Source code cloned to temp directory, deleted post-job. "
        "Job metadata kept in-memory for session duration only."
    )

    # 7. Deployment
    doc.section_title("7", "Deployment")
    doc.subsection("7.1 Docker Compose")
    doc.code_block("docker compose up --build -d")
    doc.subsection("7.2 Kubernetes")
    doc.code_block(
        "kubectl create secret generic autodevops-secrets \\\n"
        "  --from-literal=LLM_API_KEY=sk-... \\\n"
        "  --from-literal=GITHUB_TOKEN=ghp_...\n"
        "kubectl apply -f k8s/"
    )
    doc.subsection("7.3 Production Checklist")
    doc.bullet("Set CORS_ORIGINS to your frontend domain")
    doc.bullet("Use proper secrets management (Vault / AWS Secrets Manager)")
    doc.bullet("Set up database-backed job persistence")
    doc.bullet("Enable HTTPS with proper TLS certificate")
    doc.bullet("Configure Prometheus + Grafana monitoring")

    # 8. Performance
    doc.new_page()
    doc.section_title("8", "Performance Benchmarks")
    doc.table(
        ["Metric", "Expected", "Notes"],
        [
            ["Time to analyze", "2-5s", "Regex first, then LLM"],
            ["Fix generation", "5-15s", "Depends on model"],
            ["Sandbox verify", "30-120s", "First run builds Docker image"],
            ["Token usage/job", "2K-8K", "With context pruning"],
            ["Success rate", "70-90%", "Varies by complexity"],
        ],
    )

    # 9. License
    doc.section_title("9", "License")
    doc.body_text("This project is licensed under the MIT License.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("[DOC] Generating Setup Guide PDF...")
    setup = DocPDF("Setup Guide", "Installation & Configuration Guide")
    build_setup_guide(setup)
    path1 = os.path.join(OUTPUT_DIR, "SETUP_GUIDE.pdf")
    setup.output(path1)
    print(f"  \u2705 {path1} ({setup.pages_count} pages)")

    print("[DOC] Generating Project Document PDF...")
    proj = DocPDF("Project Document", "Architecture & API Reference")
    build_project_document(proj)
    path2 = os.path.join(OUTPUT_DIR, "PROJECT_DOCUMENT.pdf")
    proj.output(path2)
    print(f"  \u2705 {path2} ({proj.pages_count} pages)")

    print("\n[OK] All PDFs generated successfully!")


if __name__ == "__main__":
    main()
