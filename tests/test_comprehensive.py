#!/usr/bin/env python3
"""
Comprehensive test suite for the character fallback encoding/decoding system.

This test suite identifies issues with character-level encoding and decoding,
including problems with capitalization handling and sequence processing.
"""

import sys
from encode import encode
from decode import decode

def test_individual_characters():
    """Test encoding and decoding of individual characters."""
    print("=" * 60)
    print("INDIVIDUAL CHARACTER TESTS")
    print("=" * 60)
    
    passed = 0
    failed = 0
    failures = []
    
    # Test uppercase letters
    print("\nUppercase letters:")
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        try:
            encoded = encode(letter)
            decoded = decode(encoded)
            
            if decoded == letter:
                print(f"  ✓ {letter}: {encoded} → {decoded}")
                passed += 1
            else:
                print(f"  ✗ {letter}: {encoded} → {decoded} (expected '{letter}')")
                failures.append((letter, encoded, decoded))
                failed += 1
        except Exception as e:
            print(f"  ✗ {letter}: ERROR - {e}")
            failures.append((letter, "ERROR", str(e)))
            failed += 1
    
    # Test lowercase letters
    print("\nLowercase letters:")
    for letter in 'abcdefghijklmnopqrstuvwxyz':
        try:
            encoded = encode(letter)
            decoded = decode(encoded)
            
            if decoded == letter:
                print(f"  ✓ {letter}: {encoded} → {decoded}")
                passed += 1
            else:
                print(f"  ✗ {letter}: {encoded} → {decoded} (expected '{letter}')")
                failures.append((letter, encoded, decoded))
                failed += 1
        except Exception as e:
            print(f"  ✗ {letter}: ERROR - {e}")
            failures.append((letter, "ERROR", str(e)))
            failed += 1
    
    # Test digits
    print("\nDigits:")
    for digit in '0123456789':
        try:
            encoded = encode(digit)
            decoded = decode(encoded)
            
            if decoded == digit:
                print(f"  ✓ {digit}: {encoded} → {decoded}")
                passed += 1
            else:
                print(f"  ✗ {digit}: {encoded} → {decoded} (expected '{digit}')")
                failures.append((digit, encoded, decoded))
                failed += 1
        except Exception as e:
            print(f"  ✗ {digit}: ERROR - {e}")
            failures.append((digit, "ERROR", str(e)))
            failed += 1
    
    print(f"\nIndividual Characters Summary: {passed} passed, {failed} failed")
    return passed, failed, failures

def test_character_sequences():
    """Test various character sequences."""
    print("\n" + "=" * 60)
    print("CHARACTER SEQUENCE TESTS")
    print("=" * 60)
    
    test_cases = [
        # Spaced sequences
        "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z",
        "a b c d e f g h i j k l m n o p q r s t u v w x y z", 
        "0 1 2 3 4 5 6 7 8 9",
        
        # Continuous sequences
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "abcdefghijklmnopqrstuvwxyz",
        "0123456789",
        
        # Mixed sequences
        "ABC123xyz",
        "Hello123World",
        "Test1234",
        "A1B2C3",
        
        # Problem cases from your example
        "G",
        "g", 
        "GG",
        "gg",
        
        # Single meaningful words that should use dictionary
        "I",
        "a", 
        "A",
    ]
    
    passed = 0
    failed = 0
    failures = []
    
    for test_input in test_cases:
        try:
            encoded = encode(test_input)
            decoded = decode(encoded)
            
            if decoded == test_input:
                print(f"✓ Sequence test:")
                print(f"  Input:   '{test_input}'")
                print(f"  Encoded: '{encoded}'")
                print(f"  Decoded: '{decoded}'")
                print()
                passed += 1
            else:
                print(f"✗ Sequence test:")
                print(f"  Input:   '{test_input}'")
                print(f"  Encoded: '{encoded}'")
                print(f"  Decoded: '{decoded}'")
                print(f"  ❌ MISMATCH!")
                print()
                failures.append((test_input, encoded, decoded))
                failed += 1
        except Exception as e:
            print(f"✗ Sequence test:")
            print(f"  Input:   '{test_input}'")
            print(f"  ERROR: {e}")
            print()
            failures.append((test_input, "ERROR", str(e)))
            failed += 1
    
    print(f"Character Sequences Summary: {passed} passed, {failed} failed")
    return passed, failed, failures

def test_problematic_cases():
    """Test specific problematic cases identified."""
    print("\n" + "=" * 60)
    print("PROBLEMATIC CASE ANALYSIS")
    print("=" * 60)
    
    # Test specific problem cases
    problem_cases = [
        ('G', "Letter G uppercase"),
        ('g', "Letter g lowercase"),
        ('ABC', "Simple uppercase sequence"),
        ('Hello', "Mixed case word"),
        ('HELLO', "All caps word"),
    ]
    
    for test_input, description in problem_cases:
        print(f"\nAnalyzing: {description}")
        print(f"Input: '{test_input}'")
        
        try:
            # Step by step analysis
            encoded = encode(test_input)
            print(f"Encoded: '{encoded}'")
            
            decoded = decode(encoded)
            print(f"Decoded: '{decoded}'")
            
            # Character by character analysis for sequences
            if len(test_input) > 1:
                print("Character-by-character analysis:")
                for i, char in enumerate(test_input):
                    char_encoded = encode(char)
                    char_decoded = decode(char_encoded)
                    status = "✓" if char_decoded == char else "✗"
                    print(f"  {char} → {char_encoded} → {char_decoded} {status}")
            
            # Overall result
            if decoded == test_input:
                print("✓ OVERALL: PASS")
            else:
                print("✗ OVERALL: FAIL")
                
        except Exception as e:
            print(f"ERROR: {e}")
        
        print("-" * 40)

def analyze_emoji_mappings():
    """Analyze what emojis are being used for encoding."""
    print("\n" + "=" * 60)
    print("EMOJI MAPPING ANALYSIS")
    print("=" * 60)
    
    print("\nCharacter Fallback Mappings (letters):")
    for letter in 'abcdefghijklmnopqrstuvwxyz':
        try:
            encoded = encode(letter)
            print(f"  {letter} → {encoded}")
        except Exception as e:
            print(f"  {letter} → ERROR: {e}")
    
    print("\nCapitalized letters:")
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        try:
            encoded = encode(letter)
            print(f"  {letter} → {encoded}")
        except Exception as e:
            print(f"  {letter} → ERROR: {e}")
    
    print("\nDigit mappings:")
    for digit in '0123456789':
        try:
            encoded = encode(digit)
            print(f"  {digit} → {encoded}")
        except Exception as e:
            print(f"  {digit} → ERROR: {e}")

def run_full_test_suite():
    """Run the complete test suite and provide summary."""
    print("COMPREHENSIVE CHARACTER FALLBACK TEST SUITE")
    print("=" * 60)
    
    # Run all test categories
    individual_passed, individual_failed, individual_failures = test_individual_characters()
    sequence_passed, sequence_failed, sequence_failures = test_character_sequences()
    
    # Run analysis
    test_problematic_cases()
    analyze_emoji_mappings()
    
    # Overall summary
    total_passed = individual_passed + sequence_passed
    total_failed = individual_failed + sequence_failed
    total_tests = total_passed + total_failed
    
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    
    if total_tests > 0:
        success_rate = (total_passed / total_tests) * 100
        print(f"Success rate: {success_rate:.1f}%")
    
    if total_failed > 0:
        print(f"\nFailure breakdown:")
        print(f"  Individual characters: {individual_failed}")
        print(f"  Character sequences: {sequence_failed}")
        
        print(f"\nFirst 10 failures:")
        all_failures = individual_failures + sequence_failures
        for i, (input_val, encoded, decoded) in enumerate(all_failures[:10]):
            print(f"  {i+1}. '{input_val}' → '{encoded}' → '{decoded}'")
        
        if len(all_failures) > 10:
            print(f"  ... and {len(all_failures) - 10} more failures")
    
    return total_passed == total_tests

def main():
    """Main entry point."""
    success = run_full_test_suite()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
