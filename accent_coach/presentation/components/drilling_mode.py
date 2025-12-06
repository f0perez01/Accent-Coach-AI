"""
Drilling Mode Component

Interactive phoneme drilling for focused practice.
"""

import streamlit as st
from typing import List, Optional, Callable, Dict
from datetime import datetime


class DrillingMode:
    """
    Interactive drilling mode for pronunciation practice.

    Features:
    - Word-by-word practice with TTS
    - Repeat After Me flow
    - Progress tracking per word
    - Attempt counter
    - Success celebration
    """

    @staticmethod
    def render(
        drill_words: List[str],
        audio_service,
        on_record_callback: Callable[[bytes, str], Dict],
        tts_lang: str = "en"
    ):
        """
        Render interactive drilling mode.

        Args:
            drill_words: List of words to practice
            audio_service: AudioService instance for TTS
            on_record_callback: Function(audio_bytes, word) -> analysis_result
            tts_lang: Language code for TTS
        """
        if not drill_words:
            st.info("No words to practice. Complete an analysis first!")
            return

        # Initialize drilling session state
        if 'drilling_session' not in st.session_state:
            st.session_state.drilling_session = {
                'words': drill_words,
                'current_index': 0,
                'attempts': {},
                'completed': [],
                'started_at': datetime.now()
            }

        session = st.session_state.drilling_session

        # Update words list if changed
        if session['words'] != drill_words:
            session['words'] = drill_words
            session['current_index'] = 0
            session['attempts'] = {}
            session['completed'] = []

        # Check if all words completed
        if session['current_index'] >= len(drill_words):
            DrillingMode._render_completion(session)
            return

        current_word = drill_words[session['current_index']]

        # Initialize attempts for current word
        if current_word not in session['attempts']:
            session['attempts'][current_word] = []

        st.header("🎯 Drilling Mode")
        st.markdown("Practice each word until you master it!")

        # Progress bar
        progress = session['current_index'] / len(drill_words)
        st.progress(progress, text=f"Word {session['current_index'] + 1} of {len(drill_words)}")

        st.divider()

        # Current word section
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader(f"🔤 Practice: **{current_word}**")

            # Attempt counter
            attempt_count = len(session['attempts'][current_word])
            if attempt_count > 0:
                st.caption(f"📊 Attempts: {attempt_count}")

        with col2:
            # TTS buttons
            if st.button("🔊 Listen", key=f"listen_{current_word}", use_container_width=True):
                with st.spinner("Generating audio..."):
                    audio_bytes = audio_service.generate_tts(current_word, tts_lang, slow=False)
                    if audio_bytes:
                        st.audio(audio_bytes, format='audio/mp3')
                    else:
                        st.error("Failed to generate audio")

            if st.button("🐌 Listen Slow", key=f"listen_slow_{current_word}", use_container_width=True):
                with st.spinner("Generating slow audio..."):
                    audio_bytes = audio_service.generate_tts(current_word, tts_lang, slow=True)
                    if audio_bytes:
                        st.audio(audio_bytes, format='audio/mp3')
                    else:
                        st.error("Failed to generate slow audio")

        st.divider()

        # Recording section
        st.subheader("🎙️ Your Turn")

        recording_method = st.radio(
            "Recording method:",
            options=["Upload Audio", "Record with Microphone"],
            horizontal=True,
            key=f"drill_method_{current_word}"
        )

        audio_bytes = None

        if recording_method == "Upload Audio":
            uploaded = st.file_uploader(
                "Upload your recording",
                type=['wav', 'mp3', 'm4a'],
                key=f"upload_{current_word}_{attempt_count}"
            )
            if uploaded:
                audio_bytes = uploaded.read()
                st.success("✅ Audio loaded!")

        else:
            st.info("🎤 Click below to record")
            try:
                from audio_recorder_streamlit import audio_recorder
                audio_bytes = audio_recorder(
                    text="Click to record",
                    recording_color="#e74c3c",
                    neutral_color="#3498db",
                    icon_size="2x",
                    key=f"recorder_{current_word}_{attempt_count}"
                )
                if audio_bytes:
                    st.success("✅ Recording captured!")
            except ImportError:
                st.error("Audio recorder not available. Please upload a file.")

        # Analyze button
        can_analyze = audio_bytes is not None

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            if st.button(
                "🚀 Analyze Pronunciation",
                disabled=not can_analyze,
                type="primary",
                use_container_width=True,
                key=f"analyze_{current_word}_{attempt_count}"
            ):
                with st.spinner("🧠 Analyzing..."):
                    result = on_record_callback(audio_bytes, current_word)

                    # Store attempt
                    session['attempts'][current_word].append({
                        'timestamp': datetime.now(),
                        'result': result
                    })

                    # Display result
                    DrillingMode._render_attempt_result(result, current_word)

        with col2:
            if st.button("⏭️ Skip", use_container_width=True, key=f"skip_{current_word}"):
                session['current_index'] += 1
                st.rerun()

        with col3:
            if st.button("🔄 Reset", use_container_width=True, key=f"reset_{current_word}"):
                session['attempts'][current_word] = []
                st.rerun()

        # Show previous attempts
        if session['attempts'][current_word]:
            st.divider()
            st.subheader("📊 Your Attempts")

            for i, attempt in enumerate(reversed(session['attempts'][current_word][-3:]), 1):
                with st.expander(f"Attempt {len(session['attempts'][current_word]) - i + 1}"):
                    result = attempt['result']
                    analysis = result.get('analysis')

                    if analysis:
                        accuracy = analysis.metrics.word_accuracy
                        st.metric("Word Accuracy", f"{accuracy:.0%}")

                        if accuracy >= 90:
                            st.success("🎉 Excellent!")
                        elif accuracy >= 70:
                            st.info("👍 Good, keep practicing!")
                        else:
                            st.warning("💪 Try again!")

    @staticmethod
    def _render_attempt_result(result: Dict, target_word: str):
        """Render the result of a drilling attempt."""
        analysis = result.get('analysis')

        if not analysis:
            st.error("Analysis failed. Please try again.")
            return

        # Find the target word in analysis
        target_comparison = None
        for word_comp in analysis.per_word_comparison:
            if word_comp.word.lower() == target_word.lower():
                target_comparison = word_comp
                break

        if not target_comparison:
            st.warning(f"Could not find '{target_word}' in your recording. Did you say the word?")
            return

        # Display result
        accuracy = target_comparison.phoneme_accuracy

        if accuracy >= 90:
            st.success(f"🎉 **Excellent!** {accuracy:.0%} accuracy")
            st.balloons()

            # Mark as completed and move to next
            session = st.session_state.drilling_session
            if target_word not in session['completed']:
                session['completed'].append(target_word)
            session['current_index'] += 1

            if st.button("➡️ Next Word", type="primary", use_container_width=True):
                st.rerun()

        elif accuracy >= 70:
            st.info(f"👍 **Good!** {accuracy:.0%} accuracy - Keep practicing!")

            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"Expected: /{target_comparison.ref_phonemes}/")
            with col2:
                st.caption(f"You said: /{target_comparison.rec_phonemes}/")

            if st.button("🔁 Try Again", type="primary", use_container_width=True):
                st.rerun()

        else:
            st.warning(f"💪 **{accuracy:.0%}** - Let's improve this!")

            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"Expected: /{target_comparison.ref_phonemes}/")
            with col2:
                st.caption(f"You said: /{target_comparison.rec_phonemes}/")

            st.markdown("**Tip:** Listen to the slow version and focus on each sound.")

            if st.button("🔁 Try Again", type="primary", use_container_width=True):
                st.rerun()

    @staticmethod
    def _render_completion(session: Dict):
        """Render completion screen."""
        st.header("🎉 Drilling Complete!")
        st.success("Congratulations! You've practiced all the words!")

        # Statistics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Words Practiced", len(session['words']))

        with col2:
            total_attempts = sum(len(attempts) for attempts in session['attempts'].values())
            st.metric("Total Attempts", total_attempts)

        with col3:
            avg_attempts = total_attempts / len(session['words']) if session['words'] else 0
            st.metric("Avg per Word", f"{avg_attempts:.1f}")

        st.divider()

        # Word summary
        st.subheader("📊 Practice Summary")

        for word in session['words']:
            attempts = session['attempts'].get(word, [])
            attempt_count = len(attempts)

            with st.expander(f"🔤 {word} ({attempt_count} attempts)"):
                if attempts:
                    # Show best attempt
                    best_attempt = max(
                        attempts,
                        key=lambda a: a['result'].get('analysis').metrics.word_accuracy
                        if a['result'].get('analysis') else 0
                    )
                    best_accuracy = best_attempt['result'].get('analysis').metrics.word_accuracy
                    st.metric("Best Accuracy", f"{best_accuracy:.0%}")
                else:
                    st.caption("Skipped")

        st.divider()

        # Action buttons
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Practice Again", type="primary", use_container_width=True):
                st.session_state.drilling_session = {
                    'words': session['words'],
                    'current_index': 0,
                    'attempts': {},
                    'completed': [],
                    'started_at': datetime.now()
                }
                st.rerun()

        with col2:
            if st.button("✅ Done", use_container_width=True):
                # Clear drilling session
                if 'drilling_session' in st.session_state:
                    del st.session_state.drilling_session
                st.rerun()


def render_drilling_mode(
    drill_words: List[str],
    audio_service,
    on_record_callback: Callable[[bytes, str], Dict],
    tts_lang: str = "en"
):
    """
    Convenience function to render drilling mode.

    Args:
        drill_words: List of words to practice
        audio_service: AudioService instance for TTS
        on_record_callback: Function(audio_bytes, word) -> analysis_result
        tts_lang: Language code for TTS
    """
    return DrillingMode.render(drill_words, audio_service, on_record_callback, tts_lang)
