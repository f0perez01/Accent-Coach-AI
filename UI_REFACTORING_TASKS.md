# UI Refactoring Tasks - Streamlit App Migration

## 📋 Overview

Migrate the monolithic `app.py` (1,295+ lines) to the new microservices architecture using `accent_coach/presentation/streamlit_app.py` (~300 lines target).

**Current Status**:
- ✅ Backend microservices fully implemented (8 bounded contexts)
- ✅ All services tested (128/128 tests passing, 79% coverage)
- ⏳ UI layer still uses old monolithic managers
- 🎯 Goal: Refactor UI to use new domain services with dependency injection

---

## 🎯 High-Level Goals

1. **Replace Old Managers with New Services**
   - Remove: `GroqManager`, `WritingCoachManager`, `LanguageQueryManager`, `ConversationManager`
   - Use: New domain services from `accent_coach/domain/*`

2. **Implement Dependency Injection**
   - Initialize all services at app startup
   - Pass services to UI components via function parameters

3. **Modular Architecture**
   - Use controllers for business logic
   - Use UI components for rendering
   - Keep streamlit_app.py as thin orchestrator

4. **Maintain Feature Parity**
   - All 4 tabs working: Pronunciation, Conversation, Writing, Language Query
   - Preserve daily goals, history, Firebase auth

---

## 📦 Dependencies to Initialize

### Core Services (from `accent_coach/domain/`)

```python
# BC1: Audio Processing
from accent_coach.domain.audio.service import AudioService

# BC2: Transcription (ASR)
from accent_coach.domain.transcription.service import TranscriptionService

# BC3: Phonetic Analysis
from accent_coach.domain.phonetic.service import PhoneticAnalysisService

# BC4: Pronunciation Practice
from accent_coach.domain.pronunciation.service import PronunciationPracticeService

# BC5: Conversation Practice
from accent_coach.domain.conversation.service import ConversationService

# BC7: Writing Coach
from accent_coach.domain.writing.service import WritingService

# BC8: Language Query
from accent_coach.domain.language_query.service import LanguageQueryService
```

### Infrastructure Services

```python
# BC6: LLM Orchestration
from accent_coach.infrastructure.llm.groq_provider import GroqLLMService

# Activity Tracking
from accent_coach.infrastructure.activity.tracker import ActivityLogger

# Repositories (in-memory for MVP, Firestore for production)
from accent_coach.infrastructure.persistence.in_memory_repositories import (
    InMemoryPronunciationRepository,
    InMemoryConversationRepository,
    InMemoryWritingRepository
)
```

### Legacy Components to Keep (Temporarily)

```python
# These still work with new architecture
from auth_manager import AuthManager  # Firebase auth wrapper
from session_manager import SessionManager  # Login/logout UI
from practice_texts import PracticeTextManager  # Text library
from ipa_definitions import IPADefinitionsManager  # IPA reference
from results_visualizer import ResultsVisualizer  # Plotly visualizations
```

---

## 🔨 Implementation Tasks

### Phase 1: Service Initialization (Priority: HIGH)

**File**: `accent_coach/presentation/streamlit_app.py`

- [ ] **Task 1.1**: Initialize LLM Service
  ```python
  groq_api_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY"))
  llm_service = GroqLLMService(api_key=groq_api_key)
  ```

- [ ] **Task 1.2**: Initialize Audio & ASR Services
  ```python
  audio_service = AudioService()
  transcription_service = TranscriptionService()
  ```

- [ ] **Task 1.3**: Initialize Phonetic & Pronunciation Services
  ```python
  phonetic_service = PhoneticAnalysisService()
  pronunciation_service = PronunciationPracticeService(
      audio_service=audio_service,
      transcription_service=transcription_service,
      phonetic_service=phonetic_service,
      llm_service=llm_service,
      repository=InMemoryPronunciationRepository()  # or None
  )
  ```

- [ ] **Task 1.4**: Initialize Conversation Service
  ```python
  conversation_service = ConversationService(
      llm_service=llm_service,
      repository=InMemoryConversationRepository()  # or None
  )
  ```

- [ ] **Task 1.5**: Initialize Writing Service
  ```python
  writing_service = WritingService(
      llm_service=llm_service
  )
  ```

- [ ] **Task 1.6**: Initialize Language Query Service
  ```python
  language_query_service = LanguageQueryService(
      llm_service=llm_service
  )
  ```

- [ ] **Task 1.7**: Preserve Legacy Components
  ```python
  # Keep these for now
  auth_manager = AuthManager(st.secrets if hasattr(st, 'secrets') else None)
  session_mgr = SessionManager(...)
  activity_logger = ActivityLogger()
  ```

**Estimated Time**: 2-3 hours

---

### Phase 2: Tab 1 - Pronunciation Practice (Priority: HIGH)

**Current File**: `app.py` lines 986-1200
**Target**: New controller or inline implementation

#### Sub-tasks:

- [ ] **Task 2.1**: Migrate IPA Study Phase
  - **Current**: Uses `PhonemeProcessor.generate_reference_phonemes()` + `ResultsVisualizer.render_ipa_guide()`
  - **Action**: Keep as-is (works with new architecture)
  - **Location**: Lines 993-1015

- [ ] **Task 2.2**: Migrate Audio Recording
  - **Current**: Uses `st.audio_input()` or custom widget
  - **Action**: Keep UI, update backend call
  - **Old**: `analysis_pipeline.analyze_recording(...)`
  - **New**: `pronunciation_service.analyze_recording(audio_bytes, reference_text, user_id, config)`

- [ ] **Task 2.3**: Update Result Display
  - **Current**: Uses `ResultsVisualizer.display_comparison_table()`, `plot_waveform()`, etc.
  - **Action**: Keep visualizations, update data source
  - **Old**: `result = analysis_pipeline.analyze_recording(...)`
  - **New**: `result = pronunciation_service.analyze_recording(...)` → PracticeResult model

- [ ] **Task 2.4**: Migrate LLM Feedback Display
  - **Current**: Displays `result['llm_feedback']` if available
  - **New**: Display `result.llm_feedback` (from PracticeResult dataclass)

- [ ] **Task 2.5**: Migrate Drill Word Suggestions
  - **Current**: Auto-selects error words for next practice
  - **New**: Use `result.analysis.suggested_drill_words`

- [ ] **Task 2.6**: Save to Firebase
  - **Current**: `save_analysis_to_firestore(user_id, reference_text, result)`
  - **New**: Use repository pattern → `pronunciation_repository.save_analysis(user_id, reference_text, result)`

**Estimated Time**: 4-6 hours

---

### Phase 3: Tab 2 - Conversation Tutor (Priority: MEDIUM)

**Current File**: `app.py` function `render_conversation_tutor()` (lines 217-429)
**Target**: New controller or separate component

#### Sub-tasks:

- [ ] **Task 3.1**: Create Conversation Session
  - **Old**: `ConversationManager.create_session(user_id, mode, topic)`
  - **New**: `conversation_service.create_session(user_id, config)` → ConversationSession

- [ ] **Task 3.2**: Display Topic Starters
  - **Old**: `ConversationStarters.get_starter_by_topic(topic)`
  - **New**: `from accent_coach.domain.conversation.starters import ConversationStarters` (same!)

- [ ] **Task 3.3**: Process User Turns
  - **Old**: `ConversationManager.process_turn(session_id, user_transcript)`
  - **New**: `conversation_service.process_turn(session_id, user_transcript, user_id)` → TurnResult

- [ ] **Task 3.4**: Display Corrections & Follow-ups
  - **Current**: Shows `turn.correction` and `turn.follow_up`
  - **New**: Same fields from TurnResult model

- [ ] **Task 3.5**: Show Conversation History
  - **Current**: Displays all turns in session
  - **New**: Use `session.turns` list

- [ ] **Task 3.6**: Close Session
  - **Old**: `ConversationManager.close_session(session_id)`
  - **New**: `conversation_service.close_session(session_id)` (if needed)

- [ ] **Task 3.7**: Practice vs Exam Modes
  - **Current**: Toggle between modes
  - **New**: Use `ConversationMode.PRACTICE` or `ConversationMode.EXAM` in config

**Estimated Time**: 3-4 hours

---

### Phase 4: Tab 3 - Writing Coach (Priority: MEDIUM)

**Current File**: `app.py` function `render_writing_coach()` (lines 431-664)
**Target**: New controller

#### Sub-tasks:

- [ ] **Task 4.1**: Display Question Bank
  - **Old**: `writing_coach_manager.get_question_by_category(category, difficulty)`
  - **New**: `writing_service.get_question_by_category(category, difficulty)` → InterviewQuestion

- [ ] **Task 4.2**: Filter by Category & Difficulty
  - **Current**: Dropdown selection for Behavioral/Technical/Remote Work + Easy/Medium/Hard
  - **New**: Use `QuestionCategory` and `QuestionDifficulty` enums

- [ ] **Task 4.3**: Show XP Values
  - **Old**: Manual calculation (10/20/40)
  - **New**: `question.get_xp_value()`

- [ ] **Task 4.4**: Evaluate User Answer
  - **Old**: `writing_coach_manager.evaluate_writing(text)`
  - **New**: `writing_service.evaluate_writing(text, config)` → WritingEvaluation

- [ ] **Task 4.5**: Display CEFR Metrics
  - **Current**: Shows `evaluation['metrics']['cefr_level']`, `variety_score`
  - **New**: `evaluation.metrics.cefr_level`, `evaluation.metrics.variety_score`

- [ ] **Task 4.6**: Show Corrections & Improvements
  - **Current**: Displays corrected text, improvement suggestions, expansion words
  - **New**: `evaluation.corrected`, `evaluation.improvements`, `evaluation.expansion_words`

- [ ] **Task 4.7**: Generate Teacher Feedback
  - **Old**: `writing_coach_manager.generate_teacher_feedback(evaluation, original_text)`
  - **New**: `writing_service.generate_teacher_feedback(evaluation, original_text)`

- [ ] **Task 4.8**: Track XP & Progress
  - **Current**: Uses ActivityLogger to save XP
  - **Action**: Keep ActivityLogger integration

**Estimated Time**: 3-4 hours

---

### Phase 5: Tab 4 - Language Assistant (Priority: MEDIUM)

**Current File**: `app.py` function `render_language_chat()` (lines 666-748)
**Target**: Simple implementation (already very clean)

#### Sub-tasks:

- [ ] **Task 5.1**: Process User Query
  - **Old**: `language_query_manager.process_query(user_query, conversation_history)`
  - **New**: `language_query_service.process_query(user_query, conversation_history, config)` → QueryResult

- [ ] **Task 5.2**: Display Response
  - **Current**: Shows `result['llm_response']`
  - **New**: `result.llm_response`

- [ ] **Task 5.3**: Show Query Category
  - **Current**: Shows detected category (idiom, phrasal verb, etc.)
  - **New**: `result.category.value` (from QueryCategory enum)

- [ ] **Task 5.4**: Maintain Conversation History
  - **Current**: Stores in session state as list of dicts
  - **Action**: Keep same structure (already compatible)

- [ ] **Task 5.5**: Clear History Button
  - **Current**: Clears session state
  - **Action**: Keep as-is

**Estimated Time**: 1-2 hours

---

### Phase 6: Sidebar & Session Management (Priority: HIGH)

**Current File**: `app.py` lines 796-976
**Target**: Keep most of it, update data sources

#### Sub-tasks:

- [ ] **Task 6.1**: Daily Goal Progress Bar
  - **Current**: Uses `ActivityLogger.get_daily_score_and_progress()`
  - **Action**: Keep as-is (ActivityLogger works with new architecture)

- [ ] **Task 6.2**: User History Display
  - **Current**: Uses `SessionManager.render_user_info_and_history(user)`
  - **Action**: Update to use new repositories instead of Firestore directly
  - **Possible**: Add `get_history()` methods to each repository

- [ ] **Task 6.3**: Practice Text Selection
  - **Current**: Uses `PracticeTextManager`
  - **Action**: Keep as-is (independent component)

- [ ] **Task 6.4**: Advanced Settings (ASR Model, G2P, etc.)
  - **Current**: Stored in `st.session_state.config`
  - **Action**: Map to service config objects
  - **Example**:
    ```python
    # Map session state to domain config
    practice_config = PracticeConfig(
        sample_rate=16000,
        normalize_audio=st.session_state.config['enable_enhancement'],
        use_g2p=st.session_state.config['use_g2p'],
        language=st.session_state.config['lang'],
        use_llm_feedback=st.session_state.config['use_llm']
    )
    ```

- [ ] **Task 6.5**: LLM Settings (Model & Temperature)
  - **Current**: Uses `groq_manager.model`, `groq_manager.temperature`
  - **Action**: Update to use service config
  - **Example**: Pass to `WritingConfig(model=..., temperature=...)`

- [ ] **Task 6.6**: Logout Button
  - **Current**: Uses `SessionManager.render_logout_button()`
  - **Action**: Keep as-is

**Estimated Time**: 2-3 hours

---

### Phase 7: Testing & Validation (Priority: HIGH)

- [ ] **Task 7.1**: Manual Testing - Pronunciation Tab
  - [ ] Record audio and analyze
  - [ ] Verify LLM feedback appears
  - [ ] Verify drill words auto-select
  - [ ] Test with/without LLM enabled

- [ ] **Task 7.2**: Manual Testing - Conversation Tab
  - [ ] Start practice session
  - [ ] Submit multiple turns
  - [ ] Verify corrections and follow-ups
  - [ ] Test exam mode vs practice mode

- [ ] **Task 7.3**: Manual Testing - Writing Tab
  - [ ] Select question by category/difficulty
  - [ ] Submit answer
  - [ ] Verify CEFR evaluation
  - [ ] Verify teacher feedback
  - [ ] Check XP tracking

- [ ] **Task 7.4**: Manual Testing - Language Query Tab
  - [ ] Ask various query types (idiom, phrasal verb, grammar)
  - [ ] Verify category detection
  - [ ] Test multi-turn conversation

- [ ] **Task 7.5**: Integration Testing
  - [ ] Test daily goal updates across tabs
  - [ ] Test history persistence
  - [ ] Test authentication flow
  - [ ] Test with real Groq API

- [ ] **Task 7.6**: Error Handling
  - [ ] Test with API key missing
  - [ ] Test with invalid audio
  - [ ] Test with network errors
  - [ ] Verify graceful degradation

**Estimated Time**: 4-6 hours

---

### Phase 8: Cleanup & Documentation (Priority: LOW)

- [ ] **Task 8.1**: Remove Old Imports
  - [ ] Delete imports for old managers (`GroqManager`, `WritingCoachManager`, etc.)
  - [ ] Clean up unused imports

- [ ] **Task 8.2**: Update Comments & Docstrings
  - [ ] Add docstrings to new functions
  - [ ] Update architecture comments

- [ ] **Task 8.3**: Create Migration Guide
  - [ ] Document changes from old → new
  - [ ] Update QUICKSTART.md with new UI details

- [ ] **Task 8.4**: Deprecate Old Files
  - [ ] Move old managers to `legacy/` folder
  - [ ] Add deprecation warnings

**Estimated Time**: 2-3 hours

---

## 📊 Total Estimated Time

| Phase | Description | Time |
|-------|-------------|------|
| 1 | Service Initialization | 2-3 hours |
| 2 | Pronunciation Tab | 4-6 hours |
| 3 | Conversation Tab | 3-4 hours |
| 4 | Writing Tab | 3-4 hours |
| 5 | Language Query Tab | 1-2 hours |
| 6 | Sidebar & Session | 2-3 hours |
| 7 | Testing & Validation | 4-6 hours |
| 8 | Cleanup & Docs | 2-3 hours |
| **Total** | **Full UI Refactoring** | **21-31 hours** |

**Estimated Sprint Duration**: 3-5 days (for one developer)

---

## 🎯 Success Criteria

### Must Have (MVP)
- ✅ All 4 tabs functional (Pronunciation, Conversation, Writing, Language Query)
- ✅ Firebase authentication working
- ✅ Daily goal tracking working
- ✅ LLM integration working (Groq)
- ✅ History persistence working

### Nice to Have
- ⭐ Repository pattern fully integrated (Firestore for production)
- ⭐ Controllers extracted to separate files
- ⭐ UI components modularized
- ⭐ Integration tests added

### Quality Metrics
- 🎯 No errors in browser console
- 🎯 All features from old app.py working
- 🎯 Code reduced from 1,295 lines → ~400 lines
- 🎯 Clean dependency injection throughout

---

## 🚨 Risk Mitigation

### Risk 1: Breaking Authentication
- **Mitigation**: Keep `AuthManager` and `SessionManager` unchanged
- **Fallback**: Use old Firebase code if needed

### Risk 2: LLM API Changes
- **Mitigation**: Service abstraction already in place (GroqLLMService)
- **Fallback**: Easy to swap providers (just change initialization)

### Risk 3: Lost Features
- **Mitigation**: Thorough manual testing checklist (Phase 7)
- **Fallback**: Keep old app.py as backup

### Risk 4: Performance Issues
- **Mitigation**: Services already tested independently
- **Fallback**: Add caching if needed

---

## 📁 File Structure After Refactoring

```
accent_coach/
├── domain/                           # ✅ Already implemented
│   ├── audio/
│   ├── transcription/
│   ├── phonetic/
│   ├── pronunciation/
│   ├── conversation/
│   ├── writing/
│   └── language_query/
├── infrastructure/                   # ✅ Already implemented
│   ├── llm/
│   ├── persistence/
│   └── activity/
├── presentation/                     # 🔨 TO BE REFACTORED
│   ├── streamlit_app.py             # Main entry point (thin orchestrator)
│   ├── controllers/                 # Business logic for UI
│   │   ├── pronunciation_controller.py
│   │   ├── conversation_controller.py
│   │   ├── writing_controller.py
│   │   └── language_query_controller.py
│   └── components/                  # Reusable UI components
│       ├── pronunciation_ui.py      # IPA guide, audio player
│       ├── conversation_ui.py       # Chat interface
│       ├── writing_ui.py            # Question selector, editor
│       ├── visualizers.py           # Plotly charts (keep existing)
│       └── sidebar.py               # Daily goals, settings (optional)
└── legacy/                          # ⚠️ Old managers (deprecated)
    ├── groq_manager.py
    ├── writing_coach_manager.py
    ├── language_query_manager.py
    └── conversation_manager.py
```

---

## 🔄 Migration Strategy

### Option A: Big Bang (Not Recommended)
- Rewrite everything at once
- High risk of breaking things
- Faster but risky

### Option B: Incremental (Recommended)
1. **Week 1**: Phase 1 (Service Init) + Phase 5 (Language Query - simplest tab)
2. **Week 2**: Phase 4 (Writing) + Phase 3 (Conversation)
3. **Week 3**: Phase 2 (Pronunciation - most complex) + Phase 6 (Sidebar)
4. **Week 4**: Phase 7 (Testing) + Phase 8 (Cleanup)

### Option C: Parallel Development
- Keep old `app.py` running
- Build new `streamlit_app.py` alongside
- Switch when ready (feature flag)

**Recommendation**: Option B (Incremental) with daily commits

---

## 📝 Notes

### Key Architectural Changes

1. **No More Managers**: Direct use of domain services
2. **Dependency Injection**: Services passed via constructors
3. **Type Safety**: Use domain models (dataclasses, enums)
4. **Repository Pattern**: Abstract persistence layer
5. **Clean Separation**: UI → Controller → Service → Domain

### Preserved Components

These components work with new architecture (keep as-is):
- `AuthManager` - Firebase authentication wrapper
- `SessionManager` - Login/logout UI logic
- `PracticeTextManager` - Text library (could be migrated later)
- `IPADefinitionsManager` - IPA reference data
- `ResultsVisualizer` - Plotly visualizations
- `TTSGenerator` - Text-to-speech (part of AudioService)
- `AudioValidator` - Audio quality checks (part of AudioService)

### Breaking Changes

**Old Code**:
```python
result = analysis_pipeline.analyze_recording(
    audio_data, reference_text, config, groq_manager
)
```

**New Code**:
```python
result = pronunciation_service.analyze_recording(
    audio_bytes=audio_data,
    reference_text=reference_text,
    user_id=user['localId'],
    config=PracticeConfig(...)
)
```

---

## 🎓 Learning Resources

- [SPRINT8_COMPLETED.md](SPRINT8_COMPLETED.md) - Architecture summary
- [QUICKSTART.md](QUICKSTART.md) - Service usage examples
- [tests/unit/](tests/unit/) - 128 test examples showing service usage

---

## ✅ Checklist Summary

**Before Starting**:
- [ ] Read SPRINT8_COMPLETED.md
- [ ] Read QUICKSTART.md
- [ ] Review service tests in tests/unit/
- [ ] Backup current app.py

**During Development**:
- [ ] Follow incremental migration (Option B)
- [ ] Commit after each phase
- [ ] Test manually after each change
- [ ] Update this document with progress

**After Completion**:
- [ ] All 4 tabs working
- [ ] All tests still passing (128/128)
- [ ] Manual QA complete
- [ ] Documentation updated
- [ ] Old managers deprecated

---

**Created**: 2025-12-03
**Last Updated**: 2025-12-03
**Status**: 📋 Planning Phase
**Next Action**: Start Phase 1 (Service Initialization)
