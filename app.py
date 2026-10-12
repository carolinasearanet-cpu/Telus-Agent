import streamlit as st
from pypdf import PdfReader
from google import genai
from google.genai import types

st.set_page_config(page_title="TELUS Maps Evaluation Assistant", page_icon="🗺️", layout="wide")
st.title("TELUS Maps Search Evaluation Assistant")
st.caption("AI-assisted analysis only. This app does not log in to or submit anything to TryRating.")

with st.sidebar:
    st.header("AI configuration")
    try:
        secret_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        secret_key = ""
    manual_key = st.text_input(
        "Gemini API key (optional session fallback)",
        type="password",
        help="Prefer configuring GEMINI_API_KEY in Streamlit Settings > Secrets. Never put keys in GitHub."
    )
    api_key = secret_key or manual_key
    model_name = st.selectbox("Model", ["gemini-3.8-flash"], index=0)
    if secret_key:
        st.success("API key loaded from Streamlit Secrets.")
    elif manual_key:
        st.info("Using the key entered for this browser session.")
    else:
        st.warning("Add GEMINI_API_KEY in Streamlit Secrets to enable AI.")
    st.divider()
    st.header("Reference materials")
    guidelines = st.file_uploader("Official guidelines PDF", type=["pdf"], key="guidelines")
    examples = st.file_uploader("Examples PDF / TXT / CSV", type=["pdf", "txt", "csv"], key="examples")
    st.caption("Upload only materials you are permitted to share with an external AI service.")

def extract_file_text(upload, max_chars=350000):
    if upload is None:
        return ""
    try:
        if upload.name.lower().endswith(".pdf"):
            reader = PdfReader(upload)
            pages = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(f"[PDF page {i+1}]\n{text}")
            return "\n\n".join(pages)[:max_chars]
        return upload.getvalue().decode("utf-8", errors="replace")[:max_chars]
    except Exception as exc:
        return f"[Could not extract text from {upload.name}: {exc}]"

def call_gemini(prompt, images, key, model):
    client = genai.Client(api_key=key)
    parts = [types.Part.from_text(text=prompt)]
    for image_file in images or []:
        parts.append(types.Part.from_bytes(data=image_file.getvalue(), mime_type=image_file.type or "image/jpeg"))
        parts.append(types.Part.from_text(text=f"Screenshot filename: {image_file.name}"))
    response = client.models.generate_content(
        model=model,
        contents=[types.Content(role="user", parts=parts)],
        config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=6000),
    )
    return response.text or "The model returned no text. Try fewer or smaller screenshots."

guideline_text = extract_file_text(guidelines, 350000)
example_text = extract_file_text(examples, 50000)
tab_analyze, tab_research, tab_reference = st.tabs(["Analyze a task", "Research a result", "Search guidelines"])

with tab_analyze:
    st.subheader("Analyze task screenshots")
    st.write("Upload screenshots and, if permitted, the official guidelines and examples. The AI prepares a draft; you remain responsible for every decision.")
    query = st.text_input("Search query (if visible / known)", placeholder="Enter the query exactly as shown")
    locale = st.text_input("Locale / country", placeholder="e.g. en_US / United States")
    viewport = st.selectbox("Viewport status", ["Not sure", "Fresh", "Stale", "No viewport shown"])
    user_location = st.text_input("User location / map context", placeholder="Only information provided in the task")
    screenshots = st.file_uploader("Task screenshots", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True, key="task_screenshots")
    task_notes = st.text_area("Additional context", placeholder="Separate facts from assumptions.")
    critical_rule_notes = st.text_area("Critical guideline rules / corrections to check", placeholder="Optional: paste the exact rule or correction that applies to this task, including section number.")
    if screenshots:
        with st.expander(f"Preview {len(screenshots)} screenshot(s)"):
            cols = st.columns(min(3, len(screenshots)))
            for i, image in enumerate(screenshots):
                with cols[i % len(cols)]:
                    st.image(image, caption=image.name, use_container_width=True)
    if st.button("Analyze task with AI", type="primary", disabled=not (api_key and screenshots)):
        prompt = f"""You are an evidence-first assistant for TELUS Digital Maps Search Evaluation. You are not the final evaluator and must not submit anything.

TASK CONTEXT
Query: {query or '[not supplied]'}
Locale/country: {locale or '[not supplied]'}
Viewport status: {viewport}
User location/map context: {user_location or '[not supplied]'}
Extra notes: {task_notes or '[none]'}

CRITICAL RULE NOTES PROVIDED BY USER (check these against the official guideline text; do not silently ignore):
{critical_rule_notes or '[none supplied]'}

UPLOADED OFFICIAL GUIDELINES (primary authority):
{guideline_text or '[No guidelines PDF uploaded]'}

UPLOADED EXAMPLES (illustrative only; never override guidelines):
{example_text or '[No examples uploaded]'}

Instructions:
1. Transcribe visible query, result names, addresses, categories, map/pin clues and status labels. Mark unreadable information uncertain; never invent it.
2. Analyze each visible result separately. Separate screenshot facts, guideline evidence, example hints and inference.
3. Before rating, identify and compare all potentially applicable rules. Apply the most specific rule to the exact situation; do not default to a general rule when a specific exception applies.
4. If a user-provided critical rule conflicts with a proposed rating, explicitly investigate the conflict against the official guideline text. If the full relevant section is not available, say so and do not guess.
5. Suggest relevance, name/category, address and pin ratings only when supported. Explain uncertainty and list missing checks.
6. Mention issue checkboxes only if the uploaded guidelines support them.
7. Cite exact guideline section/page references only when present in the extracted text. Never invent references or claim a website/map was checked unless its content was supplied.
8. Draft a concise English comment only where justified; use placeholders for facts needing verification.
9. End with a checklist for human verification before manual submission.
Be cautious: uncertainty is better than a confident guess."""
        try:
            with st.spinner("Analyzing screenshots and uploaded reference materials…"):
                st.session_state["last_analysis"] = call_gemini(prompt, screenshots, api_key, model_name)
            st.success("Draft analysis generated. Verify all claims and references.")
        except Exception as exc:
            st.error(f"AI request failed: {exc}")
    if st.session_state.get("last_analysis"):
        st.markdown("### AI analysis (draft)")
        st.markdown(st.session_state["last_analysis"])
        st.download_button("Download analysis (.md)", st.session_state["last_analysis"], file_name="telus_task_analysis.md", mime="text/markdown")

with tab_research:
    st.subheader("Research a result using evidence you provide")
    st.info("This version does not automatically browse live websites. Paste the relevant source text you checked; the AI will not pretend to have opened a URL.")
    r_name = st.text_input("Result name", key="research_name")
    r_address = st.text_input("Address shown in task", key="research_address")
    r_category = st.text_input("Displayed category", key="research_category")
    r_query = st.text_input("Original query", key="research_query")
    r_url = st.text_input("Source URL(s) checked", key="research_urls")
    r_evidence = st.text_area("Paste relevant source text / evidence", key="research_evidence", height=160)
    r_pin = st.text_area("Map / pin observations", key="research_pin")
    if st.button("Evaluate this result", disabled=not (api_key and (r_name or r_address))):
        prompt = f"""Act as a cautious research assistant for TELUS Maps Search Evaluation. Do not submit ratings.
Official guideline text:
{guideline_text or '[No guidelines uploaded]'}
Examples:
{example_text or '[No examples uploaded]'}
Result name: {r_name or '[not supplied]'}
Address shown: {r_address or '[not supplied]'}
Category: {r_category or '[not supplied]'}
Original query: {r_query or '[not supplied]'}
URLs supplied by user: {r_url or '[none]'}
Source text actually supplied: {r_evidence or '[none]'}
Map/pin observations supplied by user: {r_pin or '[none]'}
Return an evidence table (claim, evidence, source, confidence), missing checks, tentative ratings only where justified, supported issue checkboxes, and a concise English comment. Cite exact guideline sections only if they appear above. Never claim you opened a URL or invent facts. If evidence is insufficient, say Cannot determine yet."""
        try:
            with st.spinner("Evaluating the supplied evidence…"):
                st.session_state["last_research"] = call_gemini(prompt, [], api_key, model_name)
            st.success("Draft evaluation generated.")
        except Exception as exc:
            st.error(f"AI request failed: {exc}")
    if st.session_state.get("last_research"):
        st.markdown(st.session_state["last_research"])
        st.download_button("Download result analysis (.md)", st.session_state["last_research"], file_name="telus_result_analysis.md", mime="text/markdown")

with tab_reference:
    st.subheader("Search uploaded guidelines")
    term = st.text_input("Keyword or section number", placeholder="e.g. 10.7.9")
    if term:
        if not guideline_text:
            st.warning("Upload the official guidelines PDF in the sidebar first.")
        else:
            lower, needle, positions, start = guideline_text.lower(), term.lower(), [], 0
            while len(positions) < 10:
                pos = lower.find(needle, start)
                if pos < 0:
                    break
                positions.append(pos)
                start = pos + len(needle)
            if not positions:
                st.info("No exact text match found. Try a shorter keyword.")
            for i, pos in enumerate(positions, 1):
                st.markdown(f"**Match {i}**")
                st.code(guideline_text[max(0, pos-450):min(len(guideline_text), pos+1000)], language=None)
    if example_text:
        with st.expander("Preview extracted examples"):
            st.text(example_text[:12000])

st.divider()
st.caption("Prototype v0.2 • AI drafts only. No automatic TryRating interaction or submission. AI can be wrong; verify each decision against project instructions and real evidence.")
