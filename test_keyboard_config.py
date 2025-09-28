#!/usr/bin/env python3
"""
Test script for RPi Keyboard Config library
Tests basic import and functionality
"""

import sys
import traceback

def test_import():
    """Test if the RPiKeyboardConfig module can be imported"""
    try:
        from RPiKeyboardConfig import RPiKeyboardConfig
        print("✓ Successfully imported RPiKeyboardConfig")
        return True
    except ImportError as e:
        print(f"✗ Failed to import RPiKeyboardConfig: {e}")
        return False

def test_keyboard_detection():
    """Test keyboard detection and basic info"""
    try:
        from RPiKeyboardConfig import RPiKeyboardConfig

        print("\nTesting keyboard detection...")
        keyboard = RPiKeyboardConfig()

        # Get basic keyboard information
        print(f"✓ Keyboard initialized successfully")

        # Try to get model info (may fail if no keyboard connected)
        try:
            model = keyboard.model
            variant = keyboard.variant
            print(f"✓ Model: {model}")
            print(f"✓ Variant: {variant}")
        except Exception as e:
            print(f"⚠ Could not get keyboard info (keyboard may not be connected): {e}")

        return True

    except Exception as e:
        print(f"✗ Keyboard detection failed: {e}")
        traceback.print_exc()
        return False

def test_available_methods():
    """Test what methods are available in the library"""
    try:
        from RPiKeyboardConfig import RPiKeyboardConfig

        print("\nAvailable methods in RPiKeyboardConfig:")
        keyboard = RPiKeyboardConfig()
        methods = [method for method in dir(keyboard) if not method.startswith('_')]

        for method in sorted(methods):
            print(f"  - {method}")

        return True

    except Exception as e:
        print(f"✗ Failed to list methods: {e}")
        return False

def main():
    """Main test function"""
    print("RPi Keyboard Config Library Test")
    print("=" * 40)

    # Test 1: Import
    import_success = test_import()

    if not import_success:
        print("\n❌ Basic import failed. Cannot proceed with further tests.")
        return False

    # Test 2: Keyboard detection
    detection_success = test_keyboard_detection()

    # Test 3: Available methods
    methods_success = test_available_methods()

    print("\n" + "=" * 40)
    print("Test Summary:")
    print(f"  Import: {'✓' if import_success else '✗'}")
    print(f"  Detection: {'✓' if detection_success else '✗'}")
    print(f"  Methods: {'✓' if methods_success else '✗'}")

    if import_success and detection_success and methods_success:
        print("\n🎉 All tests passed! Library is working.")
        return True
    else:
        print("\n⚠ Some tests failed. Check output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)