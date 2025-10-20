import os
import shutil
import subprocess
import streamlit as st
from pathlib import Path
import time

# ---------- PAGE SETUP ----------
st.set_page_config(page_title="🎬 Back-Catalog Uplift Agent", page_icon="🤖", layout="wide")
st.title("🤖 Back-Catalog Uplift Agent Dashboard")
st.caption("Autonomously analyzes and uplifts older YouTube videos using AWS Bedrock + LangGraph.")

# ---------- PATHS ----------
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR
BASE_OUTPUTS = PROJECT_ROOT / "bc" / "outputs"
REPORTS_DIR = BASE_OUTPUTS / "reports"
ARTIFACTS_DIR = BASE_OUTPUTS / "artifacts"
SUGGESTIONS_DIR = BASE_OUTPUTS / "suggestions"

# ---------- SIDEBAR INPUTS ----------
st.sidebar.header("🎥 Channel Inputs")

channel_id = st.sidebar.text_input(
    "YouTube Channel ID or URL",
    value="UCHnyfMqiRRG1u-2MsSQLbXA",
    help="Paste a channel ID (e.g., UCHnyfMqiRRG1u-2MsSQLbXA) or full URL."
)

age_days = st.sidebar.slider(
    "📆 Minimum age of videos (days)",
    min_value=30, max_value=365, value=180, step=15,
    help="The agent will focus on videos older than this."
)

limit = st.sidebar.number_input(
    "🎞 Number of videos to process",
    min_value=1, max_value=10, value=2, step=1
)

run_btn = st.sidebar.button("🚀 Run Back-Catalog Uplift")

# ---------- HELPERS ----------
def valid_channel(ch: str) -> bool:
    return bool(ch and len(ch.strip()) > 5)

def clean_outputs():
    """Remove old run folders before a new analysis."""
    for p in [REPORTS_DIR, ARTIFACTS_DIR, SUGGESTIONS_DIR]:
        if p.exists():
            shutil.rmtree(p)
    for p in [REPORTS_DIR, ARTIFACTS_DIR, SUGGESTIONS_DIR]:
        p.mkdir(parents=True, exist_ok=True)

def run_cmd(cmd_list):
    """Run a command quietly but capture logs (UTF-8 safe + correct working dir)."""
    process = subprocess.Popen(
        cmd_list,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"}
    )
    logs = ""
    for line in process.stdout:
        logs += line
    process.wait()
    return process.returncode, logs

# ---------- MAIN ACTION ----------
if run_btn:
    if not valid_channel(channel_id):
        st.error("Please enter a valid Channel ID or URL.")
        st.stop()

    # Clean old outputs silently
    clean_outputs()

    st.markdown("### 🚀 Running Agent Workflow... please wait.")
    progress = st.progress(0)
    status = st.empty()

    # STEP 1️⃣ Ingest
    status.text("📡 Fetching and analyzing channel videos...")
    progress.progress(25)
    rc1, logs_ingest = run_cmd([
        "python", "app_cli.py", "ingest",
        "--channel", channel_id,
        "--limit", str(limit),
        "--age-days", str(age_days)
    ])

    # STEP 2️⃣ LangGraph Orchestration
    if rc1 == 0:
        status.text("🧠 Running LangGraph agentic workflow...")
        progress.progress(60)
        rc2, logs_agent = run_cmd(["python", "-m", "bc.graphs.uplift_graph"])
        progress.progress(90)
    else:
        st.error("❌ Ingest failed — please check logs below.")
        st.text_area("📄 Ingest Logs", logs_ingest, height=250)
        st.stop()

    progress.progress(100)
    status.text("✅ Agentic workflow completed successfully!")

    # Small pause to show 100% animation
    time.sleep(1)
    progress.empty()
    status.empty()
    st.markdown("---")

    # Optional collapsible logs (hidden by default)
    with st.expander("🧾 View Logs (Optional)"):
        st.text_area("Ingest Logs", logs_ingest, height=200)
        if rc1 == 0:
            st.text_area("LangGraph Logs", logs_agent, height=200)

    # ---------- DISPLAY REPORTS ----------
    if REPORTS_DIR.exists():
        files = [f for f in os.listdir(REPORTS_DIR) if f.endswith(".md")]
        if files:
            st.subheader("📊 Generated Uplift Reports")
            for f in files:
                report_path = REPORTS_DIR / f
                with open(report_path, "r", encoding="utf-8") as fh:
                    content = fh.read()

                st.markdown(f"### 🎬 {f.replace('.md','').replace('_',' ').title()}")
                st.markdown(content)
                st.download_button(
                    label=f"⬇ Download {f}",
                    data=content,
                    file_name=f,
                    mime="text/markdown",
                    key=f
                )
                st.divider()
        else:
            st.warning("⚠️ No reports found. Check the agent logs above.")
    else:
        st.error("❌ Reports directory not found.")
