#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick setup test script
Verifies all dependencies are installed correctly
"""

import sys

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    errors = []

    tests = [
        ("streamlit", "Streamlit"),
        ("torch", "PyTorch"),
        ("transformers", "Transformers"),
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
        ("plotly", "Plotly"),
        ("gruut", "Gruut"),
        ("sequence_align", "Sequence Align"),
        ("groq", "Groq"),
        ("librosa", "Librosa"),
        ("soundfile", "SoundFile"),
    ]

    for module, name in tests:
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError as e:
            print(f"✗ {name} - {e}")
            errors.append(name)

    return errors

def test_torch():
    """Test PyTorch setup"""
    print("\nTesting PyTorch...")
    try:
        import torch
        print(f"✓ PyTorch version: {torch.__version__}")
        print(f"✓ CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"✓ CUDA version: {torch.version.cuda}")
            print(f"✓ Device: {torch.cuda.get_device_name(0)}")
        else:
            print("ℹ Running on CPU (CUDA not available)")
        return True
    except Exception as e:
        print(f"✗ PyTorch test failed: {e}")
        return False

def test_transformers():
    """Test Transformers library"""
    print("\nTesting Transformers...")
    try:
        from transformers import AutoProcessor
        print("✓ Transformers AutoProcessor available")
        return True
    except Exception as e:
        print(f"✗ Transformers test failed: {e}")
        return False

def test_gruut():
    """Test Gruut"""
    print("\nTesting Gruut...")
    try:
        from gruut import sentences
        test_text = "Hello world"
        result = list(sentences(test_text, lang="en-us"))
        print(f"✓ Gruut working (processed: '{test_text}')")
        return True
    except Exception as e:
        print(f"✗ Gruut test failed: {e}")
        return False

def check_api_keys():
    """Check API keys"""
    print("\nChecking API keys...")
    import os

    groq_key = os.environ.get("GROQ_API_KEY")
    hf_token = os.environ.get("HF_API_TOKEN")

    if groq_key:
        print(f"✓ GROQ_API_KEY found ({groq_key[:10]}...)")
    else:
        print("⚠ GROQ_API_KEY not found (LLM feedback will be disabled)")

    if hf_token:
        print(f"✓ HF_API_TOKEN found ({hf_token[:10]}...)")
    else:
        print("ℹ HF_API_TOKEN not found (optional, only needed for private models)")

def main():
    print("=" * 60)
    print("Accent Coach AI - Setup Test")
    print("=" * 60)

    # Test imports
    errors = test_imports()

    if errors:
        print(f"\n⚠ Missing dependencies: {', '.join(errors)}")
        print("\nInstall missing dependencies with:")
        print("pip install -r requirements.txt")
        return 1

    # Test PyTorch
    test_torch()

    # Test Transformers
    test_transformers()

    # Test Gruut
    test_gruut()

    # Check API keys
    check_api_keys()

    print("\n" + "=" * 60)
    print("✓ Setup test complete!")
    print("=" * 60)
    print("\nYou can now run the app with:")
    print("streamlit run app.py")
    print("\nMake sure to configure your API keys in .streamlit/secrets.toml")

    return 0

if __name__ == "__main__":
    sys.exit(main())
