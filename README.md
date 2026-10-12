# Maps Search Evaluation Assistant — v0.1

A hosted-ready Streamlit app for organizing TELUS Maps Search Evaluation tasks. It is assistive only:
- Upload official guidelines and optional examples.
- Enter task context and upload screenshots for visual reference.
- Record draft ratings, source URLs, evidence and English comments.
- Search extracted text from the guideline PDF.
- Export draft evaluations to CSV or JSON.

It does **not** log in to TryRating, automate clicks, submit ratings, or make unattended decisions.

## Run locally
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy online with Streamlit Community Cloud
1. Create a GitHub repository. Use private visibility if appropriate.
2. Add `app.py`, `requirements.txt`, and `README.md`.
3. Connect the repository to Streamlit Community Cloud.
4. Set main file path to `app.py` and deploy.
5. Review hosting privacy and retention settings before uploading project materials.

## Limitations
- No search engine or maps API yet; you enter source URLs and evidence.
- Guideline search uses extracted PDF text and is not a substitute for checking the original PDF.
- No LLM is integrated yet. Choose a provider and check costs and project rules before sending task material.
- This is not an official TELUS tool and cannot guarantee rating correctness.
