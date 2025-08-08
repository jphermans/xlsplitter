name: AI Improve XLSplitter

on:
  issues:
    types: [labeled, opened, edited]
  issue_comment:
    types: [created]

permissions:
  contents: write
  pull-requests: write
  issues: write

jobs:
  ai_improve:
    if: |
      (github.event_name == 'issues' && contains(github.event.issue.labels.*.name, 'ai:improve'))
      || (github.event_name == 'issue_comment' && startsWith(github.event.comment.body, '/ai-fix'))
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install requirements
        run: pip install requests

      - name: Run AI Improvement
        env:
          LLM_API_URL: ${{ secrets.LLM_API_URL }}
          LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
          LLM_MODEL: ${{ secrets.LLM_MODEL }}
        run: python .github/scripts/ai_xlsplitter_improve.py

      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v6
        with:
          branch: ai/llm-improve-${{ github.run_id }}
          title: "AI: Improvements from LLM"
          body: "Automated LLM-based improvements for Streamlit XLSplitter app."
          commit-message: "AI improvement"
