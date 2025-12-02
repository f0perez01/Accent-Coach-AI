# Accent Coach AI - Modular Architecture

This directory contains the refactored Accent Coach AI application following **Domain-Driven Design** principles.

## 📁 Structure

```
accent_coach/
├── domain/                  # Business logic (Bounded Contexts)
│   ├── audio/              # BC1: Audio Processing
│   ├── transcription/      # BC2: Speech Recognition
│   ├── phonetic/           # BC3: Phonetic Analysis
│   ├── pronunciation/      # BC4: Pronunciation Practice
│   ├── conversation/       # BC5: Conversation Tutor
│   ├── writing/            # BC7: Writing Coach
│   └── language_query/     # BC9: Language Assistant
│
├── infrastructure/          # External dependencies
│   ├── llm/                # BC6: LLM Orchestration
│   ├── persistence/        # Repository Pattern
│   ├── auth/               # Authentication
│   └── activity/           # Activity Tracking
│
├── presentation/            # UI Layer
│   ├── streamlit_app.py    # Main entry point
│   ├── controllers/        # UI → Domain
│   └── components/         # Pure UI components
│
└── shared/                  # Common utilities
    ├── models.py
    └── exceptions.py
```

## 🎯 Design Principles

### 1. Separation of Concerns
- **Domain**: Pure business logic, no dependencies on UI or infrastructure
- **Infrastructure**: External dependencies (DB, LLM, Auth)
- **Presentation**: Thin UI layer, delegates to controllers

### 2. Dependency Injection
- No global singletons
- Services receive dependencies via constructor
- Easy to test and swap implementations

### 3. Repository Pattern
- Abstract persistence behind interfaces
- Can switch from Firestore → PostgreSQL without touching domain logic
- In-memory implementations for fast testing

## 🚀 Migration Roadmap

### Sprint 1 (2-3 weeks): Infrastructure
- [x] Create directory structure
- [ ] Implement Repository interfaces
- [ ] Implement LLM Service abstraction
- [ ] Implement Activity Tracker

### Sprint 2 (3-4 weeks): Audio & ASR
- [ ] Implement AudioService
- [ ] Implement TranscriptionService
- [ ] Migrate ASRModelManager

### Sprint 3 (2-3 weeks): Phonetic Analysis
- [ ] Consolidate phonetic logic
- [ ] Implement PhoneticAnalysisService
- [ ] Extract drill word selection logic

### Sprint 4 (3 weeks): Pronunciation Practice
- [ ] Implement PronunciationPracticeService
- [ ] Create PronunciationController
- [ ] Refactor app.py pronunciation tab

### Sprint 5 (2-3 weeks): Conversation Tutor
- [ ] Implement ConversationTutorService
- [ ] Create ConversationController

### Sprint 6 (2 weeks): Writing & Language Query
- [ ] Implement WritingCoachService
- [ ] Implement LanguageQueryService

### Sprint 7 (1 week): UI Cleanup
- [ ] Extract UI logic from ResultsVisualizer
- [ ] Create pure UI components

### Sprint 8 (Ongoing): Tests
- [ ] Unit tests for all services
- [ ] Integration tests
- [ ] Acceptance tests

## 📊 Metrics

### Current State (Monolith)
- `app.py`: 1,295 lines
- Test speed: 30s per test
- Test coverage: ~10%
- Coupling: High (singletons everywhere)

### Target State (Modular)
- `streamlit_app.py`: ~300 lines
- Test speed: <1s per test
- Test coverage: >80%
- Coupling: Low (dependency injection)

## 🧪 Testing

```bash
# Unit tests (fast, no external dependencies)
pytest tests/unit/

# Integration tests (with in-memory repos)
pytest tests/integration/

# Acceptance tests (end-to-end)
pytest tests/acceptance/
```

## 📚 References

- [ARCHITECTURE_ANALYSIS.md](../ARCHITECTURE_ANALYSIS.md) - Full architectural analysis
- Microservices Patterns by Chris Richardson (Cap. 1, 3, 13)

## 🎉 Benefits

✅ **Testability**: Unit tests without Firebase, Groq, ASR model
✅ **Maintainability**: Clear separation of concerns
✅ **Scalability**: Each service can scale independently
✅ **Flexibility**: Easy to swap implementations (Groq → OpenAI, Firestore → Postgres)
✅ **Team productivity**: Faster onboarding, parallel development

---

**Status**: 🚧 Structure created, implementation in progress (Sprint 1)
