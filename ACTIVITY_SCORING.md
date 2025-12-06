# Activity Scoring System

This document describes how each activity type contributes to the daily score goal (100 points).

## Scoring by Activity Type

### 1. 🎯 Pronunciation Practice
- **Score Calculation**: `word_count × (word_accuracy / 100)`
- **Example**: 10 words with 80% accuracy = 8 points
- **Location**: [streamlit_app.py:389-411](accent_coach/presentation/streamlit_app.py#L389-L411)
- **Metadata**:
  - `word_count`: Number of words practiced
  - `word_accuracy`: Percentage of words pronounced correctly
  - `phoneme_accuracy`: Phoneme-level accuracy

### 2. 🗣️ Conversation Tutor
- **Score Calculation**: `max(5, word_count - error_count)`
- **Example**: 15 words with 2 errors = 13 points
- **Minimum**: 5 points per turn
- **Location**: [streamlit_app.py:916-938](accent_coach/presentation/streamlit_app.py#L916-L938)
- **Metadata**:
  - `word_count`: Words in user's response
  - `error_count`: Number of errors detected
  - `mode`: Conversation mode (casual, professional, etc.)

### 3. ✍️ Writing Coach
- **Score Calculation**: `min(word_count, 50)`
- **Maximum**: 50 points per writing
- **Example**: 30 words = 30 points, 80 words = 50 points (capped)
- **Location**: [streamlit_app.py:1008-1029](accent_coach/presentation/streamlit_app.py#L1008-L1029)
- **Metadata**:
  - `word_count`: Total words written
  - `cefr_level`: CEFR level assessment (A1-C2)
  - `variety_score`: Vocabulary variety (0-10)

### 4. 💬 Language Query (Ask a Question)
- **Score Calculation**: `min(word_count, 10)`
- **Maximum**: 10 points per query
- **Example**: 5 words = 5 points, 15 words = 10 points (capped)
- **Location**: [streamlit_app.py:681-705](accent_coach/presentation/streamlit_app.py#L681-L705)
- **Metadata**:
  - `query_length`: Character length of query
  - `word_count`: Number of words in query
  - `category`: Query category (idiom, phrasal_verb, etc.)

## Daily Goal System

- **Daily Goal**: 100 points
- **Progress Display**: Shown in sidebar as "X / 100 points"
- **Progress Bar Colors**:
  - 🔵 Blue (0-49%): Just getting started
  - 🟠 Orange (50-74%): Making good progress
  - 🟢 Green (75-99%): Almost there!
  - 🟡 Gold (100%+): Goal achieved!

## Example Daily Sessions

### Balanced Practice (102 points)
- 3 pronunciation practices (15 words each, 90% accuracy) = 40.5 points
- 2 conversation turns (20 words each, 1 error) = 38 points
- 1 writing evaluation (35 words) = 35 points
- 1 language query (8 words) = 8 points
**Total: ~121 points** ✅

### Quick Practice (55 points)
- 2 pronunciation practices (10 words, 80% accuracy) = 16 points
- 1 conversation turn (15 words, 2 errors) = 13 points
- 1 writing evaluation (30 words) = 30 points
**Total: ~59 points** (59% progress)

### Intensive Writing Day (150 points)
- 3 long writing evaluations (50+ words each) = 150 points
**Total: 150 points** ✅ (exceeded goal)

## Technical Implementation

### Data Flow
1. User completes an activity
2. Activity is logged with `ActivityLog` object
3. Repository saves to Firestore with fields:
   - `user_id`: User identifier
   - `activity_type`: Type of activity (enum)
   - `timestamp`: When activity occurred
   - `score`: Calculated points
   - `weight`: Same as score (compatibility)
   - `date`: YYYY-MM-DD format
   - `metadata`: Activity-specific details

### Repository Methods
- **Save**: `activity_repo.log_activity(activity)`
- **Retrieve**: `activity_repo.get_today_activities(user_id, date)`
- **Calculate**: `ActivityLogger.get_daily_score_and_progress(activities, goal=100)`

### Firestore Collections
- Collection: `user_activities`
- Index: Composite index on `user_id` + `date`
- Query: Filters by user and date string for efficiency

## Motivational Messages

Progress messages displayed in sidebar:

- **0%**: "🌟 Ready to start your learning journey today?"
- **1-24%**: "🚀 Great start! Keep going!"
- **25-49%**: "💪 You're building momentum!"
- **50-74%**: "🔥 Halfway there! Don't stop now!"
- **75-99%**: "⭐ Almost at your goal!"
- **100%+**: "🎉 Perfect! You've reached your daily goal!"

## Notes

- All activities immediately update the daily score in the sidebar
- Scores persist across sessions via Firestore
- The sidebar uses cached repositories for performance
- Activity logging failures don't interrupt the user experience
