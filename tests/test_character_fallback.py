#!/usr/bin/env python3
"""
Test script for character fallback encoding and decoding system.

This script tests the ability of the encoder and decoder to handle individual
characters and character sequences using the character fallback system.
"""

import sys
from encode import encode
from decode import decode

def test_individual_characters():
    """Test encoding and decoding of individual characters."""
    print("Testing individual characters:")
    print("-" * 50)
    
    # Test uppercase letters
    uppercase_letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for letter in uppercase_letters:
        encoded = encode(letter)
        decoded = decode(encoded)
        status = "✓" if decoded == letter else "✗"
        print(f"{letter} → {encoded} → {decoded} {status}")
    
    print()
    
    # Test lowercase letters
    lowercase_letters = 'abcdefghijklmnopqrstuvwxyz'
    for letter in lowercase_letters:
        encoded = encode(letter)
        decoded = decode(encoded)
        status = "✓" if decoded == letter else "✗"
        print(f"{letter} → {encoded} → {decoded} {status}")
    
    print()
    
    # Test digits
    digits = '0123456789'
    for digit in digits:
        encoded = encode(digit)
        decoded = decode(encoded)
        status = "✓" if decoded == digit else "✗"
        print(f"{digit} → {encoded} → {decoded} {status}")

def test_character_sequences():
    """Test encoding and decoding of character sequences."""
    print("\nTesting character sequences:")
    print("-" * 50)
    
    test_sequences = [
        "ABC",
        "abc", 
        "123",
        "XYZ",
        "xyz",
        "G",     # Previously problematic
        "g",     # Previously problematic
        "Hello", # Should use character fallback for letters not recognized as words
        "HELLO", # All caps
        "Test123", # Mixed letters and numbers
        "ABC123xyz", # Complex mixed sequence
    ]
    
    for sequence in test_sequences:
        encoded = encode(sequence)
        decoded = decode(encoded)
        status = "✓" if decoded == sequence else "✗"
        print(f"{sequence} → {encoded} → {decoded} {status}")

def test_meaningful_words():
    """Test that meaningful words like 'I' and 'a' still work correctly."""
    print("\nTesting meaningful words:")
    print("-" * 50)
    
    meaningful_words = ["I", "a", "A"]
    
    for word in meaningful_words:
        encoded = encode(word)
        decoded = decode(encoded)
        status = "✓" if decoded == word else "✗"
        print(f"{word} → {encoded} → {decoded} {status}")

def run_comprehensive_test():
    """Run comprehensive tests and report summary."""
    print("=" * 60)
    print("COMPREHENSIVE CHARACTER FALLBACK TEST")
    print("=" * 60)
    
    # Track success/failure counts
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    # Test all uppercase letters
    print("\n1. Testing uppercase letters A-Z:")
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        encoded = encode(letter)
        decoded = decode(encoded)
        total_tests += 1
        if decoded == letter:
            passed_tests += 1
            print(f"  {letter}: ✓")
        else:
            failed_tests.append(letter)
            print(f"  {letter}: ✗ (got '{decoded}', expected '{letter}')")
    
    # Test all lowercase letters  
    print("\n2. Testing lowercase letters a-z:")
    for letter in 'abcdefghijklmnopqrstuvwxyz':
        encoded = encode(letter)
        decoded = decode(encoded)
        total_tests += 1
        if decoded == letter:
            passed_tests += 1
            print(f"  {letter}: ✓")
        else:
            failed_tests.append(letter)
            print(f"  {letter}: ✗ (got '{decoded}', expected '{letter}')")
    
    # Test all digits
    print("\n3. Testing digits 0-9:")
    for digit in '0123456789':
        encoded = encode(digit)
        decoded = decode(encoded)
        total_tests += 1
        if decoded == digit:
            passed_tests += 1
            print(f"  {digit}: ✓")
        else:
            failed_tests.append(digit)
            print(f"  {digit}: ✗ (got '{decoded}', expected '{digit}')")
    
    # Test sequences
    print("\n4. Testing character sequences:")
    sequences = ["ABC", "abc", "123", "XYZ", "xyz", "Hello", "Test123"]
    for seq in sequences:
        encoded = encode(seq)
        decoded = decode(seq)
        total_tests += 1
        if decoded == seq:
            passed_tests += 1
            print(f"  {seq}: ✓")
        else:
            failed_tests.append(seq)
            print(f"  {seq}: ✗ (got '{decoded}', expected '{seq}')")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {passed_tests/total_tests*100:.1f}%")
    
    if failed_tests:
        print(f"\nFailed tests: {', '.join(str(x) for x in failed_tests)}")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--comprehensive":
        success = run_comprehensive_test()
        sys.exit(0 if success else 1)
    else:
        test_individual_characters()
        test_character_sequences()
        test_meaningful_words()
