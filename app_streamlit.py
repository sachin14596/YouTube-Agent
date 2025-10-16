import os
import shutil
import subprocess
import streamlit as st

# ---------- PAGE SETUP ----------
st.set_page_config(page_title="🎬 Back-Catalog Uplift Agent", page_icon="🤖", layout="wide")
st.title("🤖 Back-Catalog Uplift Agent Dashboard")
st.caption("Autonomously analyzes and uplifts older YouTube videos.")

# ---------- SIDEBAR INPUTS ----------
st.sidebar.header("Channel Inputs")

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

run_btn = st.sidebar.button("🚀 Run Agent")

# ---------- PATHS ----------
base_outputs = "bc/outputs"
reports_dir = os.path.join(base_outputs, "reports")
artifacts_dir = os.path.join(base_outputs, "artifacts")
suggestions_dir = os.path.join(base_outputs, "suggestions")

# ---------- HELPERS ----------
def valid_channel(ch: str) -> bool:
    return bool(ch and len(ch.strip()) > 5)

def clean_outputs():
    """Remove old run folders before a new analysis."""
    for p in [reports_dir, artifacts_dir, suggestions_dir]:
        if os.path.exists(p):
            shutil.rmtree(p)
            print(f"🧹 Cleared old folder: {p}")
    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(artifacts_dir, exist_ok=True)
    os.makedirs(suggestions_dir, exist_ok=True)

def run_cmd(cmd_list):
    """Run subprocess and capture logs quietly."""
    process = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
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

    st.info(f"📡 Parameters: Channel={channel_id}, Age ≥ {age_days} days, Limit={limit}")
    st.markdown("---")

    # 🧹 Clean old run folders before processing
    st.warning("🧹 Cleaning old outputs from previous runs...")
    clean_outputs()

    with st.spinner("🤖 Agent analyzing your channel and optimizing hooks..."):
        # 1️⃣ Ingest step
        rc1, logs_ingest = run_cmd([
            "python", "app_cli.py", "ingest",
            "--channel", channel_id,
            "--limit", str(limit),
            "--age-days", str(age_days)
        ])

        # 2️⃣ Agentic LangGraph workflow
        if rc1 == 0:
            rc2, logs_agent = run_cmd(["python", "-m", "bc.graphs.uplift_graph"])
        else:
            st.error("❌ Ingest failed — please check console logs.")
            st.text_area("📄 Ingest Logs", logs_ingest, height=250)
            st.stop()

    st.success("✅ Agentic workflow completed successfully!")
    st.markdown("---")

    # ---------- DISPLAY REPORTS ----------
    if os.path.exists(reports_dir):
        files = [f for f in os.listdir(reports_dir) if f.endswith(".md")]
        if files:
            st.subheader("📊 Generated Uplift Reports")
            for f in files:
                report_path = os.path.join(reports_dir, f)
                with open(report_path, "r", encoding="utf-8") as fh:
                    content = fh.read()

                st.markdown(f"### 📽 {f.replace('.md','').replace('_',' ').title()}")
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
            st.warning("No reports found yet.")
    else:
        st.warning("Reports directory not found.")
