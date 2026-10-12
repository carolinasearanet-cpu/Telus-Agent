import streamlit as st
import pandas as pd
from pypdf import PdfReader

st.set_page_config(page_title="Maps Evaluation Assistant", page_icon="🗺️", layout="wide")
st.title("Maps Search Evaluation Assistant")
st.caption("Assistive tool for research, evidence tracking and draft ratings. It does not connect to or submit anything to TryRating.")

with st.sidebar:
    st.header("Reference materials")
    guidelines = st.file_uploader("Official guidelines PDF", type=["pdf"], key="guidelines")
    examples = st.file_uploader("Correct examples (PDF/TXT/CSV)", type=["pdf", "txt", "csv"], key="examples")
    st.info("Upload only materials you are permitted to use. Avoid credentials and confidential project data.")

def read_uploaded_text(file):
    if not file:
        return ""
    try:
        if file.name.lower().endswith(".pdf"):
            reader = PdfReader(file)
            return "\n\n".join(f"[Page {i+1}]\n{p.extract_text() or ''}" for i, p in enumerate(reader.pages))
        return file.getvalue().decode("utf-8", errors="replace")[:100000]
    except Exception as e:
        return f"Could not read file: {e}"

guideline_text = read_uploaded_text(guidelines)
example_text = read_uploaded_text(examples)

tab_task, tab_reference, tab_export = st.tabs(["Task workspace", "Guideline search", "Export"])

with tab_task:
    st.subheader("Task context")
    c1, c2 = st.columns(2)
    with c1:
        query = st.text_input("Search query", placeholder="e.g. lunch")
        locale = st.text_input("Locale / country", placeholder="e.g. en_US / United States")
        viewport = st.selectbox("Viewport status", ["Unknown", "Fresh", "Stale", "No viewport shown"])
    with c2:
        user_location = st.text_input("User location shown in task", placeholder="Coordinates or area, if provided")
        notes = st.text_area("Other task context", placeholder="Record visible context; distinguish facts from assumptions.")
        screenshots = st.file_uploader("Task screenshots", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
    if screenshots:
        cols = st.columns(min(3, len(screenshots)))
        for i, image in enumerate(screenshots):
            with cols[i % len(cols)]:
                st.image(image, caption=image.name, use_container_width=True)

    st.divider()
    st.subheader("Evaluate results")
    st.caption("Add each result separately. Treat ratings as drafts and confirm them against the official project instructions.")
    if "results" not in st.session_state:
        st.session_state.results = []
    with st.form("result_form", clear_on_submit=True):
        st.markdown("**New result**")
        name = st.text_input("Result name")
        address = st.text_input("Result address")
        category = st.text_input("Displayed category")
        result_url = st.text_input("Official or reliable source URL")
        source_note = st.text_area("What does this source confirm?", placeholder="e.g. official website confirms name/address; menu confirms lunch service.")
        a, b, c = st.columns(3)
        with a:
            navigational = st.selectbox("Navigational result?", ["No", "Yes"])
            relevance = st.selectbox("Relevance", ["Not rated", "Navigational", "Excellent", "Good", "Acceptable", "Bad"])
        with b:
            relevance_issue = st.multiselect("Relevance issue (if applicable)", ["User Intent Issue", "Distance/Prominence Issue"])
            name_accuracy = st.selectbox("Name accuracy", ["Not rated", "Correct", "Partially Correct", "Incorrect", "n/a"])
        with c:
            address_accuracy = st.selectbox("Address accuracy", ["Not rated", "Correct", "Incorrect", "Can't Verify", "n/a"])
            pin_accuracy = st.selectbox("Pin accuracy", ["Not rated", "Perfect", "Approximate", "Wrong", "Can't Verify", "n/a"])
        closed = st.selectbox("Business closed / does not exist?", ["Not determined", "No", "Yes"])
        rationale = st.text_area("Reasoning / uncertainty", placeholder="Why does this rating follow from the guidelines and evidence?")
        comment = st.text_area("Draft comment in English", placeholder="Concise explanation, guideline section(s), and source evidence.")
        submitted = st.form_submit_button("Add result")
        if submitted:
            if not name.strip() and not address.strip():
                st.error("Add at least a result name or address.")
            else:
                st.session_state.results.append({
                    "query": query, "locale_country": locale, "viewport": viewport,
                    "user_location": user_location, "task_notes": notes,
                    "name": name, "address": address, "category": category,
                    "source_url": result_url, "source_evidence": source_note,
                    "navigational": navigational, "relevance": relevance,
                    "relevance_issues": ", ".join(relevance_issue),
                    "name_accuracy": name_accuracy, "address_accuracy": address_accuracy,
                    "pin_accuracy": pin_accuracy, "closed_nonexistent": closed,
                    "reasoning_uncertainty": rationale, "comment_en": comment
                })
                st.success(f"Added: {name or address}")

    if st.session_state.results:
        st.subheader(f"Current results ({len(st.session_state.results)})")
        for idx, item in enumerate(st.session_state.results):
            with st.expander(f"{idx+1}. {item['name'] or item['address']} — {item['relevance']}"):
                st.write(f"**Address:** {item['address'] or 'Not entered'}")
                st.write(f"**Source:** {item['source_url'] or 'Not entered'}")
                st.write(f"**Evidence:** {item['source_evidence'] or 'Not entered'}")
                st.write(f"**Relevance issues:** {item['relevance_issues'] or 'None selected'}")
                st.write(f"**Comment:** {item['comment_en'] or 'Not drafted'}")
                if st.button("Remove result", key=f"remove_{idx}"):
                    st.session_state.results.pop(idx)
                    st.rerun()

with tab_reference:
    st.subheader("Search the uploaded guidelines")
    st.write("Search extracted text from the official PDF. Verify exact section references in the original PDF.")
    term = st.text_input("Keyword or section", placeholder="e.g. 10.7.9 Soft Categories")
    if term:
        if not guideline_text:
            st.warning("Upload the official guidelines PDF in the sidebar first.")
        else:
            lower, needle, positions, start = guideline_text.lower(), term.lower(), [], 0
            while len(positions) < 8:
                pos = lower.find(needle, start)
                if pos < 0: break
                positions.append(pos)
                start = pos + len(needle)
            if not positions:
                st.info("No exact text match found. Try a shorter keyword.")
            for i, pos in enumerate(positions, 1):
                st.markdown(f"**Match {i}**")
                st.code(guideline_text[max(0, pos-500):min(len(guideline_text), pos+1100)], language=None)
    if example_text:
        with st.expander("Preview extracted examples"):
            st.text(example_text[:12000])

with tab_export:
    st.subheader("Export draft evaluations")
    if not st.session_state.results:
        st.info("Add one or more results in Task workspace first.")
    else:
        df = pd.DataFrame(st.session_state.results)
        st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8-sig"), file_name="maps_evaluation_draft.csv", mime="text/csv")
        st.download_button("Download JSON", df.to_json(orient="records", indent=2, force_ascii=False).encode("utf-8"), file_name="maps_evaluation_draft.json", mime="application/json")

st.divider()
st.caption("Version 0.1 • No automated browsing, no account login, no TryRating interaction, and no AI-generated rating decisions yet. Ratings and comments are manually entered and must be verified.")
