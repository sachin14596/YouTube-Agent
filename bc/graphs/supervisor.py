# bc/graphs/supervisor.py
from pathlib import Path
import json
from typing import Dict, Any, List

from transformers import AutoTokenizer, AutoModelForCausalLM

# ---- Config ----
#MODEL_NAME = "google/gemma-3-270m"
#MODEL_NAME = "meta-llama/Llama-3.2-1B-Instruct"
MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

ALLOWED_NODES = ["analyze_hook", "rewrite", "titlethumb", "policy", "report"]

class Supervisor:
    def __init__(self, model_name: str = MODEL_NAME, device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._load_model()

    def _load_model(self):
        print(f"🧠 Loading Supervisor model: {self.model_name} ...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        if hasattr(self.model, "to"):
            self.model.to(self.device)
        print("✅ Supervisor model ready.")

    def _gen(self, prompt: str, max_new_tokens: int = 96) -> str:
        messages = [{"role": "user", "content": prompt}]
        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self.model.device)
        out = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        text = self.tokenizer.decode(out[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
        return text.strip()

    def decide_next(self, state: Dict[str, Any]) -> str:
        """
        Decide next node based on current per-video state.
        Hard rule: must run 'policy' before 'report'.
        """
        # --- Minimal heuristic fallback (if LLM output invalid) ---
        def fallback() -> str:
            # If no hook_score yet → analyze
            if state.get("hook_score") is None:
                return "analyze_hook"
            # If no rewrite yet and hook_score is weak → rewrite
            if not state.get("rewritten_script") and (state.get("hook_score", 0) < 0.4):
                return "rewrite"
            # If no title/thumbnail ideas → titlethumb
            if not state.get("titlethumb_ideas"):
                return "titlethumb"
            # If no policy check yet → policy
            if not state.get("policy_checked"):
                return "policy"
            # Otherwise → report
            return "report"

        # --- Enforce the single hard constraint ---
        if state.get("wants_report") and not state.get("policy_checked"):
            return "policy"

        # --- Build a compact prompt for the LLM supervisor ---
        score = state.get("hook_score")
        has_rw = bool(state.get("rewritten_script"))
        has_tt = bool(state.get("titlethumb_ideas"))
        policy_done = bool(state.get("policy_checked"))
        wants_report = bool(state.get("wants_report"))

        prompt = f"""
You are a routing controller for an agentic content-uplift system.
You must select exactly ONE next node from: {ALLOWED_NODES}.

State summary:
- hook_score: {score}
- rewritten_script: {has_rw}
- titlethumb_ideas: {has_tt}
- policy_checked: {policy_done}
- wants_report: {wants_report}

Hard rule: 'policy' must run before 'report'.
Guidance:
- If no hook_score → choose 'analyze_hook'.
- If hook_score < 0.4 and no rewritten_script → choose 'rewrite'.
- If no title/thumbnail ideas → choose 'titlethumb'.
- If report is requested or everything else exists but policy not done → choose 'policy'.
- Else choose 'report'.

Reply with ONLY the node name (no extra text).
"""
        try:
            out = self._gen(prompt)
            choice = out.strip().split()[0].lower()
            # normalize
            choice = choice.replace(".", "").replace("'", "")
            if choice in ALLOWED_NODES:
                return choice
            return fallback()
        except Exception:
            return fallback()


# ------ quick CLI test helper ------
def _demo():
    sup = Supervisor(MODEL_NAME)
    demo_states: List[Dict[str, Any]] = [
        {"hook_score": None, "rewritten_script": None, "titlethumb_ideas": None, "policy_checked": False, "wants_report": False},
        {"hook_score": 0.18, "rewritten_script": None, "titlethumb_ideas": None, "policy_checked": False, "wants_report": False},
        {"hook_score": 0.55, "rewritten_script": "some text", "titlethumb_ideas": None, "policy_checked": False, "wants_report": False},
        {"hook_score": 0.55, "rewritten_script": "some text", "titlethumb_ideas": "ideas", "policy_checked": False, "wants_report": True},
        {"hook_score": 0.55, "rewritten_script": "some text", "titlethumb_ideas": "ideas", "policy_checked": True, "wants_report": True},
    ]
    for i, st in enumerate(demo_states, 1):
        nxt = sup.decide_next(st)
        print(f"[{i}] next → {nxt} | state: {st}")

if __name__ == "__main__":
    _demo()
__all__ = ["Supervisor", "_demo"]
