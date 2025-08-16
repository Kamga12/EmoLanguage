#!/usr/bin/env python3
"""
Analyze word transformation patterns in the emoji mapping files.

This script loads both word_to_emoji.json and word_to_emoji_original.json files,
identifies word families, and categorizes transformations by type.
"""

import json
import re
from collections import defaultdict
from pathlib import Path

def load_json_files():
    """Load both emoji mapping files."""
    current_file = Path('mappings/word_to_emoji.json')
    original_file = Path('mappings/backups/word_to_emoji_original.json')
    
    with open(current_file, 'r', encoding='utf-8') as f:
        current_data = json.load(f)
    
    with open(original_file, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    return current_data, original_data

def identify_base_words(all_words):
    """Identify base words and their variations."""
    word_families = defaultdict(list)
    
    for word in all_words:
        # Find potential base words by removing common suffixes
        base_candidates = []
        
        # Try removing various suffixes to find base word
        suffixes_to_try = [
            # Plurals
            'ies', 'es', 's',
            # Verb forms
            'ing', 'ed', 'er', 'est',
            # Adverbs
            'ly',
            # Agent nouns
            'or', 'ist',
            # Abstract nouns
            'ness', 'ity', 'ment', 'tion', 'sion',
            # Adjective forms
            'able', 'ful', 'less', 'ive', 'ous', 'ic', 'al'
        ]
        
        base_candidates.append(word)  # The word itself might be the base
        
        for suffix in suffixes_to_try:
            if word.endswith(suffix):
                base = word[:-len(suffix)]
                if len(base) >= 3:  # Avoid too short bases
                    base_candidates.append(base)
        
        # Find the best base candidate (one that appears in our word list)
        best_base = word
        for candidate in base_candidates:
            if candidate in all_words and candidate != word:
                best_base = candidate
                break
        
        word_families[best_base].append(word)
    
    return word_families

def categorize_transformations(word_families):
    """Categorize word transformations by type."""
    transformations = {
        'plurals': defaultdict(list),
        'verb_conjugations': defaultdict(list),
        'comparatives': defaultdict(list),
        'adverbs': defaultdict(list),
        'agent_nouns': defaultdict(list),
        'abstract_nouns': defaultdict(list),
        'adjective_forms': defaultdict(list)
    }
    
    for base_word, variations in word_families.items():
        for word in variations:
            if word == base_word:
                continue
            
            # Plurals
            if (word.endswith('s') and not word.endswith('ss') and 
                base_word + 's' == word):
                transformations['plurals'][base_word].append(word)
            elif (word.endswith('es') and base_word + 'es' == word):
                transformations['plurals'][base_word].append(word)
            elif (word.endswith('ies') and 
                  base_word.endswith('y') and 
                  base_word[:-1] + 'ies' == word):
                transformations['plurals'][base_word].append(word)
            
            # Verb conjugations
            elif (word.endswith('ing') and 
                  (base_word + 'ing' == word or 
                   base_word[:-1] + 'ing' == word or  # drop final e
                   base_word + base_word[-1] + 'ing' == word)):  # double consonant
                transformations['verb_conjugations'][base_word].append(word)
            elif (word.endswith('ed') and 
                  (base_word + 'ed' == word or 
                   base_word[:-1] + 'ed' == word or  # drop final e
                   base_word + base_word[-1] + 'ed' == word)):  # double consonant
                transformations['verb_conjugations'][base_word].append(word)
            elif (word.endswith('s') and not word.endswith('ss') and 
                  base_word + 's' == word and base_word not in transformations['plurals']):
                transformations['verb_conjugations'][base_word].append(word)
            
            # Comparatives and superlatives
            elif (word.endswith('er') and 
                  (base_word + 'er' == word or 
                   base_word[:-1] + 'er' == word)):  # drop final e
                transformations['comparatives'][base_word].append(word)
            elif (word.endswith('est') and 
                  (base_word + 'est' == word or 
                   base_word[:-1] + 'est' == word)):  # drop final e
                transformations['comparatives'][base_word].append(word)
            
            # Adverbs
            elif word.endswith('ly'):
                if base_word + 'ly' == word:
                    transformations['adverbs'][base_word].append(word)
                elif base_word.endswith('y') and base_word[:-1] + 'ily' == word:
                    transformations['adverbs'][base_word].append(word)
                elif base_word.endswith('ic') and base_word + 'ally' == word:
                    transformations['adverbs'][base_word].append(word)
            
            # Agent nouns
            elif (word.endswith('er') and base_word + 'er' == word and 
                  word not in transformations['comparatives'][base_word]):
                transformations['agent_nouns'][base_word].append(word)
            elif word.endswith('or') and base_word + 'or' == word:
                transformations['agent_nouns'][base_word].append(word)
            elif word.endswith('ist') and base_word + 'ist' == word:
                transformations['agent_nouns'][base_word].append(word)
            
            # Abstract nouns
            elif word.endswith('ness') and base_word + 'ness' == word:
                transformations['abstract_nouns'][base_word].append(word)
            elif word.endswith('ity') and base_word + 'ity' == word:
                transformations['abstract_nouns'][base_word].append(word)
            elif word.endswith('ment') and base_word + 'ment' == word:
                transformations['abstract_nouns'][base_word].append(word)
            elif word.endswith('tion') and base_word + 'tion' == word:
                transformations['abstract_nouns'][base_word].append(word)
            elif word.endswith('sion') and base_word + 'sion' == word:
                transformations['abstract_nouns'][base_word].append(word)
            
            # Adjective forms
            elif word.endswith('able') and base_word + 'able' == word:
                transformations['adjective_forms'][base_word].append(word)
            elif word.endswith('ful') and base_word + 'ful' == word:
                transformations['adjective_forms'][base_word].append(word)
            elif word.endswith('less') and base_word + 'less' == word:
                transformations['adjective_forms'][base_word].append(word)
            elif word.endswith('ive') and base_word + 'ive' == word:
                transformations['adjective_forms'][base_word].append(word)
            elif word.endswith('ous') and base_word + 'ous' == word:
                transformations['adjective_forms'][base_word].append(word)
            elif word.endswith('ic') and base_word + 'ic' == word:
                transformations['adjective_forms'][base_word].append(word)
            elif word.endswith('al') and base_word + 'al' == word:
                transformations['adjective_forms'][base_word].append(word)
    
    return transformations

def analyze_word_families(transformations):
    """Find interesting word families with multiple transformation types."""
    word_family_analysis = defaultdict(dict)
    
    # Collect all base words that have transformations
    all_bases = set()
    for category, base_words in transformations.items():
        all_bases.update(base_words.keys())
    
    # For each base word, collect all its transformations
    for base in all_bases:
        word_family_analysis[base]['transformations'] = {}
        total_variations = 0
        
        for category, base_words in transformations.items():
            if base in base_words:
                word_family_analysis[base]['transformations'][category] = base_words[base]
                total_variations += len(base_words[base])
        
        word_family_analysis[base]['total_variations'] = total_variations
        word_family_analysis[base]['transformation_types'] = len(word_family_analysis[base]['transformations'])
    
    return word_family_analysis

def print_analysis_results(transformations, word_family_analysis, current_data, original_data):
    """Print comprehensive analysis results."""
    
    print("=" * 80)
    print("WORD-TO-EMOJI MAPPING TRANSFORMATION ANALYSIS")
    print("=" * 80)
    
    print(f"\nTotal words in current mapping: {len(current_data)}")
    print(f"Total words in original mapping: {len(original_data)}")
    print(f"Words only in current: {len(set(current_data.keys()) - set(original_data.keys()))}")
    print(f"Words only in original: {len(set(original_data.keys()) - set(current_data.keys()))}")
    
    print("\n" + "=" * 50)
    print("TRANSFORMATION CATEGORIES SUMMARY")
    print("=" * 50)
    
    for category, base_words in transformations.items():
        total_transformations = sum(len(variations) for variations in base_words.values())
        print(f"\n{category.replace('_', ' ').title()}:")
        print(f"  - Base words with this transformation: {len(base_words)}")
        print(f"  - Total transformations: {total_transformations}")
        
        # Show top 5 examples
        examples = []
        for base, variations in list(base_words.items())[:5]:
            examples.append(f"{base} → {', '.join(variations)}")
        
        if examples:
            print("  - Examples:")
            for example in examples:
                print(f"    * {example}")
    
    print("\n" + "=" * 50)
    print("WORD FAMILIES WITH MULTIPLE TRANSFORMATION TYPES")
    print("=" * 50)
    
    # Sort families by number of transformation types and total variations
    sorted_families = sorted(
        word_family_analysis.items(),
        key=lambda x: (x[1]['transformation_types'], x[1]['total_variations']),
        reverse=True
    )
    
    print(f"\nTop 20 most complex word families:")
    for i, (base, analysis) in enumerate(sorted_families[:20], 1):
        print(f"\n{i}. '{base}' family:")
        print(f"   - Transformation types: {analysis['transformation_types']}")
        print(f"   - Total variations: {analysis['total_variations']}")
        
        for trans_type, variations in analysis['transformations'].items():
            print(f"   - {trans_type}: {', '.join(variations)}")
    
    print("\n" + "=" * 50)
    print("DETAILED BREAKDOWN BY TRANSFORMATION TYPE")
    print("=" * 50)
    
    for category, base_words in transformations.items():
        if not base_words:
            continue
            
        print(f"\n{category.replace('_', ' ').title().upper()}:")
        print("-" * 40)
        
        # Sort by number of variations per base word
        sorted_bases = sorted(base_words.items(), key=lambda x: len(x[1]), reverse=True)
        
        for base, variations in sorted_bases[:15]:  # Show top 15
            print(f"{base}: {', '.join(variations)}")

def main():
    """Main analysis function."""
    try:
        # Load the data
        print("Loading emoji mapping files...")
        current_data, original_data = load_json_files()
        
        # Combine all words from both files
        all_words = set(current_data.keys()) | set(original_data.keys())
        print(f"Analyzing {len(all_words)} unique words...")
        
        # Identify word families
        print("Identifying word families...")
        word_families = identify_base_words(all_words)
        
        # Categorize transformations
        print("Categorizing transformations...")
        transformations = categorize_transformations(word_families)
        
        # Analyze word families
        print("Analyzing word families...")
        word_family_analysis = analyze_word_families(transformations)
        
        # Print results
        print_analysis_results(transformations, word_family_analysis, current_data, original_data)
        
    except FileNotFoundError as e:
        print(f"Error: Could not find required file: {e}")
        print("Please ensure both emoji mapping files exist in the correct locations.")
    except json.JSONDecodeError as e:
        print(f"Error: Could not parse JSON file: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
