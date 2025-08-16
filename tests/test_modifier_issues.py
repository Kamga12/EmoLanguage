#!/usr/bin/env python3

import sys
import os

# Add the current directory to the Python path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from encode import encode
from decode import decode

def test_word_modifiers(word):
    """Test encoding and decoding of a word, showing detailed information."""
    print(f"\n=== Testing: '{word}' ===")
    
    # Initial encoding
    encoded = encode(word)
    print(f"Original: '{word}'")
    print(f"Encoded:  {encoded}")
    
    # Initial decoding
    decoded = decode(encoded)
    print(f"Decoded:  '{decoded}'")
    
    # Check if round-trip is successful
    if word == decoded:
        print("✅ Round-trip successful")
    else:
        print(f"❌ Round-trip failed: '{word}' != '{decoded}'")
    
    # Test multiple cycles
    print("\n--- Testing multiple cycles ---")
    current = word
    for cycle in range(1, 4):
        encoded = encode(current)
        decoded = decode(encoded)
        print(f"Cycle {cycle}: '{current}' -> {encoded} -> '{decoded}'")
        
        if current != decoded:
            print(f"❌ Cycle {cycle} failed: '{current}' != '{decoded}'")
            break
        current = decoded
    else:
        print("✅ All cycles successful")
    
    return encoded, decoded

def main():
    test_words = [
        "hidden",
        "Sincerely",
        "Administrative Manager",
        "Administrative",
        "Manager"
    ]
    
    for word in test_words:
        test_word_modifiers(word)
        print("-" * 50)

if __name__ == "__main__":
    main()
