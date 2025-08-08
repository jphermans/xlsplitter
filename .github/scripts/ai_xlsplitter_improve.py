import os, json, subprocess, pathlib, re, sys, requests

# === Secrets ===
LLM_API_URL = os.getenv("LLM_API_URL", "https://api.moonshot.ai/anthropic")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")

if not LLM_API_KEY:
    print("❌ Missing LLM_API_KEY", file=sys.stderr)
    sys.exit(1)

# === Issue context ophalen ===
issue_path = os.getenv("GITHUB_EVENT_PATH", "")
issue_body = os.getenv("COMMENT_BODY", "")
issue_title = "AI Fix Trigger"

if issue_path and pathlib.Path(issue_path).exists():
    with open(issue_path, "r") as f:
        event = json.load(f)
        issue = event.get("issue", {})
        issue_title = issue.get("title", issue_title)
        issue_body = issue.get("body", issue_body)

# === Relevante codebestanden ophalen ===
files = ["app.py", "requirements.txt", "README.md"]
blobs = []

for fname in files:
    p = pathlib.Path(fname)
    if p.exists():
        content = p.read_text(encoding="utf-8", errors="ignore")[:1500]
        blobs.append(f"### {fname}\n{content}")

# === Prompt samenstellen ===
system_prompt = "You are a senior Python and Streamlit engineer. Only return a minimal unified diff. No explanation or markdown. No extra commentary."
user_prompt = f"""
Please improve the following Streamlit app.

- Add st.set_page_config if missing
- Add caching with st.cache_data or st.cache_resource
- Add type hints
- Improve uploader UX and UI
- Only use built-in or existing dependencies
- Add simple pytest file if possible

Issue:
Title: {issue_title}
Body: {issue_body}

Relevant files:
{chr(10).join(blobs)}

Return only a unified diff (git-style). No explanation, no extra text, no code fences.
"""

# === API call to Anthropic ===
headers = {
    "x-api-key": LLM_API_KEY,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json"
}

payload = {
    "model": LLM_MODEL,
    "max_tokens": 2048,
    "system": system_prompt,
    "messages": [
        {"role": "user", "content": user_prompt}
    ]
}

print("🔁 Requesting Claude model from:", LLM_API_URL)
res = requests.post(LLM_API_URL, headers=headers, json=payload)

try:
    patch = res.json()["content"][0]["text"]
except Exception as e:
    print("❌ Failed to parse Claude response:", e)
    print("Full response:", res.text)
    sys.exit(1)

# === Clean patch from possible code blocks ===
patch = patch.strip()
if "```" in patch:
    patch = re.sub(r"```.*?```", "", patch, flags=re.S).strip()

# === Save and apply patch ===
pathlib.Path("ai.patch").write_text(patch)
print("📦 PATCH CONTENT START\n", patch, "\n📦 PATCH CONTENT END")

res = subprocess.run(["git", "apply", "--reject", "--whitespace=nowarn", "ai.patch"])
if res.returncode != 0:
    print("⚠️ Patch kon niet toegepast worden. Sla suggestie op als bestand.")
    pathlib.Path("AI_PATCH_SUGGESTIONS.diff").write_text(patch)
    sys.exit(0)

# === Commit & push branch ===
branch_name = f"ai/claude-fix-{os.getpid()}"
subprocess.run(["git", "checkout", "-b", branch_name], check=True)
subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", "AI: Apply Claude-generated fix"], check=True)
subprocess.run(["git", "push", "origin", "HEAD"], check=True)