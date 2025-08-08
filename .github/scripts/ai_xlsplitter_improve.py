import os, json, subprocess, pathlib, re, sys, requests

# === config via GitHub Secrets ===
LLM_API_URL = os.getenv("LLM_API_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3")

if not LLM_API_URL or not LLM_API_KEY:
    print("Missing LLM_API_URL or LLM_API_KEY", file=sys.stderr)
    sys.exit(1)

# === haal issue info op ===
issue_path = os.getenv("GITHUB_EVENT_PATH", "")
issue_body = ""
issue_title = ""

if issue_path and pathlib.Path(issue_path).exists():
    with open(issue_path, "r") as f:
        event = json.load(f)
        issue_title = event.get("issue", {}).get("title", "")
        issue_body = event.get("issue", {}).get("body", "")
else:
    issue_title = "AI fix trigger"
    issue_body = os.getenv("COMMENT_BODY", "")

# === lees relevante bestanden ===
files = ["app.py", "requirements.txt", "README.md"]
blobs = []

for fname in files:
    path = pathlib.Path(fname)
    if path.exists():
        content = path.read_text(encoding="utf-8", errors="ignore")[:1500]
        blobs.append(f"### {fname}\n{content}")

# === prompt genereren ===
SYSTEM = "You are a senior Python/Streamlit engineer. Return ONLY a minimal unified diff. No explanations."
USER = f"""
Improve the following Streamlit app (XLSplitter):

- Add st.set_page_config if missing
- Use st.cache_data / st.cache_resource where applicable
- Improve file uploader UX
- Add simple type hints
- Do not add any heavy dependencies
- Add pytest file for core logic if applicable

Issue:
{issue_title}

Details:
{issue_body}

Files:
{chr(10).join(blobs)}

Respond with a single unified diff only. No explanations. No markdown code blocks.
"""

# === call LLM API ===
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {LLM_API_KEY}"
}

payload = {
    "model": LLM_MODEL,
    "messages": [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": USER}
    ],
    "temperature": 0.2
}

print("Calling LLM at:", LLM_API_URL)
response = requests.post(LLM_API_URL, headers=headers, json=payload)

try:
    patch = response.json()["choices"][0]["message"]["content"]
except Exception as e:
    print("Error parsing LLM response:", e)
    print("Raw response:", response.text)
    sys.exit(1)

# === schoon patch op (code fences verwijderen) ===
match = re.search(r"```diff(.*?)```", patch, re.S)
if match:
    patch = match.group(1).strip()
elif patch.startswith("```"):
    patch = patch.strip("```").strip()

# === schrijf patchbestand en pas toe ===
patch_path = pathlib.Path("ai.patch")
patch_path.write_text(patch, encoding="utf-8")
print("=== PATCH BEGIN ===\n", patch, "\n=== PATCH END ===")

result = subprocess.run(["git", "apply", "--reject", "--whitespace=nowarn", str(patch_path)])

if result.returncode != 0:
    print("⚠️ Patch kon niet worden toegepast. Suggestie wordt als diff-bestand opgeslagen.")
    pathlib.Path("AI_PATCH_SUGGESTIONS.diff").write_text(patch, encoding="utf-8")
    sys.exit(0)

# === commit & push patch ===
branch_name = f"ai/llm-fix-{os.getpid()}"

subprocess.run(["git", "checkout", "-b", branch_name], check=True)
subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", "AI: Apply LLM-generated fix"], check=True)
subprocess.run(["git", "push", "origin", "HEAD"], check=True)