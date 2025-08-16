#!/usr/bin/env python3
"""
Script to normalize the dictionary file by applying consistent normalization rules
and providing statistics on the changes made.
"""

import re
from collections import Counter
import argparse

def normalize_word(word):
    """
    Normalize a word using consistent rules.
    
    Args:
        word (str): The word to normalize
        
    Returns:
        str: The normalized word, or None if it should be excluded
    """
    # Convert to lowercase and strip whitespace
    word = word.strip().lower()
    
    # Remove any non-alphabetic characters
    word = re.sub(r'[^a-z]', '', word)
    
    # Only exclude completely empty words
    if not word:
        return None
    
    return word

def normalize_dictionary(input_file, output_file=None):
    """
    Normalize all words in the dictionary file.
    
    Args:
        input_file (str): Path to the input dictionary file
        output_file (str): Path to the output file (if None, overwrites input)
        
    Returns:
        dict: Statistics about the normalization process
    """
    if output_file is None:
        output_file = input_file
    
    print(f"Reading dictionary from: {input_file}")
    
    # Read original words
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            original_words = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: File {input_file} not found!")
        return None
    
    print(f"Original dictionary contains: {len(original_words)} entries")
    
    # Track statistics
    stats = {
        'original_count': len(original_words),
        'excluded_count': 0,
        'duplicate_count': 0,
        'final_count': 0,
        'changes': []
    }
    
    # Normalize all words
    normalized_words = []
    excluded_words = []
    changes = []
    
    for original_word in original_words:
        normalized = normalize_word(original_word)
        
        if normalized is None:
            excluded_words.append(original_word)
            stats['excluded_count'] += 1
        elif normalized != original_word.strip().lower():
            # Word was changed during normalization
            changes.append((original_word, normalized))
            normalized_words.append(normalized)
        else:
            # Word unchanged
            normalized_words.append(normalized)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_normalized = []
    duplicates = []
    
    for word in normalized_words:
        if word in seen:
            duplicates.append(word)
            stats['duplicate_count'] += 1
        else:
            seen.add(word)
            unique_normalized.append(word)
    
    # Sort the final list
    final_words = sorted(unique_normalized)
    stats['final_count'] = len(final_words)
    stats['changes'] = changes
    
    # Write normalized dictionary
    print(f"Writing normalized dictionary to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        for word in final_words:
            f.write(word + '\n')
    
    # Print statistics
    print("\n" + "="*60)
    print("DICTIONARY NORMALIZATION STATISTICS")
    print("="*60)
    print(f"Original entries:          {stats['original_count']:,}")
    print(f"Excluded entries:          {stats['excluded_count']:,}")
    print(f"Duplicate entries removed: {stats['duplicate_count']:,}")
    print(f"Final entries:             {stats['final_count']:,}")
    print(f"Net change:                {stats['final_count'] - stats['original_count']:+,}")
    print(f"Compression ratio:         {stats['final_count']/stats['original_count']:.1%}")
    
    if excluded_words:
        print(f"\nExcluded words ({len(excluded_words)}):")
        for word in excluded_words[:10]:  # Show first 10
            print(f"  '{word}'")
        if len(excluded_words) > 10:
            print(f"  ... and {len(excluded_words) - 10} more")
    
    if duplicates:
        duplicate_counts = Counter(duplicates)
        print(f"\nMost common duplicates:")
        for word, count in duplicate_counts.most_common(10):
            print(f"  '{word}': {count + 1} total occurrences")
    
    if changes:
        print(f"\nWords that were changed ({len(changes)}):")
        for original, normalized in changes[:10]:  # Show first 10
            print(f"  '{original}' -> '{normalized}'")
        if len(changes) > 10:
            print(f"  ... and {len(changes) - 10} more")
    
    print("="*60)
    print("Dictionary normalization completed successfully!")
    
    return stats

def main():
    parser = argparse.ArgumentParser(description='Normalize dictionary file')
    parser.add_argument('input_file', 
                       help='Path to the input dictionary file')
    parser.add_argument('-o', '--output', 
                       help='Path to the output file (default: overwrite input)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be changed without writing')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE - No files will be modified")
        output_file = None  # Don't write anything
    else:
        output_file = args.output
    
    stats = normalize_dictionary(args.input_file, output_file)
    
    if stats and args.dry_run:
        print("\nTo apply these changes, run without --dry-run flag")

if __name__ == '__main__':
    main()
