#!/usr/bin/env python3
"""
Test script for IPA Guide Component
Validates:
- All filter categories work correctly
- Symbols are displayed properly
- Correct number of symbols per category
"""

from ipa_definitions import IPADefinitionsManager


def test_ipa_guide_component():
    """Test IPA Guide Component functionality."""
    print("=" * 70)
    print("🧪 Testing IPA Guide Component")
    print("=" * 70)
    
    # Test 1: Get all symbols
    print("\n" + "-" * 70)
    print("Test 1: Get All Symbols")
    print("-" * 70)
    all_symbols = IPADefinitionsManager.get_all_definitions()
    print(f"✓ Total symbols: {len(all_symbols)}")
    print(f"  Sample: {list(all_symbols.items())[:3]}")
    
    # Test 2: Get vowels
    print("\n" + "-" * 70)
    print("Test 2: Get Vowels")
    print("-" * 70)
    vowels = IPADefinitionsManager.get_vowels()
    print(f"✓ Total vowels: {len(vowels)}")
    print("  Vowels:")
    for symbol, definition in list(vowels.items())[:5]:
        print(f"    {symbol}: {definition}")
    
    # Test 3: Get diphthongs
    print("\n" + "-" * 70)
    print("Test 3: Get Diphthongs")
    print("-" * 70)
    diphthongs = IPADefinitionsManager.get_diphthongs()
    print(f"✓ Total diphthongs: {len(diphthongs)}")
    print("  Diphthongs:")
    for symbol, definition in diphthongs.items():
        print(f"    {symbol}: {definition}")
    
    # Test 4: Get consonants
    print("\n" + "-" * 70)
    print("Test 4: Get Consonants")
    print("-" * 70)
    consonants = IPADefinitionsManager.get_consonants()
    print(f"✓ Total consonants: {len(consonants)}")
    print("  Consonants:")
    for symbol, definition in list(consonants.items())[:5]:
        print(f"    {symbol}: {definition}")
    
    # Test 5: Get specific definition
    print("\n" + "-" * 70)
    print("Test 5: Get Specific Definition")
    print("-" * 70)
    test_symbols = ["ə", "θ", "aɪ", "ŋ"]
    for symbol in test_symbols:
        definition = IPADefinitionsManager.get_definition(symbol)
        if definition:
            print(f"  ✓ {symbol}: {definition}")
        else:
            print(f"  ✗ {symbol}: Not found")
    
    # Test 6: Validate category counts
    print("\n" + "-" * 70)
    print("Test 6: Validate Category Counts")
    print("-" * 70)
    
    total_categorized = len(vowels) + len(diphthongs) + len(consonants) + 2  # +2 for stress markers
    print(f"  Vowels: {len(vowels)}")
    print(f"  Diphthongs: {len(diphthongs)}")
    print(f"  Consonants: {len(consonants)}")
    print(f"  Stress markers: 2")
    print(f"  Total categorized: {total_categorized}")
    print(f"  Total in definitions: {len(all_symbols)}")
    
    if total_categorized == len(all_symbols):
        print(f"  ✓ All symbols are categorized!")
    else:
        print(f"  ⚠️  {len(all_symbols) - total_categorized} symbols may be uncategorized")
    
    # Test 7: Validate no duplicates across categories
    print("\n" + "-" * 70)
    print("Test 7: Check for Duplicate Symbols")
    print("-" * 70)
    
    vowel_set = set(vowels.keys())
    diphthong_set = set(diphthongs.keys())
    consonant_set = set(consonants.keys())
    
    overlap_vd = vowel_set & diphthong_set
    overlap_vc = vowel_set & consonant_set
    overlap_dc = diphthong_set & consonant_set
    
    if not (overlap_vd or overlap_vc or overlap_dc):
        print("  ✓ No duplicates found across categories")
    else:
        if overlap_vd:
            print(f"  ⚠️  Vowels & Diphthongs overlap: {overlap_vd}")
        if overlap_vc:
            print(f"  ⚠️  Vowels & Consonants overlap: {overlap_vc}")
        if overlap_dc:
            print(f"  ⚠️  Diphthongs & Consonants overlap: {overlap_dc}")
    
    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)
    
    # Summary table
    print("\n📊 Summary:")
    print(f"  Total Symbols: {len(all_symbols)}")
    print(f"  Categories:")
    print(f"    - Vowels: {len(vowels)}")
    print(f"    - Diphthongs: {len(diphthongs)}")
    print(f"    - Consonants: {len(consonants)}")
    print(f"    - Stress Markers: 2")


if __name__ == "__main__":
    test_ipa_guide_component()
