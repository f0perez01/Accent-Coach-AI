#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Activity Logger
Tracks user activities for progress heatmap visualization.
"""

from typing import Dict, Optional
from datetime import datetime
from enum import Enum


class ActivityType(Enum):
    """Types of user activities to track."""
    PRONUNCIATION_PRACTICE = "pronunciation_practice"
    WRITING_PRACTICE = "writing_practice"
    CONVERSATION_TURN = "conversation_turn"


class ActivityLogger:
    """
    Logs user activities for progress tracking and heatmap visualization.

    Responsibilities:
    - Record user activities (audio recordings, text submissions, conversation turns)
    - Calculate activity weight based on content length
    - Provide structured data for Firestore persistence

    Future enhancements:
    - Weighted scoring based on complexity
    - Streak tracking
    - Daily/weekly goals
    """

    @staticmethod
    def create_activity_log(
        user_id: str,
        activity_type: ActivityType,
        content_length: int = 0,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Create a structured activity log entry.

        Args:
            user_id: User identifier
            activity_type: Type of activity (pronunciation, writing, conversation)
            content_length: Length of content (words for text, seconds for audio)
            metadata: Optional additional data (e.g., CEFR level, error count)

        Returns:
            Dict ready for Firestore persistence with structure:
            {
                "user_id": str,
                "activity_type": str,
                "content_length": int,
                "weight": int,
                "metadata": dict,
                "timestamp": datetime,
                "date": str (YYYY-MM-DD for heatmap grouping)
            }
        """
        now = datetime.now()

        # Simple weight calculation (can be enhanced later)
        weight = ActivityLogger._calculate_weight(activity_type, content_length)

        return {
            "user_id": user_id,
            "activity_type": activity_type.value,
            "content_length": content_length,
            "weight": weight,
            "metadata": metadata or {},
            "timestamp": now,
            "date": now.strftime("%Y-%m-%d")  # For heatmap grouping
        }

    @staticmethod
    def _calculate_weight(activity_type: ActivityType, content_length: int) -> int:
        """
        Calculate activity weight for progress tracking.

        Current implementation: Simple base weight
        Future: Could factor in difficulty, accuracy, complexity

        Args:
            activity_type: Type of activity
            content_length: Length of content

        Returns:
            Integer weight (1-100 scale)
        """
        # Base weights by activity type
        base_weights = {
            ActivityType.PRONUNCIATION_PRACTICE: 10,
            ActivityType.WRITING_PRACTICE: 15,
            ActivityType.CONVERSATION_TURN: 12
        }

        base = base_weights.get(activity_type, 10)

        # Simple scaling: +1 point per 10 units of content
        # For text: 10 words = +1 point
        # For audio: 10 seconds = +1 point
        length_bonus = min(content_length // 10, 20)  # Cap at +20

        return base + length_bonus

    @staticmethod
    def log_pronunciation_activity(
        user_id: str,
        audio_duration_seconds: float,
        word_count: int,
        error_count: int = 0
    ) -> Dict:
        """
        Log a pronunciation practice activity.

        Args:
            user_id: User identifier
            audio_duration_seconds: Duration of recorded audio
            word_count: Number of words in reference text
            error_count: Number of pronunciation errors detected

        Returns:
            Activity log dict
        """
        metadata = {
            "audio_duration": audio_duration_seconds,
            "word_count": word_count,
            "error_count": error_count
        }

        # Use word count as content length for weight calculation
        return ActivityLogger.create_activity_log(
            user_id=user_id,
            activity_type=ActivityType.PRONUNCIATION_PRACTICE,
            content_length=word_count,
            metadata=metadata
        )

    @staticmethod
    def log_writing_activity(
        user_id: str,
        text_length: int,
        cefr_level: str = "N/A",
        variety_score: int = 0
    ) -> Dict:
        """
        Log a writing practice activity.

        Args:
            user_id: User identifier
            text_length: Number of words in written text
            cefr_level: Assessed CEFR level
            variety_score: Vocabulary variety score (1-10)

        Returns:
            Activity log dict
        """
        metadata = {
            "text_length": text_length,
            "cefr_level": cefr_level,
            "variety_score": variety_score
        }

        return ActivityLogger.create_activity_log(
            user_id=user_id,
            activity_type=ActivityType.WRITING_PRACTICE,
            content_length=text_length,
            metadata=metadata
        )

    @staticmethod
    def log_conversation_activity(
        user_id: str,
        transcript_length: int,
        turn_number: int = 1,
        errors_detected: int = 0
    ) -> Dict:
        """
        Log a conversation turn activity.

        Args:
            user_id: User identifier
            transcript_length: Number of words in user's response
            turn_number: Turn number in conversation session
            errors_detected: Number of errors detected in turn

        Returns:
            Activity log dict
        """
        metadata = {
            "transcript_length": transcript_length,
            "turn_number": turn_number,
            "errors_detected": errors_detected
        }

        return ActivityLogger.create_activity_log(
            user_id=user_id,
            activity_type=ActivityType.CONVERSATION_TURN,
            content_length=transcript_length,
            metadata=metadata
        )

    @staticmethod
    def aggregate_daily_activities(activities: list) -> Dict[str, int]:
        """
        Aggregate activities by date for heatmap visualization.

        Args:
            activities: List of activity log dicts

        Returns:
            Dict mapping date (YYYY-MM-DD) to total weight
            Example: {"2025-11-29": 45, "2025-11-28": 30}
        """
        daily_weights = {}

        for activity in activities:
            date = activity.get("date", "")
            weight = activity.get("weight", 0)

            if date:
                daily_weights[date] = daily_weights.get(date, 0) + weight

        return daily_weights

    @staticmethod
    def get_daily_score_and_progress(
        activities_today: list,
        daily_goal: int = 100
    ) -> Dict:
        """
        Calculate accumulated score for today and progress percentage towards daily goal.

        Args:
            activities_today: List of activity records for current day
            daily_goal: Daily goal in points (default 100)

        Returns:
            Dict with:
            - date: Today's date (YYYY-MM-DD)
            - accumulated_score: Total points earned today
            - daily_goal: Target goal
            - progress_percentage: Percentage of goal completed (0-100)
            - exceeded: Boolean indicating if goal was exceeded
            - message: Motivational message based on progress
        """
        today_date_str = datetime.now().strftime("%Y-%m-%d")

        # Aggregate points for today
        daily_aggregated = ActivityLogger.aggregate_daily_activities(activities_today)
        accumulated_score = daily_aggregated.get(today_date_str, 0)

        # Calculate percentage (capped at 100 for display, but track if exceeded)
        raw_percentage = (accumulated_score / daily_goal) * 100 if daily_goal > 0 else 0
        progress_percentage = min(100, raw_percentage)
        exceeded = accumulated_score > daily_goal

        # Generate motivational message
        message = ActivityLogger._get_motivational_message(
            accumulated_score,
            daily_goal,
            progress_percentage
        )

        return {
            "date": today_date_str,
            "accumulated_score": accumulated_score,
            "daily_goal": daily_goal,
            "progress_percentage": round(progress_percentage, 1),
            "exceeded": exceeded,
            "message": message
        }

    @staticmethod
    def _get_motivational_message(score: int, goal: int, percentage: float) -> str:
        """
        Generate motivational message based on current progress.

        Args:
            score: Current accumulated score
            goal: Daily goal
            percentage: Progress percentage

        Returns:
            Motivational message string
        """
        remaining = max(0, goal - score)

        if score == 0:
            return "🌟 Ready to start your learning journey today?"
        elif percentage < 25:
            return f"💪 Great start! {remaining} points to reach your goal!"
        elif percentage < 50:
            return f"🎯 You're making progress! {remaining} points to go!"
        elif percentage < 75:
            return f"🔥 Halfway there! Keep the momentum going!"
        elif percentage < 100:
            return f"⭐ Almost done! Just {remaining} points left!"
        elif score == goal:
            return "🎉 Perfect! You've reached your daily goal!"
        else:
            over = score - goal
            return f"🌟 Amazing! You exceeded your goal by {over} points!"
