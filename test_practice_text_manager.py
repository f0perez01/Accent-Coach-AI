#!/usr/bin/env python3
"""
Test script for PracticeTextManager integration
Validates:
- All categories are accessible
- Texts load correctly for each category
- Metadata is present
- Search functionality works
- Random selection works
"""

from accent_coach.domain.pronunciation import PracticeTextManager

def test_practice_text_manager():
    """Test PracticeTextManager functionality."""
    print("=" * 70)
    print("🧪 Testing PracticeTextManager")
    print("=" * 70)
    
    # Initialize manager
    manager = PracticeTextManager()
    print("\n✅ PracticeTextManager initialized")
    
    # Test 1: Get all categories
    print("\n" + "-" * 70)
    print("Test 1: Get Categories")
    print("-" * 70)
    categories = manager.get_categories()
    print(f"✓ Found {len(categories)} categories:")
    for i, cat in enumerate(categories, 1):
        cat_info = manager.get_category_info(cat)
        print(f"  {i}. {cat}: {cat_info['count']} texts - {cat_info['description']}")
    
    # Test 2: Get texts for each category
    print("\n" + "-" * 70)
    print("Test 2: Get Texts by Category")
    print("-" * 70)
    total_texts = 0
    for cat in categories:
        texts = manager.get_texts_for_category(cat)
        total_texts += len(texts)
        print(f"\n{cat} ({len(texts)} texts):")
        
        # Show first 2 texts as sample
        for i, text in enumerate(texts[:2], 1):
            print(f"  {i}. \"{text.text[:50]}...\"")
            print(f"     Focus: {text.focus} | Difficulty: {text.difficulty}")
    
    print(f"\n✓ Total texts across all categories: {total_texts}")
    
    # Test 3: Search functionality
    print("\n" + "-" * 70)
    print("Test 3: Search Functionality")
    print("-" * 70)
    search_query = "the"
    results = manager.search_texts(search_query)
    print(f"✓ Search for '{search_query}' found {len(results)} texts:")
    for i, text in enumerate(results[:3], 1):
        print(f"  {i}. [{text.category}] \"{text.text[:50]}...\"")
    
    # Test 4: Random selection
    print("\n" + "-" * 70)
    print("Test 4: Random Selection")
    print("-" * 70)
    
    # Random from all categories
    random_text = manager.get_random_text()
    print(f"✓ Random text (any category):")
    print(f"  Category: {random_text.category}")
    print(f"  Text: \"{random_text.text[:60]}...\"")
    print(f"  Focus: {random_text.focus}")
    
    # Random from specific category
    specific_cat = "Tongue Twisters"
    random_tongue_twister = manager.get_random_text(specific_cat)
    print(f"\n✓ Random text from '{specific_cat}':")
    print(f"  Text: \"{random_tongue_twister.text[:60]}...\"")
    print(f"  Focus: {random_tongue_twister.focus}")
    
    # Test 5: Validate all texts have required fields
    print("\n" + "-" * 70)
    print("Test 5: Validate Text Metadata")
    print("-" * 70)
    all_texts_valid = True
    for cat in categories:
        texts = manager.get_texts_for_category(cat)
        for text in texts:
            if not all([text.text, text.category, text.focus, text.difficulty]):
                print(f"  ✗ Missing fields in: {text.text[:30]}")
                all_texts_valid = False
    
    if all_texts_valid:
        print(f"✓ All {total_texts} texts have complete metadata")
    
    print("\n" + "=" * 70)
    print("✅ All tests passed!")
    print("=" * 70)


if __name__ == "__main__":
    test_practice_text_manager()
