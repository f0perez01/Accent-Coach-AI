import streamlit as st
from lexical.metrics import compute_metrics_for_text, load_basic_wordlists
from lexical.suggester import SuggestionEngine
from db.models import init_db, add_text_for_user, get_user_stats


def main():
    st.title("Vocabulary Coach — MVP")
    st.markdown("Upload or paste student text to analyze lexical variety and get contextual suggestions.")

    init_db()
    user = st.text_input("Student ID", value="student_1")

    st.header("Input")
    text = st.text_area("Paste student text here", height=200)
    uploaded = st.file_uploader("Or upload a .txt file", type=["txt"])
    if uploaded and not text:
        text = uploaded.read().decode("utf-8")

    if st.button("Analyze") and text.strip():
        add_text_for_user(user, text)
        wordlists = load_basic_wordlists()
        metrics = compute_metrics_for_text(text, wordlists=wordlists)

        st.sidebar.header("Metrics")
        for k, v in metrics.items():
            st.sidebar.write(f"**{k}**: {v}")

        st.header("Suggestions")
        sugg_engine = SuggestionEngine()
        suggestions = sugg_engine.suggest(text, top_k=15)

        for idx, s in enumerate(suggestions, 1):
            st.markdown(f"**{idx}. {s['word']}** — {s.get('reason','')}")
            st.write(s.get('example',''))
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Accept {s['word']}", key=f"accept-{idx}"):
                    st.success(f"Accepted {s['word']}")
            with col2:
                if st.button(f"Reject {s['word']}", key=f"reject-{idx}"):
                    st.error(f"Rejected {s['word']}")

        st.header("Student History")
        stats = get_user_stats(user)
        st.write(stats)


if __name__ == "__main__":
    main()
