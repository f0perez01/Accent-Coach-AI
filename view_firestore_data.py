"""
Script to view and analyze Firestore data.
Shows what's currently stored in the database.
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import streamlit as st
from auth_manager import AuthManager
from datetime import datetime

def view_firestore_data():
    """Display all data stored in Firestore collections."""

    print("Firestore Data Viewer")
    print("=" * 60)

    # Initialize
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

    # Collections to check
    collections = {
        "pronunciation_analyses": ["user_id", "reference_text", "timestamp"],
        "conversation_turns": ["session_id", "user_transcript", "timestamp"],
        "writing_evaluations": ["user_id", "original_text", "timestamp"],
        "user_activities": ["user_id", "activity_type", "timestamp"],
    }

    for collection_name, fields in collections.items():
        print(f"\n{collection_name.upper()}")
        print("-" * 60)

        try:
            docs = db.collection(collection_name).limit(10).stream()
            doc_list = list(docs)

            if not doc_list:
                print(f"  No documents found in {collection_name}")
                continue

            print(f"  Total documents (showing first 10): {len(doc_list)}")

            for i, doc in enumerate(doc_list, 1):
                data = doc.to_dict()
                print(f"\n  Document {i} (ID: {doc.id}):")

                for field in fields:
                    value = data.get(field, "N/A")
                    if isinstance(value, datetime):
                        value = value.strftime("%Y-%m-%d %H:%M:%S")
                    print(f"    - {field}: {value}")

                # Show additional interesting fields
                if collection_name == "pronunciation_analyses":
                    if "metrics" in data:
                        metrics = data["metrics"]
                        print(f"    - word_accuracy: {metrics.get('word_accuracy', 'N/A')}")
                        print(f"    - phoneme_accuracy: {metrics.get('phoneme_accuracy', 'N/A')}")

                if collection_name == "user_activities":
                    if "score" in data:
                        print(f"    - score: {data.get('score', 'N/A')}")

        except Exception as e:
            print(f"  [ERROR] Could not read {collection_name}: {e}")

    print("\n" + "=" * 60)
    print("Data view complete!")

if __name__ == "__main__":
    view_firestore_data()
