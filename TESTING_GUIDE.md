# Testing Guide - New Streamlit App

## 🚀 How to Run the New App

### Step 1: Activate Virtual Environment

```bash
cd c:\Users\f0per\f28\Accent-Coach-AI
venv\Scripts\activate
```

### Step 2: Ensure Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Set Environment Variables

Make sure you have your `.env` file or set the API key:

```bash
# Option 1: Create .env file
echo GROQ_API_KEY=your_api_key_here > .env

# Option 2: Set environment variable (Windows)
set GROQ_API_KEY=your_api_key_here
```

### Step 4: Run the New App

```bash
streamlit run streamlit_app.py
```

The app should open in your browser at `http://localhost:8501`

---

## ✅ Testing Checklist - Week 1

### Phase 1: Service Initialization

**Goal**: Verify all services are initialized correctly

- [ ] **Test 1.1**: App starts without errors
  - **Action**: Run `streamlit run streamlit_app.py`
  - **Expected**: App loads, no import errors
  - **Pass/Fail**: _____

- [ ] **Test 1.2**: LLM service detection
  - **Action**: Check sidebar for "✓ Groq API Connected"
  - **Expected**: Green success message if API key is set
  - **Pass/Fail**: _____

- [ ] **Test 1.3**: No console errors
  - **Action**: Check terminal/console for errors
  - **Expected**: No errors or warnings
  - **Pass/Fail**: _____

---

### Phase 5: Language Query Tab

**Goal**: Verify Language Assistant tab works correctly

#### Test 5.1: Navigate to Tab
- **Action**: Click on "💬 Language Assistant" tab
- **Expected**: Tab opens, shows header "Language Assistant"
- **Pass/Fail**: _____

#### Test 5.2: Initial State
- **Action**: Observe initial state
- **Expected**:
  - Shows "No queries yet. Ask your first question below!"
  - Text area is empty
  - Buttons: "🚀 Ask" and "🗑️ Clear History"
- **Pass/Fail**: _____

#### Test 5.3: Submit Simple Query
- **Action**:
  1. Type: "What does 'break the ice' mean?"
  2. Click "🚀 Ask"
- **Expected**:
  - Spinner shows "Thinking..."
  - Response appears in chat history
  - Category badge shows (likely "Idiom")
  - Query added to history
- **Pass/Fail**: _____

#### Test 5.4: Category Detection - Phrasal Verb
- **Action**: Type "What is the meaning of 'look up to'?"
- **Expected**: Category badge shows "🔄 Phrasal Verb"
- **Pass/Fail**: _____

#### Test 5.5: Category Detection - Expression
- **Action**: Type "Is 'touch base' commonly used?"
- **Expected**: Category badge shows "💬 Expression"
- **Pass/Fail**: _____

#### Test 5.6: Category Detection - Grammar
- **Action**: Type "When should I use present perfect tense?"
- **Expected**: Category badge shows "📚 Grammar"
- **Pass/Fail**: _____

#### Test 5.7: Conversation History
- **Action**:
  1. Submit 2-3 queries
  2. Check history display
- **Expected**:
  - All queries shown in expandable cards
  - Most recent query expanded by default
  - Each card shows: question, category, answer
- **Pass/Fail**: _____

#### Test 5.8: Follow-up Query (Context)
- **Action**:
  1. Ask: "What does 'bite the bullet' mean?"
  2. Then ask: "Can you give me more examples?"
- **Expected**:
  - Second response should reference the idiom from first query
  - Shows context understanding
- **Pass/Fail**: _____

#### Test 5.9: Clear History
- **Action**: Click "🗑️ Clear History"
- **Expected**:
  - History cleared
  - Shows "No queries yet" message
  - Page reloads
- **Pass/Fail**: _____

#### Test 5.10: Empty Query Validation
- **Action**:
  1. Leave text area empty
  2. Click "🚀 Ask"
- **Expected**: Nothing happens (button doesn't trigger)
- **Pass/Fail**: _____

#### Test 5.11: Long Query
- **Action**: Type a very long question (200+ characters)
- **Expected**:
  - Query processes normally
  - Title truncated to 50 chars in history
  - Full query shown inside expander
- **Pass/Fail**: _____

#### Test 5.12: Error Handling (No API Key)
- **Action**:
  1. Remove GROQ_API_KEY from environment
  2. Restart app
  3. Try to submit query
- **Expected**: Error message displayed gracefully
- **Pass/Fail**: _____

---

### Authentication & Sidebar

#### Test Auth.1: Login Required
- **Action**: Access app without logging in
- **Expected**: Login screen appears
- **Pass/Fail**: _____

#### Test Auth.2: Successful Login
- **Action**: Enter valid credentials
- **Expected**:
  - Redirects to main app
  - Shows user email in sidebar
- **Pass/Fail**: _____

#### Test Sidebar.1: Daily Goal Display
- **Action**: Check sidebar "🎯 Daily Goal" section
- **Expected**:
  - Shows score (0-100+)
  - Shows progress bar
  - Shows message
- **Pass/Fail**: _____

#### Test Sidebar.2: System Info
- **Action**: Check "📊 System Info" section
- **Expected**: Shows LLM connection status
- **Pass/Fail**: _____

#### Test Sidebar.3: Logout
- **Action**: Click logout button
- **Expected**: Returns to login screen
- **Pass/Fail**: _____

---

## 🐛 Bug Report Template

If you find a bug, document it here:

### Bug #1
**Date**: _____
**Tester**: _____
**Severity**: ☐ Critical  ☐ High  ☐ Medium  ☐ Low

**Description**:
_____

**Steps to Reproduce**:
1. _____
2. _____
3. _____

**Expected Result**:
_____

**Actual Result**:
_____

**Error Message** (if any):
```
_____
```

**Screenshot**: (attach if relevant)

**Status**: ☐ Open  ☐ In Progress  ☐ Fixed  ☐ Won't Fix

**Resolution**:
_____

---

## 📊 Test Summary

**Date**: _____
**Tester**: _____

| Category | Tests | Passed | Failed | Pass Rate |
|----------|-------|--------|--------|-----------|
| Service Init | 3 | ___ | ___ | ___% |
| Language Query | 12 | ___ | ___ | ___% |
| Auth & Sidebar | 5 | ___ | ___ | ___% |
| **Total** | **20** | ___ | ___ | ___% |

**Overall Status**: ☐ All Passed  ☐ Some Issues  ☐ Major Issues

**Ready for Week 2**: ☐ Yes  ☐ No (needs fixes)

---

## 🔧 Troubleshooting

### Issue: Import Errors
**Symptoms**: `ModuleNotFoundError` or `ImportError`
**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

### Issue: API Key Not Found
**Symptoms**: "⚠ Groq API Not Available"
**Solution**:
```bash
# Set environment variable
set GROQ_API_KEY=your_key_here

# Or create .env file
echo GROQ_API_KEY=your_key_here > .env
```

### Issue: Streamlit Errors
**Symptoms**: App crashes or freezes
**Solution**:
```bash
# Clear cache
streamlit cache clear

# Restart app
streamlit run streamlit_app.py
```

### Issue: Firebase Errors
**Symptoms**: Login fails
**Solution**:
- Check Firebase configuration in `auth_manager.py`
- Verify Firebase credentials in secrets

---

## 📝 Notes

Use this section for any additional observations during testing:

**Positive Observations**:
- _____

**Areas for Improvement**:
- _____

**Performance Notes**:
- _____

**User Experience Notes**:
- _____

---

**Testing Complete**: ☐ Yes  ☐ No
**Next Steps**: _____
