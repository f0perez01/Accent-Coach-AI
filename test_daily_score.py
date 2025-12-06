"""
Test script to verify daily score calculation works correctly.
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import streamlit as st
from datetime import datetime
from accent_coach.infrastructure.persistence import FirestoreActivityRepository
from auth_manager import AuthManager
from activity_logger import ActivityLogger

def test_daily_score():
    """Test daily score retrieval and calculation."""

    print("Testing Daily Score Calculation...")
    print("=" * 60)

    # Initialize Firestore
    try:
        auth_manager = AuthManager(st.secrets if hasattr(st, 'secrets') else None)
        auth_manager.init_firebase()
        db = auth_manager.get_db()

        if not db:
            print("[ERROR] Could not connect to Firestore")
            return

        print("[OK] Connected to Firestore\n")

    except Exception as e:
        print(f"[ERROR] Failed to initialize: {e}")
        return

    # Initialize repository
    activity_repo = FirestoreActivityRepository(db)

    # Test with actual user data
    user_id = "NCLn6ipXOISbWza0CYauqGuuFjn2"  # From view_firestore_data.py
    today = datetime.now()

    print(f"User ID: {user_id}")
    print(f"Date: {today.strftime('%Y-%m-%d')}\n")

    # Get today's activities
    try:
        activities = activity_repo.get_today_activities(user_id, today)
        print(f"[OK] Retrieved {len(activities)} activities for today")

        if activities:
            print("\nActivity Details:")
            for i, activity in enumerate(activities, 1):
                print(f"  {i}. Type: {activity.get('activity_type')}")
                print(f"     Weight: {activity.get('weight', 0)}")
                print(f"     Date: {activity.get('date')}")
                print(f"     Timestamp: {activity.get('timestamp')}")
        else:
            print("  No activities found for today")

    except Exception as e:
        print(f"[ERROR] Failed to get activities: {e}")
        return

    # Calculate daily score
    try:
        progress_data = ActivityLogger.get_daily_score_and_progress(
            activities_today=activities,
            daily_goal=100
        )

        print("\n" + "=" * 60)
        print("DAILY SCORE CALCULATION")
        print("=" * 60)
        print(f"Date: {progress_data['date']}")
        print(f"Accumulated Score: {progress_data['accumulated_score']}")
        print(f"Daily Goal: {progress_data['daily_goal']}")
        print(f"Progress: {progress_data['progress_percentage']}%")
        print(f"Goal Exceeded: {progress_data['exceeded']}")
        print(f"\nMessage: {progress_data['message']}")
        print("=" * 60)

        if progress_data['accumulated_score'] > 0:
            print("\n[SUCCESS] Daily score calculation is working!")
        else:
            print("\n[WARNING] No score accumulated for today")

    except Exception as e:
        print(f"[ERROR] Failed to calculate daily score: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_daily_score()
