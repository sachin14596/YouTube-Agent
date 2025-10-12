# bc/tools/shortlist_builder.py
import json, os

def build_shortlist(
    hooks_path="bc/outputs/analysis/hooks.json",
    output_path="bc/outputs/artifacts/_shortlist.json",
    threshold=0.4
):
    if not os.path.exists(hooks_path):
        print(f"❌ hooks.json not found: {hooks_path}")
        return

    with open(hooks_path, "r", encoding="utf-8") as f:
        hooks = json.load(f)

    # filter by low hook score
    shortlist = [h for h in hooks if h.get("hook_score", 0) < threshold]

    if not shortlist:
        print("⚠️ No weak-hook videos found (all above threshold).")
    else:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(shortlist, f, indent=2)
        print(f"✅ Shortlist saved → {output_path}")
        for v in shortlist:
            print(f"- {v['title']} | hook_score={v['hook_score']}")

if __name__ == "__main__":
    build_shortlist()
