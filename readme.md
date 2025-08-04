# XLSplitter

XLSplitter is a Python Streamlit application that allows users to split large Excel files into smaller batches while preserving:

- ✅ Cell formatting
- ✅ Data validation (e.g. dropdowns)
- ✅ Column widths
- ✅ Formulas

The app lets users specify the number of rows per batch (default is 1000) and downloads the resulting files as a ZIP archive.

---

## 🚀 Features

- Upload `.xlsx` files
- Split into batches of `N` rows per file
- Maintain cell styles, validation, and formatting
- Generate batch files: `Batch_1.xlsx`, `Batch_2.xlsx`, ...
- Download all in a single ZIP file
- Simple Streamlit web UI with progress tracking

---

## 📦 Build Windows EXE

This repository includes a GitHub Actions workflow to automatically build a Windows `.exe` file using PyInstaller.

To build manually:

1. Go to the **Actions** tab
2. Select the `Build Windows EXE` workflow
3. Click **"Run workflow"**
4. After completion, download the ZIP from the created Release

---

```markdown
## 🧰 Requirements

If running locally, it's recommended to create a virtual environment:

```bash
# Create and activate virtual environment (Windows)
python -m venv .venv
.venv\Scripts\activate

# Or on macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

```bash
pip install -r requirements.txt