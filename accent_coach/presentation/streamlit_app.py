"""
Streamlit Main Application

Thin UI orchestrator following Domain-Driven Design.
Delegates to domain services with dependency injection.

Refactored from monolithic app.py (1,295 lines → ~400 lines target)
"""

import os
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

    # Initialize repositories (using in-memory for now)
    pronunciation_repo = InMemoryPronunciationRepository()
    conversation_repo = InMemoryConversationRepository()
    writing_repo = InMemoryWritingRepository()

    # Initialize domain services with dependency injection
    audio_service = AudioService()
    transcription_service = TranscriptionService()
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
        st.info("🚧 Pronunciation Practice - Coming in Week 3")
        st.markdown("This tab will use `PronunciationPracticeService` for audio analysis.")

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
