#!/usr/bin/env python3
"""
Comprehensive test script for all character encoding and decoding.

This script tests every letter, digit, and common character to ensure
the fallback system works correctly with the regional indicator emojis.
"""

import sys, os


# Add parent directory to path to import encode/decode modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from encode import encode
from decode import decode

def test_all_letters():
    """Test all uppercase and lowercase letters."""
    print("Testing all letters:")
    print("=" * 60)
    
    failed_tests = []
    passed_tests = 0
    total_tests = 0
    
    # Test uppercase letters A-Z
    print("\nUppercase letters:")
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        try:
            encoded = encode(letter)
            decoded = decode(encoded)
            total_tests += 1
            
            if decoded == letter:
                passed_tests += 1
                print(f"  {letter}: {encoded} → {decoded} ✓")
            else:
                failed_tests.append((letter, decoded, encoded))
                print(f"  {letter}: {encoded} → {decoded} ✗ (expected '{letter}')")
        except Exception as e:
            failed_tests.append((letter, f"ERROR: {e}", ""))
            print(f"  {letter}: ERROR - {e}")
            total_tests += 1
    
    # Test lowercase letters a-z
    print("\nLowercase letters:")
    for letter in 'abcdefghijklmnopqrstuvwxyz':
        try:
            encoded = encode(letter)
            decoded = decode(encoded)
            total_tests += 1
            
            if decoded == letter:
                passed_tests += 1
                print(f"  {letter}: {encoded} → {decoded} ✓")
            else:
                failed_tests.append((letter, decoded, encoded))
                print(f"  {letter}: {encoded} → {decoded} ✗ (expected '{letter}')")
        except Exception as e:
            failed_tests.append((letter, f"ERROR: {e}", ""))
            print(f"  {letter}: ERROR - {e}")
            total_tests += 1
    
    return passed_tests, total_tests, failed_tests

def test_all_digits():
    """Test all digits 0-9."""
    print("\n\nTesting all digits:")
    print("=" * 60)
    
    failed_tests = []
    passed_tests = 0
    total_tests = 0
    
    for digit in '0123456789':
        try:
            encoded = encode(digit)
            decoded = decode(encoded)
            total_tests += 1
            
            if decoded == digit:
                passed_tests += 1
                print(f"  {digit}: {encoded} → {decoded} ✓")
            else:
                failed_tests.append((digit, decoded, encoded))
                print(f"  {digit}: {encoded} → {decoded} ✗ (expected '{digit}')")
        except Exception as e:
            failed_tests.append((digit, f"ERROR: {e}", ""))
            print(f"  {digit}: ERROR - {e}")
            total_tests += 1
    
    return passed_tests, total_tests, failed_tests

def test_character_sequences():
    """Test various character sequences."""
    print("\n\nTesting character sequences:")
    print("=" * 60)
    
    test_sequences = [
        "ABC",      # Simple uppercase
        "abc",      # Simple lowercase
        "XYZ",      # End of alphabet
        "xyz",      # End of alphabet lowercase
        "123",      # Simple digits
        "G",        # Previously problematic letter
        "g",        # Previously problematic letter
        "Hello",    # Mixed case word
        "HELLO",    # All uppercase
        "test",     # All lowercase
        "Test123",  # Mixed letters and digits
        "ABC123xyz",# Complex mixed
        "A1B2C3",   # Alternating letters/digits
    ]
    
    failed_tests = []
    passed_tests = 0
    total_tests = 0
    
    for sequence in test_sequences:
        try:
            encoded = encode(sequence)
            decoded = decode(encoded)
            total_tests += 1
            
            if decoded == sequence:
                passed_tests += 1
                print(f"  {sequence}: {encoded} → {decoded} ✓")
            else:
                failed_tests.append((sequence, decoded, encoded))
                print(f"  {sequence}: {encoded} → {decoded} ✗ (expected '{sequence}')")
        except Exception as e:
            failed_tests.append((sequence, f"ERROR: {e}", ""))
            print(f"  {sequence}: ERROR - {e}")
            total_tests += 1
    
    return passed_tests, total_tests, failed_tests

def test_special_words():
    """Test words that should still use word mappings."""
    print("\n\nTesting special meaningful words:")
    print("=" * 60)
    
    special_words = ["I", "a", "A"]
    
    failed_tests = []
    passed_tests = 0
    total_tests = 0
    
    for word in special_words:
        try:
            encoded = encode(word)
            decoded = decode(encoded)
            total_tests += 1
            
            if decoded == word:
                passed_tests += 1
                print(f"  {word}: {encoded} → {decoded} ✓")
            else:
                failed_tests.append((word, decoded, encoded))
                print(f"  {word}: {encoded} → {decoded} ✗ (expected '{word}')")
        except Exception as e:
            failed_tests.append((word, f"ERROR: {e}", ""))
            print(f"  {word}: ERROR - {e}")
            total_tests += 1
    
    return passed_tests, total_tests, failed_tests

def show_emoji_mappings():
    """Show what emojis are being used for character fallback."""
    print("\n\nCharacter fallback emoji mappings:")
    print("=" * 60)
    
    print("\nLetters (using regional indicators):")
    for letter in 'abcdefghijklmnopqrstuvwxyz':
        try:
            encoded = encode(letter)
            print(f"  {letter} → {encoded}")
        except Exception as e:
            print(f"  {letter} → ERROR: {e}")
    
    print("\nDigits (using number emojis):")
    for digit in '0123456789':
        try:
            encoded = encode(digit)
            print(f"  {digit} → {encoded}")
        except Exception as e:
            print(f"  {digit} → ERROR: {e}")

def main():
    """Run all character tests and show summary."""
    print("COMPREHENSIVE CHARACTER ENCODING/DECODING TEST")
    print("=" * 60)
    
    # Run all test categories
    letter_passed, letter_total, letter_failed = test_all_letters()
    digit_passed, digit_total, digit_failed = test_all_digits()
    seq_passed, seq_total, seq_failed = test_character_sequences()
    word_passed, word_total, word_failed = test_special_words()
    
    # Show emoji mappings
    show_emoji_mappings()
    
    # Calculate totals
    total_passed = letter_passed + digit_passed + seq_passed + word_passed
    total_tests = letter_total + digit_total + seq_total + word_total
    total_failed = letter_failed + digit_failed + seq_failed + word_failed
    
    # Print final summary
    print("\n\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Total tests run: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_tests - total_passed}")
    print(f"Success rate: {total_passed/total_tests*100:.1f}%")
    
    if total_failed:
        print(f"\nFailed test breakdown:")
        print(f"  Letters: {len(letter_failed)}")
        print(f"  Digits: {len(digit_failed)}")
        print(f"  Sequences: {len(seq_failed)}")
        print(f"  Special words: {len(word_failed)}")
        
        print(f"\nFirst few failures:")
        all_failures = letter_failed + digit_failed + seq_failed + word_failed
        for i, (input_val, output, encoded) in enumerate(all_failures[:10]):
            print(f"  {input_val} → {encoded} → {output}")
        
        if len(all_failures) > 10:
            print(f"  ... and {len(all_failures) - 10} more")
    
    # Return success status
    return total_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
