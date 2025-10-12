import os
import re
import json
from pathlib import Path

ARTIFACTS_PATH = "bc/outputs/artifacts/videos.json"
TRANSCRIPTS_DIR = "bc/outputs/transcripts"
ANALYSIS_DIR = "bc/outputs/analysis"
HOOKS_OUT = os.path.join(ANALYSIS_DIR, "hooks.json")

# --- tiny helper: safe read ---
def _read_txt(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

def _clean_text(t: str) -> str:
    # normalize whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t

def _first_chunk(text: str, target_chars: int = 900) -> str:
    """
    We don't have exact timestamps in the .txt, so approximate ~60s by characters.
    Whisper base at normal speech ~12–15 chars/sec ≈ 720–900 chars/min.
    """
    if not text:
        return ""
    text = _clean_text(text)
    return text[:target_chars]

def _score_hook(text: str) -> dict:
    """
    Very light, explainable heuristic to get us started.
    Returns {score: float, notes: [..], factors: {...}}
    """
    notes = []
    if not text:
        return {"score": 0.0, "notes": ["no transcript"], "factors": {}}

    # Signals
    curiosity_kw = [
        "what happens", "what if", "why", "how", "can you", "mystery",
        "surprising", "counterintuitive", "secret", "we discovered",
        "we tested", "we tried", "you won't believe", "unexpected"
    ]
    stakes_kw = [
        "danger", "risk", "cost", "fail", "impossible", "problem",
        "fix", "solution", "proof", "evidence", "real", "myth"
    ]
    specificity_hits = len(re.findall(r"\b\d+(\.\d+)?\b", text))  # numbers = specificity
    questions = text.count("?")
    uppercase_proper = len(re.findall(r"\b[A-Z][a-z]{3,}\b", text))  # rough proper nouns
    exclaim = text.count("!")
    # filler / weak openers
    weak_kw = ["in this video", "today we're", "welcome back", "hey guys", "like and subscribe"]
    weak_hits = sum(1 for w in weak_kw if w in text.lower())
    # curiosity/stakes density
    cur_hits = sum(1 for w in curiosity_kw if w in text.lower())
    stk_hits = sum(1 for w in stakes_kw if w in text.lower())
    # length / pacing proxy
    words = len(text.split())
    long_rambling = words > 220  # ~ >60s worth of dense talk for first chunk

    # normalize features to 0..1 rough scale
    def clip01(x, lo, hi):
        if hi == lo:
            return 0.0
        return max(0.0, min(1.0, (x - lo) / (hi - lo)))

    f_curiosity = clip01(cur_hits, 0, 4)
    f_stakes    = clip01(stk_hits, 0, 4)
    f_specific  = clip01(specificity_hits, 0, 6)
    f_questions = clip01(questions, 0, 3)
    f_proper    = clip01(uppercase_proper, 0, 10)
    f_exclaim   = clip01(exclaim, 0, 2)
    f_weakpen   = 1.0 - clip01(weak_hits, 0, 2)  # penalty inverted
    f_pacing    = 0.6 if long_rambling else 1.0  # very rough pacing penalty

    # weighted sum
    score = (
        0.22 * f_curiosity +
        0.20 * f_stakes +
        0.18 * f_specific +
        0.12 * f_questions +
        0.10 * f_proper +
        0.05 * f_exclaim +
        0.08 * f_weakpen
    ) * f_pacing

    # notes
    if cur_hits == 0: notes.append("add a curiosity hook (why/how/what if)")
    if stk_hits == 0: notes.append("add stakes or tension (risk/cost/benefit)")
    if specificity_hits == 0: notes.append("add specific facts or numbers early")
    if questions == 0: notes.append("ask a pointed question to create pull")
    if weak_hits > 0: notes.append("avoid generic openers (“in this video…”)")
    if long_rambling: notes.append("tighten pacing; front-load payoff within ~20s")

    return {
        "score": round(float(score), 3),
        "notes": notes,
        "factors": {
            "curiosity_hits": cur_hits,
            "stakes_hits": stk_hits,
            "specificity_hits": specificity_hits,
            "questions": questions,
            "proper_nouns": uppercase_proper,
            "exclaims": exclaim,
            "weak_openers": weak_hits,
            "words": words
        }
    }

def analyze_hooks(
    artifacts_path: str = ARTIFACTS_PATH,
    transcripts_dir: str = TRANSCRIPTS_DIR,
    out_path: str = HOOKS_OUT,
    target_chars: int = 900
):
    # ensure dirs
    Path(ANALYSIS_DIR).mkdir(parents=True, exist_ok=True)

    # load selected videos (Phase 2 output)
    with open(artifacts_path, "r", encoding="utf-8") as f:
        videos = json.load(f)

    results = []
    for v in videos:
        vid = v.get("video_id")
        title = v.get("title")
        tpath = Path(transcripts_dir) / f"{vid}.txt"

        text = _read_txt(tpath)
        chunk = _first_chunk(text, target_chars=target_chars)
        hook = _score_hook(chunk)

        results.append({
            "video_id": vid,
            "title": title,
            "hook_score": hook["score"],
            "hook_notes": hook["notes"],
            "hook_factors": hook["factors"],
            "first60_text": chunk if chunk else None
        })

    # sort by hook score (desc)
    results.sort(key=lambda x: x["hook_score"], reverse=True)

    # write file
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✅ Hook analysis saved → {out_path}")
    # print quick summary
    for r in results[:3]:
        print(f"- {r['title']} | hook_score={r['hook_score']} | notes: {', '.join(r['hook_notes'][:2]) or '—'}")
