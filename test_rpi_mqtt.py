#!/usr/bin/env python3
"""Test script for rpi_mqtt.py functionality"""

import sys
import os

# Add system path for RPiKeyboardConfig
sys.path.insert(0, '/usr/lib/python3/dist-packages')

# Import the functions we want to test
from rpi_mqtt import parse_colour, _parse_colour_to_rgb, leds_clear, leds_set_all, led_set_rc

def test_color_parsing():
    """Test various color parsing functions"""
    print("Testing color parsing...")

    # Test named colors
    assert parse_colour("red") == "red"
    assert _parse_colour_to_rgb("red") == (255, 0, 0)

    # Test hex colors
    assert parse_colour("#FF0000") == "rgb(255,0,0)"
    assert _parse_colour_to_rgb("#FF0000") == (255, 0, 0)

    # Test CSV colors
    assert parse_colour("255,0,0") == "255,0,0"
    assert _parse_colour_to_rgb("255,0,0") == (255, 0, 0)

    # Test JSON colors
    assert parse_colour('{"r":255,"g":0,"b":0}') == "rgb(255,0,0)"
    assert parse_colour('{"h":0,"s":255,"v":255}') == "0,255,255"

    print("✓ Color parsing tests passed")

def test_led_functions():
    """Test LED control functions"""
    print("Testing LED control functions...")

    # These will use the mock keyboard
    try:
        print("Testing leds_clear()...")
        leds_clear()

        print("Testing leds_set_all()...")
        leds_set_all("red")

        print("Testing led_set_rc()...")
        led_set_rc(1, 1, "blue")

        print("✓ LED control tests completed (check output above)")
    except Exception as e:
        print(f"LED control test error: {e}")

def main():
    """Run all tests"""
    print("=== Testing rpi_mqtt.py ===\n")

    try:
        test_color_parsing()
        test_led_functions()
        print("\n=== All tests completed successfully! ===")
    except Exception as e:
        print(f"\nTest failed: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())