#!/usr/bin/env python3
"""
Quick test script for Advanced Settings component

Run this to verify the component works correctly.
"""

import sys
sys.path.insert(0, '/Users/fantperezc/diplomado/Accent-Coach-AI')

from accent_coach.presentation.components.settings import AdvancedSettings

def test_advanced_settings():
    """Test AdvancedSettings component."""
    print("🧪 Testing AdvancedSettings Component")
    print("=" * 50)
    
    # Test 1: Default config
    print("\n1️⃣ Testing default configuration...")
    default_config = AdvancedSettings._get_default_config()
    print(f"✓ Default config keys: {list(default_config.keys())}")
    print(f"✓ Default model: {default_config['model_name']}")
    print(f"✓ Use G2P: {default_config['use_g2p']}")
    print(f"✓ Use LLM: {default_config['use_llm']}")
    print(f"✓ Language: {default_config['lang']}")
    print(f"✓ Enhancement enabled: {default_config['enable_enhancement']}")
    
    # Test 2: Model options
    print("\n2️⃣ Testing model options...")
    print(f"✓ Available models: {len(AdvancedSettings.MODEL_OPTIONS)}")
    for label, model_name in AdvancedSettings.MODEL_OPTIONS.items():
        print(f"  - {label}: {model_name}")
    
    # Test 3: Model display names
    print("\n3️⃣ Testing model display names...")
    for model_name in AdvancedSettings.MODEL_OPTIONS.values():
        display_name = AdvancedSettings.get_model_display_name(model_name)
        print(f"✓ {model_name.split('/')[-1]} → {display_name}")
    
    # Test 4: Language options
    print("\n4️⃣ Testing language options...")
    print(f"✓ Available languages: {AdvancedSettings.LANGUAGE_OPTIONS}")
    
    # Test 5: Model label retrieval
    print("\n5️⃣ Testing model label retrieval...")
    test_model = 'facebook/wav2vec2-base-960h'
    label = AdvancedSettings._get_model_label(test_model)
    print(f"✓ Model '{test_model}' → Label: '{label}'")
    
    print("\n" + "=" * 50)
    print("✅ All tests passed!")
    print("\n💡 Next steps:")
    print("   1. Run: streamlit run accent_coach/presentation/streamlit_app.py")
    print("   2. Log in to the application")
    print("   3. Check sidebar for '⚙️ Advanced Settings' expander")
    print("   4. Test each setting and verify it persists across tabs")
    print("   5. Verify selected model is used in pronunciation analysis")

if __name__ == "__main__":
    test_advanced_settings()
