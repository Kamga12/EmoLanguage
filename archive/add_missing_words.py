#!/usr/bin/env python3
"""
Script to extract unencoded words from text and add them to dictionary.txt after normalization.

This script:
1. Takes unencoded words from a file
2. Normalizes them using the WordNormalizer
3. Adds unique normalized words to documents/dictionary.txt
"""

import sys
from pathlib import Path
from typing import Set, List

# Add the lib directory to the path
sys.path.append(str(Path(__file__).parent / 'lib'))

from lib.word_normalizer import WordNormalizer

def load_unencoded_words(filepath: str) -> List[str]:
    """Load unencoded words from file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip()]
        print(f"Loaded {len(words)} unencoded words from {filepath}")
        return words
    except FileNotFoundError:
        print(f"Error: File {filepath} not found")
        return []

def load_existing_dictionary(dict_path: str) -> Set[str]:
    """Load existing words from dictionary."""
    try:
        with open(dict_path, 'r', encoding='utf-8') as f:
            words = {line.strip().lower() for line in f if line.strip()}
        print(f"Loaded {len(words)} existing words from {dict_path}")
        return words
    except FileNotFoundError:
        print(f"Dictionary file {dict_path} not found, starting empty")
        return set()

def normalize_and_filter_words(words: List[str], normalizer: WordNormalizer, existing_words: Set[str]) -> List[str]:
    """Normalize words and filter out duplicates and existing words."""
    normalized_words = []
    seen = set()
    
    for word in words:
        # Skip emoji characters and very short words
        if len(word) < 2 or not word.isalpha():
            continue
            
        # Skip words with capital letters (likely proper nouns - names, places, etc.)
        if any(c.isupper() for c in word):
            continue
            
        normalized = normalizer.normalize_word(word)
        normalized_lower = normalized.lower()
        
        # Skip if already seen in this batch or already in dictionary
        if normalized_lower in seen or normalized_lower in existing_words:
            continue
            
        normalized_words.append(normalized)
        seen.add(normalized_lower)
    
    print(f"Normalized to {len(normalized_words)} unique new words")
    return sorted(normalized_words)

def add_words_to_dictionary(new_words: List[str], dict_path: str) -> None:
    """Add new words to dictionary file."""
    if not new_words:
        print("No new words to add")
        return
    
    try:
        # Append new words to dictionary
        with open(dict_path, 'a', encoding='utf-8') as f:
            for word in new_words:
                f.write(f"{word}\n")
        
        print(f"Successfully added {len(new_words)} new words to {dict_path}")
        
        # Show sample of added words
        sample_size = min(10, len(new_words))
        print(f"Sample of added words: {new_words[:sample_size]}")
        
    except Exception as e:
        print(f"Error writing to dictionary: {e}")

def main():
    """Main function."""
    unencoded_file = "/tmp/unencoded_words.txt"
    dictionary_path = "documents/dictionary.txt"
    
    print("🔄 Processing unencoded words from Bee Movie script...")
    
    # Initialize word normalizer
    normalizer = WordNormalizer()
    
    # Load unencoded words
    unencoded_words = load_unencoded_words(unencoded_file)
    if not unencoded_words:
        return 1
    
    # Load existing dictionary words
    existing_words = load_existing_dictionary(dictionary_path)
    
    # Normalize and filter words
    new_words = normalize_and_filter_words(unencoded_words, normalizer, existing_words)
    
    # Add new words to dictionary
    add_words_to_dictionary(new_words, dictionary_path)
    
    # Show final statistics
    final_existing = load_existing_dictionary(dictionary_path)
    print(f"\n✅ Dictionary now contains {len(final_existing)} total words")
    
    return 0

if __name__ == "__main__":
    exit(main())
