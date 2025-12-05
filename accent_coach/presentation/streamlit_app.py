"""
Streamlit Main Application

Thin UI orchestrator following Domain-Driven Design.
Delegates to domain services with dependency injection.

Refactored from monolithic app.py (1,295 lines → ~400 lines target)
"""

import os
from datetime import datetime
import streamlit as st

# Domain Services
from accent_coach.domain.audio.service import AudioService
from accent_coach.domain.transcription.service import TranscriptionService
from accent_coach.domain.phonetic.service import PhoneticAnalysisService
from accent_coach.domain.pronunciation.service import PronunciationPracticeService
from accent_coach.domain.conversation.service import ConversationService
from accent_coach.domain.conversation.models import ConversationConfig, ConversationMode
from accent_coach.domain.writing.service import WritingService
from accent_coach.domain.writing.models import QuestionCategory, QuestionDifficulty
from accent_coach.domain.language_query.service import LanguageQueryService
from accent_coach.domain.language_query.models import QueryConfig, QueryCategory

# Infrastructure Services
from accent_coach.infrastructure.llm.groq_provider import GroqLLMService
from accent_coach.infrastructure.persistence.in_memory_repositories import (
    InMemoryPronunciationRepository,
    InMemoryConversationRepository,
    InMemoryWritingRepository
)

# Legacy components (keep for now)
from auth_manager import AuthManager
from session_manager import SessionManager
from activity_logger import ActivityLogger


def init_session_state():
    """Initialize session state variables."""
    if 'config' not in st.session_state:
        st.session_state.config = {
            'model_name': 'facebook/wav2vec2-base-960h',
            'use_g2p': True,
            'use_llm': True,
            'lang': 'en-us',
            'enable_enhancement': True,
            'enable_vad': True,
            'enable_denoising': True,
            'show_quality_metrics': False,
        }

    if 'language_query_history' not in st.session_state:
        st.session_state.language_query_history = []

    if 'user' not in st.session_state:
        st.session_state.user = None


def initialize_services():
    """
    Initialize all domain services with dependency injection.

    Returns:
        dict: Dictionary containing all initialized services
    """
    # Get API keys
    try:
        groq_api_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY"))
    except:
        groq_api_key = os.environ.get("GROQ_API_KEY")

    # Initialize infrastructure services
    llm_service = GroqLLMService(api_key=groq_api_key) if groq_api_key else None

    # Initialize ASR Manager for transcription
    from accent_coach.domain.transcription.asr_manager import ASRModelManager
    
    MODEL_OPTIONS = {
        "Wav2Vec2 Base (Fast, Cloud-Friendly)": "facebook/wav2vec2-base-960h",
        "Wav2Vec2 Large (Better Accuracy, Needs More RAM)": "facebook/wav2vec2-large-960h",
        "Wav2Vec2 XLSR (Phonetic)": "mrrubino/wav2vec2-large-xlsr-53-l2-arctic-phoneme",
    }
    DEFAULT_MODEL = "facebook/wav2vec2-base-960h"
    
    asr_manager = ASRModelManager(DEFAULT_MODEL, MODEL_OPTIONS)

    # Initialize repositories (using in-memory for now)
    pronunciation_repo = InMemoryPronunciationRepository()
    conversation_repo = InMemoryConversationRepository()
    writing_repo = InMemoryWritingRepository()

    # Initialize domain services with dependency injection
    audio_service = AudioService()
    transcription_service = TranscriptionService(asr_manager=asr_manager)
    phonetic_service = PhoneticAnalysisService()

    pronunciation_service = PronunciationPracticeService(
        audio_service=audio_service,
        transcription_service=transcription_service,
        phonetic_service=phonetic_service,
        llm_service=llm_service,
        repository=pronunciation_repo
    )

    conversation_service = ConversationService(
        audio_service=audio_service,
        transcription_service=transcription_service,
        llm_service=llm_service,
        repository=conversation_repo
    )

    writing_service = WritingService(
        llm_service=llm_service
    )

    language_query_service = LanguageQueryService(
        llm_service=llm_service
    )

    # Legacy components
    auth_manager = AuthManager(st.secrets if hasattr(st, 'secrets') else None)

    return {
        # Domain services
        'audio': audio_service,
        'transcription': transcription_service,
        'phonetic': phonetic_service,
        'pronunciation': pronunciation_service,
        'conversation': conversation_service,
        'writing': writing_service,
        'language_query': language_query_service,
        # Infrastructure
        'llm': llm_service,
        'auth': auth_manager,
        # Repositories
        'repos': {
            'pronunciation': pronunciation_repo,
            'conversation': conversation_repo,
            'writing': writing_repo,
        }
    }


def render_pronunciation_practice_tab(user: dict, pronunciation_service: PronunciationPracticeService):
    """
    Render Pronunciation Practice tab (BC4).

    Audio-based pronunciation practice with phonetic analysis.
    """
    st.header("🎤 Pronunciation Practice")
    st.markdown("Record yourself speaking and get instant feedback on pronunciation, phonetics, and word accuracy")

    # Initialize session state
    if 'pronunciation_result' not in st.session_state:
        st.session_state.pronunciation_result = None
    if 'pronunciation_history' not in st.session_state:
        st.session_state.pronunciation_history = []

    # Section 1: Reference Text Input
    st.subheader("📝 Choose Text to Practice")

    # Initialize PracticeTextManager
    from accent_coach.domain.pronunciation import PracticeTextManager
    practice_manager = PracticeTextManager()

    # Category selection
    col1, col2 = st.columns([2, 1])
    with col1:
        categories = practice_manager.get_categories()
        selected_category = st.selectbox(
            "Select a category:",
            options=categories,
            help="Choose a practice category suitable for your level"
        )
    
    with col2:
        # Category info
        cat_info = practice_manager.get_category_info(selected_category)
        if cat_info:
            st.metric("Texts Available", cat_info['count'])
            st.caption(cat_info['description'])

    # Text selection
    texts_in_category = practice_manager.get_texts_for_category(selected_category)
    text_options = [text.text for text in texts_in_category] + ["Custom text..."]
    
    preset_choice = st.selectbox(
        "Select a text or enter custom:",
        options=text_options,
        help="Choose a preset text or select 'Custom text...' to write your own"
    )

    # Clear suggested drill words when text changes
    if 'last_reference_text' not in st.session_state:
        st.session_state.last_reference_text = None
    
    if preset_choice == "Custom text...":
        reference_text = st.text_input(
            "Enter your text:",
            placeholder="Type the text you want to practice...",
            max_chars=200
        )
    else:
        reference_text = preset_choice
        # Find the selected text object for metadata
        selected_text_obj = next((t for t in texts_in_category if t.text == preset_choice), None)
        if selected_text_obj:
            st.info(f"**Practice text**: {reference_text}")
            st.caption(f"ℹ️ Focus: {selected_text_obj.focus} | Level: {selected_text_obj.difficulty}")
        else:
            st.info(f"**Practice text**: {reference_text}")
    
    # Track text changes for clearing drill words
    if st.session_state.last_reference_text != reference_text:
        st.session_state.last_reference_text = reference_text
        if 'suggested_drill_words' in st.session_state:
            st.session_state.suggested_drill_words = []

    st.divider()

    # Section 2: Audio Recording
    st.subheader("🎙️ Record Your Pronunciation")

    # Two input methods: File upload OR audio recorder
    recording_method = st.radio(
        "Choose recording method:",
        options=["Upload Audio File", "Record with Microphone"],
        horizontal=True
    )

    audio_bytes = None

    if recording_method == "Upload Audio File":
        uploaded_file = st.file_uploader(
            "Upload your audio file (WAV, MP3, M4A)",
            type=['wav', 'mp3', 'm4a'],
            help="Record audio on your device and upload it here"
        )

        if uploaded_file:
            audio_bytes = uploaded_file.read()
            st.audio(audio_bytes, format='audio/wav')
            st.success("✅ Audio file loaded!")

    else:  # Record with Microphone
        st.info("🎤 Browser-based audio recording")

        try:
            from audio_recorder_streamlit import audio_recorder

            audio_bytes = audio_recorder(
                text="Click to record",
                recording_color="#e74c3c",
                neutral_color="#3498db",
                icon_name="microphone",
                icon_size="3x",
            )

            if audio_bytes:
                st.audio(audio_bytes, format='audio/wav')
                st.success("✅ Recording complete!")

        except ImportError:
            st.warning("⚠️ Audio recorder not available. Please use 'Upload Audio File' method.")
            st.info("To enable microphone recording, install: pip install audio-recorder-streamlit")

    st.divider()

    # Section 3: Configuration
    with st.expander("⚙️ Advanced Settings", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            use_llm = st.checkbox(
                "Enable LLM Feedback",
                value=True,
                help="Get AI-powered personalized feedback"
            )

            normalize_audio = st.checkbox(
                "Normalize Audio",
                value=True,
                help="Adjust volume levels automatically"
            )

        with col2:
            use_g2p = st.checkbox(
                "Use Phoneme Analysis",
                value=True,
                help="Enable grapheme-to-phoneme conversion"
            )

    # Section 4: Analyze Button
    analyze_button = st.button("🔍 Analyze Pronunciation", type="primary", use_container_width=True)

    if analyze_button and audio_bytes and reference_text.strip():
        with st.spinner("🔄 Analyzing your pronunciation..."):
            try:
                from accent_coach.domain.pronunciation.models import PracticeConfig

                config = PracticeConfig(
                    use_llm_feedback=use_llm and st.session_state.llm_available,
                    normalize_audio=normalize_audio,
                    use_g2p=use_g2p,
                    sample_rate=16000,
                    asr_model=st.session_state.config['model_name'],
                    language=st.session_state.config['lang']
                )

                result = pronunciation_service.analyze_recording(
                    audio_bytes=audio_bytes,
                    reference_text=reference_text,
                    user_id=user.get('localId', 'demo'),
                    config=config
                )

                st.session_state.pronunciation_result = result
                st.session_state.pronunciation_history.append({
                    'reference_text': reference_text,
                    'result': result,
                    'timestamp': datetime.now()
                })

                st.success("✅ Analysis complete!")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                import traceback
                with st.expander("🔍 Error Details"):
                    st.code(traceback.format_exc())

    elif analyze_button:
        if not reference_text.strip():
            st.warning("⚠️ Please enter or select text to practice")
        if not audio_bytes:
            st.warning("⚠️ Please record or upload audio first")

    # Section 5: Results Display
    if st.session_state.pronunciation_result:
        result = st.session_state.pronunciation_result
        analysis = result.analysis

        st.divider()
        st.header("📊 Analysis Results")

        # Metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Word Accuracy",
                value=f"{analysis.metrics.word_accuracy:.1%}",
                help="Percentage of words pronounced correctly"
            )

        with col2:
            st.metric(
                label="Phoneme Accuracy",
                value=f"{analysis.metrics.phoneme_accuracy:.1%}",
                help="Percentage of phonemes pronounced correctly"
            )

        with col3:
            st.metric(
                label="Correct Words",
                value=f"{analysis.metrics.correct_words}/{analysis.metrics.total_words}",
                help="Number of correctly pronounced words"
            )

        with col4:
            error_rate = analysis.metrics.phoneme_error_rate
            st.metric(
                label="Error Rate",
                value=f"{error_rate:.1%}",
                delta=f"-{error_rate:.1%}" if error_rate < 0.2 else None,
                delta_color="inverse",
                help="Phoneme Error Rate (PER)"
            )

        # What you said
        st.subheader("💬 What You Said")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Transcription:**")
            st.info(result.raw_decoded)

        with col2:
            st.markdown("**Phonemes (IPA):**")
            st.code(result.recorded_phoneme_str, language=None)

        # Word-by-word comparison
        if analysis.per_word_comparison:
            st.subheader("🔍 Word-by-Word Analysis")

            for word_comp in analysis.per_word_comparison:
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    icon = "✅" if word_comp.match else "❌"
                    st.markdown(f"{icon} **{word_comp.word}**")

                with col2:
                    st.caption(f"Expected: /{word_comp.ref_phonemes}/")
                    st.caption(f"Your pronunciation: /{word_comp.rec_phonemes}/")

                with col3:
                    accuracy_color = "🟢" if word_comp.phoneme_accuracy > 0.8 else "🟡" if word_comp.phoneme_accuracy > 0.5 else "🔴"
                    st.caption(f"{accuracy_color} {word_comp.phoneme_accuracy:.0%}")

                if word_comp.errors:
                    with st.expander("View errors"):
                        for error in word_comp.errors:
                            st.markdown(f"- {error}")

        # IPA Breakdown (educational)
        if analysis.ipa_breakdown:
            st.subheader("📚 IPA Breakdown (Learn the Sounds)")

            for ipa_item in analysis.ipa_breakdown[:5]:  # Show first 5
                with st.expander(f"🔤 {ipa_item.word} → /{ipa_item.ipa}/"):
                    st.markdown(f"**Hint:** {ipa_item.hint}")

                    if ipa_item.audio:
                        st.audio(ipa_item.audio, format='audio/mp3')

        # Suggested drill words
        if analysis.suggested_drill_words:
            st.subheader("🎯 Practice These Words")
            st.markdown("Focus on these words to improve:")

            drill_cols = st.columns(min(len(analysis.suggested_drill_words), 4))
            for i, word in enumerate(analysis.suggested_drill_words[:4]):
                with drill_cols[i]:
                    st.info(word)

        # LLM Feedback
        if result.llm_feedback:
            st.divider()
            st.subheader("🤖 AI Tutor Feedback")
            st.markdown(result.llm_feedback)

        # Clear button
        if st.button("🗑️ Clear Results", use_container_width=True):
            st.session_state.pronunciation_result = None
            st.rerun()


def render_language_query_tab(user: dict, language_query_service: LanguageQueryService):
    """
    Render Language Assistant tab (BC8).

    Simplest tab - good starting point for refactoring.
    """
    st.header("💬 Language Assistant")
    st.markdown("Ask me about **idioms**, **phrasal verbs**, **expressions**, or any English language questions!")

    # Show chat history
    st.subheader("Chat History")

    if st.session_state.language_query_history:
        for i, entry in enumerate(reversed(st.session_state.language_query_history)):
            with st.expander(f"💬 {entry['user_query'][:50]}..." if len(entry['user_query']) > 50 else f"💬 {entry['user_query']}", expanded=(i == 0)):
                st.markdown(f"**You asked:** {entry['user_query']}")

                # Show category badge
                category = entry.get('category', 'expression')
                category_colors = {
                    'idiom': '🎭',
                    'phrasal_verb': '🔄',
                    'expression': '💬',
                    'slang': '😎',
                    'grammar': '📚',
                    'vocabulary': '📖',
                    'error': '❌'
                }
                emoji = category_colors.get(category, '💬')
                st.caption(f"{emoji} Category: **{category.replace('_', ' ').title()}**")

                st.markdown("---")
                st.markdown(f"**Answer:**\n\n{entry['llm_response']}")
    else:
        st.info("No queries yet. Ask your first question below!")

    st.divider()

    # Query input
    st.subheader("Ask a Question")

    user_query = st.text_area(
        "Your question:",
        placeholder="e.g., Is 'touch base' commonly used in American English?",
        height=100,
        key="language_query_input"
    )

    col1, col2 = st.columns([1, 5])

    with col1:
        submit_query = st.button("🚀 Ask", type="primary", use_container_width=True)

    with col2:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.language_query_history = []
            st.rerun()

    # Process query
    if submit_query and user_query.strip():
        with st.spinner("Thinking..."):
            try:
                # Build conversation history for context
                conversation_history = [
                    {
                        'user_query': entry['user_query'],
                        'llm_response': entry['llm_response']
                    }
                    for entry in st.session_state.language_query_history[-3:]  # Last 3 for context
                ]

                # Call new service
                config = QueryConfig()
                result = language_query_service.process_query(
                    user_query=user_query,
                    conversation_history=conversation_history,
                    config=config
                )

                # Add to history
                st.session_state.language_query_history.append({
                    'user_query': result.user_query,
                    'llm_response': result.llm_response,
                    'category': result.category.value,
                    'timestamp': result.timestamp
                })

                st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


def render_conversation_tutor_tab(user: dict, conversation_service: ConversationService):
    """
    Render Conversation Tutor tab (BC5).

    Multi-turn conversation practice with AI feedback.
    """
    st.header("🗣️ Conversation Practice Tutor")
    st.markdown("Practice natural English conversation with AI-powered feedback and guidance")

    # Initialize session state
    if 'conversation_session' not in st.session_state:
        st.session_state.conversation_session = None
    if 'conversation_turns' not in st.session_state:
        st.session_state.conversation_turns = []

    # Section 1: Session Configuration
    st.subheader("⚙️ Session Settings")

    col1, col2, col3 = st.columns(3)

    with col1:
        mode = st.selectbox(
            "Mode",
            options=[ConversationMode.PRACTICE.value, ConversationMode.EXAM.value],
            format_func=lambda x: x.title(),
            help="Practice: Get corrections. Exam: Test your skills."
        )

    with col2:
        topic = st.selectbox(
            "Topic",
            options=["Technology", "Travel", "Work", "Hobbies", "Education", "Current Events"],
            help="Choose a conversation topic"
        )

    with col3:
        proficiency = st.selectbox(
            "Your Level",
            options=["beginner", "intermediate", "advanced"],
            index=1
        )

    # Start new session button
    if st.button("🎬 Start New Session", type="primary"):
        try:
            config = ConversationConfig(
                mode=ConversationMode(mode),
                topic=topic,
                user_level=proficiency
            )

            session = conversation_service.create_session(
                user_id=user.get('localId', 'demo'),
                config=config
            )

            st.session_state.conversation_session = session
            st.session_state.conversation_turns = []

            st.success(f"✅ New {mode} session started on topic: **{topic}**")
            st.rerun()

        except Exception as e:
            st.error(f"Error creating session: {str(e)}")

    # Show starter prompt if session exists
    if st.session_state.conversation_session:
        session = st.session_state.conversation_session

        st.divider()
        st.subheader("💭 Conversation")

        # Show starter (only if no turns yet)
        if not st.session_state.conversation_turns:
            from accent_coach.domain.conversation.starters import ConversationStarters

            starter = ConversationStarters.get_starter(
                topic=session.topic,
                level=session.level or "B1-B2"
            )
            st.info(f"**AI Tutor**: {starter}")

        # Display conversation history
        for turn in st.session_state.conversation_turns:
            # User message
            with st.chat_message("user"):
                st.markdown(turn['user_transcript'])

            # AI response
            with st.chat_message("assistant"):
                # Correction (if any)
                if turn.get('correction'):
                    st.warning(f"✏️ **Correction**: {turn['correction']}")

                # Follow-up
                if turn.get('follow_up'):
                    st.markdown(turn['follow_up'])

        st.divider()

        # User input for next turn
        user_transcript = st.text_area(
            "Your response:",
            height=100,
            placeholder="Type what you would say in this conversation...",
            key=f"conv_input_{len(st.session_state.conversation_turns)}"
        )

        col1, col2 = st.columns([1, 5])

        with col1:
            submit_turn = st.button("💬 Send", type="primary", use_container_width=True)

        with col2:
            if st.button("🔄 End Session", use_container_width=True):
                # Close session
                try:
                    conversation_service.close_session(session.session_id)
                    st.session_state.conversation_session = None
                    st.session_state.conversation_turns = []
                    st.success("Session ended successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error closing session: {str(e)}")

        # Process turn
        if submit_turn and user_transcript.strip():
            with st.spinner("Tutor is thinking..."):
                try:
                    turn_result = conversation_service.process_turn(
                        session_id=session.session_id,
                        user_transcript=user_transcript,
                        user_id=user.get('localId', 'demo')
                    )

                    # Add turn to history
                    st.session_state.conversation_turns.append({
                        'user_transcript': user_transcript,
                        'correction': turn_result.correction,
                        'follow_up': turn_result.follow_up
                    })

                    st.rerun()

                except Exception as e:
                    st.error(f"Error processing turn: {str(e)}")

        # Show session stats
        if st.session_state.conversation_turns:
            st.divider()
            st.caption(f"📊 Turns: {len(st.session_state.conversation_turns)} | Mode: {session.mode.value.title()} | Topic: {session.topic}")

    else:
        st.info("👆 Click 'Start New Session' to begin practicing!")


def render_writing_coach_tab(user: dict, writing_service: WritingService):
    """
    Render Writing Coach tab (BC7).

    Helps users practice writing answers to interview questions.
    """
    st.header("✍️ Interview Writing Coach")
    st.markdown("Practice writing answers to interview questions and receive AI-powered feedback")

    # Initialize session state for writing
    if 'selected_question' not in st.session_state:
        st.session_state.selected_question = None
    if 'writing_text' not in st.session_state:
        st.session_state.writing_text = ""
    if 'evaluation_result' not in st.session_state:
        st.session_state.evaluation_result = None

    # Section 1: Question Selection
    st.subheader("🎯 Select Interview Questions")

    col1, col2 = st.columns(2)

    with col1:
        category = st.selectbox(
            "Question Category",
            options=[cat.value for cat in QuestionCategory],
            format_func=lambda x: x.replace('_', ' ').title()
        )

    with col2:
        difficulty = st.selectbox(
            "Difficulty Level",
            options=[diff.value for diff in QuestionDifficulty],
            format_func=lambda x: x.title()
        )

    # Get questions for selected category/difficulty
    try:
        question = writing_service.get_question_by_category(
            category=QuestionCategory(category),
            difficulty=QuestionDifficulty(difficulty)
        )

        if question:
            st.session_state.selected_question = question

            # Display question
            st.info(f"**Question**: {question.text}")

            # Show XP value
            xp_value = question.get_xp_value()
            xp_colors = {10: "🔵", 20: "🟢", 40: "🟡"}
            xp_emoji = xp_colors.get(xp_value, "⭐")
            st.caption(f"{xp_emoji} **XP Value**: {xp_value} points")

    except Exception as e:
        st.error(f"Error loading question: {str(e)}")

    st.divider()

    # Section 2: Writing Area
    st.subheader("✍️ Draft Your Answer")

    writing_text = st.text_area(
        "Your answer:",
        value=st.session_state.writing_text,
        height=200,
        placeholder="Write your answer here. Aim for 3-5 sentences with good structure and vocabulary.",
        key="writing_input"
    )

    st.session_state.writing_text = writing_text

    # Word count
    word_count = len(writing_text.split()) if writing_text.strip() else 0
    st.caption(f"📝 Word count: {word_count}")

    col1, col2, col3 = st.columns([1, 1, 3])

    with col1:
        evaluate_button = st.button("🚀 Evaluate", type="primary", use_container_width=True)

    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.writing_text = ""
            st.session_state.evaluation_result = None
            st.rerun()

    # Section 3: Evaluation & Feedback
    if evaluate_button and writing_text.strip():
        with st.spinner("Analyzing your writing..."):
            try:
                from accent_coach.domain.writing.models import WritingConfig

                config = WritingConfig()
                evaluation = writing_service.evaluate_writing(
                    text=writing_text,
                    config=config
                )

                st.session_state.evaluation_result = evaluation

            except Exception as e:
                st.error(f"❌ Error during evaluation: {str(e)}")

    # Display evaluation results
    if st.session_state.evaluation_result:
        evaluation = st.session_state.evaluation_result

        st.divider()
        st.subheader("📊 Evaluation Results")

        # Metrics display
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="CEFR Level",
                value=evaluation.metrics.cefr_level,
                help="Common European Framework of Reference for Languages"
            )

        with col2:
            st.metric(
                label="Vocabulary Variety",
                value=f"{evaluation.metrics.variety_score}/10",
                help="Lexical diversity score"
            )

        with col3:
            word_count = len(writing_text.split())
            st.metric(
                label="Word Count",
                value=word_count
            )

        # Corrected version
        if evaluation.corrected and evaluation.corrected != writing_text:
            st.subheader("✅ Corrected Version")
            st.success(evaluation.corrected)
        else:
            st.success("✅ No corrections needed - excellent work!")

        # Improvements
        if evaluation.improvements:
            st.subheader("💡 Suggestions for Improvement")
            for i, improvement in enumerate(evaluation.improvements, 1):
                st.markdown(f"{i}. {improvement}")

        # Expansion words
        if evaluation.expansion_words:
            st.subheader("📚 Vocabulary Expansion")
            st.markdown("Consider using these alternatives:")

            # Display in columns
            cols = st.columns(3)
            for i, vocab in enumerate(evaluation.expansion_words):
                col_idx = i % 3
                with cols[col_idx]:
                    st.markdown(f"**{vocab.replaces_simple_word}** → *{vocab.word}*")
                    st.caption(f"/{vocab.ipa}/ - {vocab.meaning_context}")

        # Follow-up questions
        if evaluation.questions:
            st.subheader("🤔 Follow-up Questions")
            for i, question in enumerate(evaluation.questions, 1):
                st.markdown(f"{i}. {question}")

        # Generate teacher feedback
        st.divider()

        if st.button("👨‍🏫 Get Teacher Feedback", type="secondary"):
            with st.spinner("Generating personalized feedback..."):
                try:
                    teacher_feedback = writing_service.generate_teacher_feedback(
                        evaluation=evaluation,
                        original_text=writing_text
                    )

                    st.subheader("👨‍🏫 Teacher's Feedback")
                    st.info(teacher_feedback)

                except Exception as e:
                    st.error(f"Error generating feedback: {str(e)}")


def render_sidebar(user: dict, auth_manager: AuthManager, session_mgr: SessionManager):
    """Render sidebar with user info and daily goals."""
    with st.sidebar:
        st.write(f"👤 **{user['email']}**")
        st.divider()

        # Daily Goal Progress
        st.header("🎯 Daily Goal")

        today_activities = auth_manager.get_today_activities(user.get('localId', ''))
        progress_data = ActivityLogger.get_daily_score_and_progress(
            activities_today=today_activities,
            daily_goal=100
        )

        score = progress_data['accumulated_score']
        goal = progress_data['daily_goal']
        percentage = progress_data['progress_percentage']
        exceeded = progress_data['exceeded']

        # Color based on progress
        if exceeded:
            bar_color = "#FFD700"  # Gold
        elif percentage >= 75:
            bar_color = "#4CAF50"  # Green
        elif percentage >= 50:
            bar_color = "#FFA726"  # Orange
        else:
            bar_color = "#2196F3"  # Blue

        st.markdown(f"""
        <div style="background-color: #f0f2f6; border-radius: 10px; padding: 15px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 1.2rem; font-weight: bold;">{score}</span>
                <span style="font-size: 0.9rem; color: #666;">/ {goal} points</span>
            </div>
            <div style="background-color: #ddd; border-radius: 5px; height: 20px; overflow: hidden;">
                <div style="background-color: {bar_color}; width: {percentage}%; height: 100%;
                            transition: width 0.3s ease; border-radius: 5px;"></div>
            </div>
            <div style="margin-top: 8px; font-size: 0.85rem; color: #555; text-align: center;">
                {progress_data['message']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Advanced Settings
        from accent_coach.presentation.components import render_advanced_settings
        render_advanced_settings()

        st.divider()

        # System info
        st.header("📊 System Info")

        if st.session_state.get('llm_available', False):
            st.success("✓ Groq API Connected")
        else:
            st.warning("⚠ Groq API Not Available")

        st.divider()

        session_mgr.render_logout_button()


def main():
    """Main Streamlit application entry point."""
    st.set_page_config(
        page_title="Accent Coach AI",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize session state
    init_session_state()

    # Initialize services
    services = initialize_services()

    # Store LLM availability in session state
    st.session_state.llm_available = services['llm'] is not None

    # Initialize legacy session manager
    session_mgr = SessionManager(
        login_callback=services['auth'].login_user,
        register_callback=services['auth'].register_user,
        get_history_callback=services['auth'].get_user_analyses,
        save_analysis_callback=services['auth'].save_analysis_to_firestore,
        save_registration_callback=services['auth'].save_user_registration
    )

    # Auth flow
    should_return, _ = session_mgr.render_login_ui()
    if should_return:
        return

    # Get logged-in user
    user = st.session_state.user

    # Main title
    st.title("🎙️ Accent Coach AI")
    st.markdown("Practice your American English pronunciation with AI-powered feedback")

    # Sidebar
    render_sidebar(user, services['auth'], session_mgr)

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Pronunciation Practice",
        "🗣️ Conversation Tutor",
        "✍️ Writing Coach",
        "💬 Language Assistant"
    ])

    with tab1:
        # Pronunciation Practice tab (fully implemented!)
        render_pronunciation_practice_tab(user, services['pronunciation'])

    with tab2:
        # Conversation Tutor tab (fully implemented!)
        render_conversation_tutor_tab(user, services['conversation'])

    with tab3:
        # Writing Coach tab (fully implemented!)
        render_writing_coach_tab(user, services['writing'])

    with tab4:
        # Language Query tab (fully implemented!)
        render_language_query_tab(user, services['language_query'])


if __name__ == "__main__":
    main()
