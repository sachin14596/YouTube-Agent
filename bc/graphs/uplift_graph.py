"""
LangGraph DAG – Back-Catalog Uplift Agent
----------------------------------------
Agentic workflow connecting:
hook_rewrite → description_rewrite → title_thumb_scout → policy_guard → reporter
"""

from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from bc.tools.hook_rewrite import hook_rewrite
from bc.tools.description_rewrite import description_rewrite
from bc.tools.title_thumb_scout import title_thumb_scout
from bc.tools.policy_guard import policy_guard
from bc.tools.reporter import reporter


# === Define the State Schema ===
class VideoState(BaseModel):
    step: str = Field(default="start")
    channel_id: str | None = None
    limit: int | None = 2
    videos_processed: int = 0
    last_output: str | None = None
    safe: bool = True


# === Define Each Node ===
def node_hook_rewrite(state: VideoState):
    print("\n🧩 Step 1: Hook Rewrite")
    hook_rewrite()
    state.step = "rewrite_done"
    state.last_output = "hook_rewrites.json"
    return state


def node_description_rewrite(state: VideoState):
    print("\n🧩 Step 2: Description Rewrite")
    description_rewrite()
    state.step = "description_done"
    state.last_output = "description_rewrites.json"
    return state


def node_title_thumb(state: VideoState):
    print("\n🧩 Step 3: Title & Thumbnail Suggestions")
    title_thumb_scout()
    state.step = "titlethumb_done"
    state.last_output = "titlethumb.json"
    return state


def node_policy_guard(state: VideoState):
    print("\n🧩 Step 4: Policy Compliance Check")
    policy_guard()
    state.step = "policy_done"
    state.last_output = "policy_notes.json"
    return state


def node_reporter(state: VideoState):
    print("\n🧩 Step 5: Report Compilation")
    reporter()
    state.step = "report_done"
    state.last_output = "final_reports"
    return state


# === Build the Graph ===
def build_uplift_graph():
    graph = StateGraph(VideoState)

    # Add nodes
    graph.add_node("rewrite", node_hook_rewrite)
    graph.add_node("description", node_description_rewrite)
    graph.add_node("titlethumb", node_title_thumb)
    graph.add_node("policy", node_policy_guard)
    graph.add_node("report", node_reporter)

    # Connect edges (execution order)
    graph.add_edge("rewrite", "description")
    graph.add_edge("description", "titlethumb")
    graph.add_edge("titlethumb", "policy")
    graph.add_edge("policy", "report")
    graph.add_edge("report", END)

    # Entry point
    graph.set_entry_point("rewrite")

    return graph.compile()


# === Run Compiled Graph ===
def run_uplift_graph():
    print("🧠 Building and running Uplift LangGraph DAG...\n")
    compiled = build_uplift_graph()

    # initial input state
    initial_state = {"channel_id": "UCHnyfMqiRRG1u-2MsSQLbXA", "limit": 2}

    for event in compiled.stream(initial_state):
        if isinstance(event, tuple):
            state, node_name = event
            print(f"📍 Step: {node_name}")
            print(f"➡️  Last Output: {getattr(state, 'last_output', 'N/A')}\n")
        elif isinstance(event, dict):
            print(f"📍 Step: {event.get('step', 'unknown')}")
            print(f"➡️  Output: {event.get('last_output', 'N/A')}\n")
        else:
            print(f"📍 Event: {event}")

    print("✅ LangGraph workflow completed successfully!\n")


if __name__ == "__main__":
    run_uplift_graph()
