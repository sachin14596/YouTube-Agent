# 🧠 Back-Catalog Uplift Agent  
> *An Agentic AI system that autonomously analyzes, rewrites, and optimizes YouTube back-catalog videos for better engagement.*

---

## 🚀 Overview
**Back-Catalog Uplift Agent** is a multi-phase, end-to-end AI workflow that:
- Ingests public YouTube channel data,
- Identifies older videos still showing engagement activity,
- Analyzes and rewrites the “hook zone” (first 60–90 seconds),
- Generates creative **titles + thumbnail** prompts,
- Runs policy-safety checks, and  
- Produces professional **Markdown + JSON** reports for each video.

Built using **LangGraph**, **Transformers**, and **Whisper**, the system behaves as an *agentic intelligence* rather than a rule-based script — capable of autonomous reasoning and decision-making across multiple tools.

---

## 🧩 System Architecture
LangGraph DAG:
[Ingest]
↓
[HookAnalyzer]
↓
[Rewrite] → [Title/Thumb]
↓
[PolicyGuard]
↓
[Reporter]


Each node passes structured state (`videos.json`, `hook_rewrites.json`, etc.) to the next.  
All nodes share a **single LLM instance** (`meta-llama/Llama-3.2-1B-Instruct`) through a centralized model loader, keeping memory use minimal and latency consistent.

---

## 🧠 Project Phases Summary

| Phase | Focus | Key Deliverables |
|:------|:------|:-----------------|
| **1️⃣ Ingest + Transcripts** | Fetch YouTube metadata and captions; Whisper fallback for missing captions. | `youtube_ingest.py`, `transcript_parse.py` |
| **2️⃣ Candidate Selection** | Identify older videos (> 180 days) still getting views/comments. | `candidate_selector.py`, metrics in `videos.json` |
| **3️⃣ Creative Optimization** | LLM rewrite of intros, generate 3 titles + thumbnail prompts, run policy guard. | `hook_rewrite.py`, `title_thumb_scout.py`, `policy_guard.py` |
| **4️⃣ Agentic LangGraph Integration** | Orchestrate all modules in a single DAG with shared LLM instance. | `uplift_graph.py`, `shared_model.py`, unified reports |

---


## 🧱 Key Technical Highlights

🧠 Agentic Workflow using LangGraph

🪶 Single Shared LLM (Llama-3.2-1B-Instruct) for all tool calls — avoids re-loading 2.5 GB model multiple times.

🎧 Whisper Fallback ensures transcripts even when captions are disabled.

🧮 Heuristic + LLM Hybrid Scoring combines view velocity and hook analysis.

🧾 Structured Reporting — every run produces Markdown & JSON summaries.

🧰 Modular Nodes easily extensible to new agents (e.g., TrendScout, CompetitorPulse).

## 🧭 Future Roadmap

| Upcoming Feature                        | Description                                                           |
| --------------------------------------- | --------------------------------------------------------------------- |
| 🧑‍🏫 **LLM-based Supervisor Node**     | Adaptive tool routing and confidence gating.                          |
| 🧩 **Trend Scout & Competitor Pulse**   | Fetch live topic demand and rival data.                               |
| 🛡️ **Dynamic Policy API**              | Integrate Perspective API / OpenAI Guardrails.                        |
| ☁️ **AWS Bedrock Deployment**           | Persist state in S3, metrics in CloudWatch.                           |
| 🖥️ **Streamlit Frontend (Next Phase)** | Interactive dashboard for reviewing and approving uplift suggestions. |



## Example Output
🧠 Loading shared model globally...
✍️ Rewriting: Atomic Theory
✅ Rewritten: Atomic Theory
🎨 Generated Titles + Thumbnails
🛡️ Policy Safe
📝 Markdown + JSON reports saved → bc/outputs/reports/
✅ LangGraph workflow completed successfully!

## Steps
python app_cli.py ingest --channel UCHnyfMqiRRG1u-2MsSQLbXA --limit 2
python -c "from bc.tools.title_thumb_scout import title_thumb_scout; title_thumb_scout()"
python -c "from bc.tools.policy_guard import policy_guard; policy_guard()"
python -c "from bc.tools.reporter import reporter; reporter()"
python -m bc.graphs.uplift_graph

