"""
Quick script to verify Firestore connection and data persistence.
Run this to check if data is being saved correctly.
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import streamlit as st
from auth_manager import AuthManager
from datetime import datetime

def test_firestore_connection():
    """Test Firestore connection and basic operations."""

    print("Testing Firestore Connection...")
    print("-" * 50)

    # Initialize AuthManager
    try:
        auth_manager = AuthManager(st.secrets if hasattr(st, 'secrets') else None)
        auth_manager.init_firebase()
        db = auth_manager.get_db()

        if not db:
            print("[FAIL] Firestore client is None")
            print("   Check if Firebase is properly initialized")
            return False

        print("[PASS] Firestore client initialized successfully")

    except Exception as e:
        print(f"[FAIL] Could not initialize Firestore: {e}")
        return False

    # Test write operation
    try:
        test_collection = "test_connection"
        test_doc = {
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "message": "Testing Firestore connection"
        }

        doc_ref = db.collection(test_collection).document("test_doc")
        doc_ref.set(test_doc)
        print("[PASS] Write test successful")

    except Exception as e:
        print(f"[FAIL] Could not write to Firestore: {e}")
        return False

    # Test read operation
    try:
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            print(f"[PASS] Read test successful: {data.get('message')}")
        else:
            print("[FAIL] Document not found after writing")
            return False

    except Exception as e:
        print(f"[FAIL] Could not read from Firestore: {e}")
        return False

    # Clean up test document
    try:
        doc_ref.delete()
        print("[PASS] Cleanup successful")
    except Exception as e:
        print(f"[WARN] Could not delete test document: {e}")

    # Check existing collections
    try:
        print("\nChecking existing collections...")
        collections_to_check = [
            "pronunciation_analyses",
            "conversation_turns",
            "writing_evaluations",
            "user_activities"
        ]

        for collection_name in collections_to_check:
            docs = db.collection(collection_name).limit(5).stream()
            count = sum(1 for _ in docs)
            print(f"   - {collection_name}: {count} documents (showing first 5)")

    except Exception as e:
        print(f"[WARN] Could not list collections: {e}")

    print("-" * 50)
    print("[SUCCESS] ALL TESTS PASSED - Firestore is working correctly!")
    return True

if __name__ == "__main__":
    test_firestore_connection()
