#!/usr/bin/env python3
"""
Fast parallelized analysis of word transformation patterns in the current emoji mapping file.

This optimized version uses multiprocessing to analyze word families efficiently.
"""

import json
import re
from collections import defaultdict
from pathlib import Path
import multiprocessing as mp
from functools import partial
import time

def load_mappingsping():
    """Load the current emoji mapping file."""
    current_file = Path('mappings/word_to_emoji.json')
    
    with open(current_file, 'r', encoding='utf-8') as f:
        current_data = json.load(f)
    
    return current_data

def find_transformations_for_word(args):
    """Find transformations for a single word. Designed for multiprocessing."""
    word, word_set = args
    transformations = []
    
    # Try removing common suffixes to find base words
    patterns = [
        # Plurals
        (r'(.{3,})s$', r'\1', 'plurals'),
        (r'(.{3,})es$', r'\1', 'plurals'),
        (r'(.{3,}[^aeiou])ies$', r'\1y', 'plurals'),
        (r'(.{3,}[^f])ves$', r'\1f', 'plurals'),
        (r'(.{3,})ves$', r'\1fe', 'plurals'),
        
        # Verb conjugations
        (r'(.{3,})ing$', r'\1', 'verb_conjugations'),
        (r'(.{3,})ing$', r'\1e', 'verb_conjugations'),
        (r'(.{2,})(\w)\2ing$', r'\1\2', 'verb_conjugations'),
        (r'(.{3,})ed$', r'\1', 'verb_conjugations'),
        (r'(.{3,})ed$', r'\1e', 'verb_conjugations'),
        (r'(.{2,})(\w)\2ed$', r'\1\2', 'verb_conjugations'),
        
        # Comparatives
        (r'(.{3,})er$', r'\1', 'comparatives'),
        (r'(.{3,})er$', r'\1e', 'comparatives'),
        (r'(.{3,}[^aeiou])ier$', r'\1y', 'comparatives'),
        (r'(.{3,})est$', r'\1', 'comparatives'),
        (r'(.{3,})est$', r'\1e', 'comparatives'),
        (r'(.{3,}[^aeiou])iest$', r'\1y', 'comparatives'),
        
        # Adverbs
        (r'(.{3,})ly$', r'\1', 'adverbs'),
        (r'(.{3,}[^aeiou])ily$', r'\1y', 'adverbs'),
        (r'(.{3,}ic)ally$', r'\1', 'adverbs'),
        
        # Agent nouns
        (r'(.{3,})er$', r'\1', 'agent_nouns'),
        (r'(.{3,})or$', r'\1', 'agent_nouns'),
        (r'(.{3,})ist$', r'\1', 'agent_nouns'),
        
        # Abstract nouns
        (r'(.{3,})ness$', r'\1', 'abstract_nouns'),
        (r'(.{3,})ity$', r'\1', 'abstract_nouns'),
        (r'(.{3,})ment$', r'\1', 'abstract_nouns'),
        (r'(.{3,})tion$', r'\1', 'abstract_nouns'),
        (r'(.{3,})sion$', r'\1', 'abstract_nouns'),
        
        # Adjective forms
        (r'(.{3,})able$', r'\1', 'adjective_forms'),
        (r'(.{3,})ful$', r'\1', 'adjective_forms'),
        (r'(.{3,})less$', r'\1', 'adjective_forms'),
        (r'(.{3,})ive$', r'\1', 'adjective_forms'),
        (r'(.{3,})ous$', r'\1', 'adjective_forms'),
        (r'(.{3,})ic$', r'\1', 'adjective_forms'),
        (r'(.{3,})al$', r'\1', 'adjective_forms'),
    ]
    
    for pattern, replacement, category in patterns:
        match = re.match(pattern, word)
        if match:
            potential_base = re.sub(pattern, replacement, word)
            if potential_base in word_set and potential_base != word:
                transformations.append((potential_base, word, category))
    
    return transformations

def analyze_transformations_parallel(words, num_processes=None):
    """Analyze transformations using multiprocessing."""
    if num_processes is None:
        num_processes = min(32, mp.cpu_count())
    
    word_set = set(words)
    
    # Prepare arguments for multiprocessing
    args = [(word, word_set) for word in words]
    
    print(f"Using {num_processes} processes to analyze {len(words):,} words...")
    
    # Use multiprocessing to find transformations
    with mp.Pool(num_processes) as pool:
        results = pool.map(find_transformations_for_word, args, chunksize=100)
    
    # Collect results
    transformations = {
        'plurals': defaultdict(list),
        'verb_conjugations': defaultdict(list),
        'comparatives': defaultdict(list),
        'adverbs': defaultdict(list),
        'agent_nouns': defaultdict(list),
        'abstract_nouns': defaultdict(list),
        'adjective_forms': defaultdict(list)
    }
    
    for word_transformations in results:
        for base, derived, category in word_transformations:
            transformations[category][base].append(derived)
    
    return transformations

def find_word_families(transformations):
    """Find word families with multiple transformation types."""
    family_analysis = defaultdict(dict)
    
    # Collect all base words that have transformations
    all_bases = set()
    for category, base_words in transformations.items():
        all_bases.update(base_words.keys())
    
    # Analyze each family
    for base in all_bases:
        family_analysis[base]['transformations'] = {}
        total_variations = 0
        
        for category, base_words in transformations.items():
            if base in base_words and base_words[base]:
                family_analysis[base]['transformations'][category] = base_words[base]
                total_variations += len(base_words[base])
        
        family_analysis[base]['total_variations'] = total_variations
        family_analysis[base]['transformation_types'] = len(family_analysis[base]['transformations'])
    
    return family_analysis

def print_analysis_results(emoji_data, transformations, family_analysis):
    """Print comprehensive analysis results."""
    
    print("=" * 80)
    print("CURRENT EMOJI MAPPING WORD TRANSFORMATION ANALYSIS")
    print("=" * 80)
    
    print(f"\nTotal words in current mapping: {len(emoji_data):,}")
    
    # Overall statistics
    total_families = len([f for f in family_analysis.values() if f['total_variations'] > 0])
    total_transformations = sum(f['total_variations'] for f in family_analysis.values())
    
    print(f"Word families with transformations: {total_families:,}")
    print(f"Total word transformations found: {total_transformations:,}")
    
    print("\n" + "=" * 60)
    print("TRANSFORMATION CATEGORIES OVERVIEW")
    print("=" * 60)
    
    for category, base_words in transformations.items():
        if not base_words:
            continue
            
        total_transforms = sum(len(variations) for variations in base_words.values())
        print(f"\n{category.replace('_', ' ').title()}:")
        print(f"  • Base words: {len(base_words):,}")
        print(f"  • Total transformations: {total_transforms:,}")
        
        # Show examples
        examples = list(base_words.items())[:3]
        if examples:
            print("  • Examples:")
            for base, variations in examples:
                print(f"    - {base} → {', '.join(variations[:3])}")
    
    print("\n" + "=" * 60)
    print("TOP WORD FAMILIES (MULTIPLE TRANSFORMATION TYPES)")
    print("=" * 60)
    
    # Sort by complexity
    complex_families = sorted(
        [(base, data) for base, data in family_analysis.items()
         if data['transformation_types'] >= 3],
        key=lambda x: (x[1]['transformation_types'], x[1]['total_variations']),
        reverse=True
    )
    
    print(f"\nFound {len(complex_families)} families with 3+ transformation types:")
    
    for i, (base, data) in enumerate(complex_families[:20], 1):
        print(f"\n{i}. '{base}' family:")
        print(f"   Types: {data['transformation_types']}, Variations: {data['total_variations']}")
        
        for trans_type, variations in data['transformations'].items():
            print(f"   • {trans_type}: {', '.join(variations)}")

    print("\n" + "=" * 60)
    print("INTERESTING WORD FAMILY EXAMPLES")
    print("=" * 60)
    
    # Show some of the most complex families
    print("\nMost complex families (by transformation types):")
    for i, (base, data) in enumerate(complex_families[:10], 1):
        print(f"\n{i}. '{base}' → {data['total_variations']} variations across {data['transformation_types']} types")
        for trans_type, variations in sorted(data['transformations'].items()):
            print(f"   {trans_type}: {', '.join(sorted(variations))}")

    print("\n" + "=" * 60)
    print("TRANSFORMATION TYPE BREAKDOWN")
    print("=" * 60)
    
    for category, base_words in transformations.items():
        if not base_words:
            continue
            
        print(f"\n{category.replace('_', ' ').title().upper()}:")
        print("-" * 40)
        
        # Show top examples by number of variations
        sorted_examples = sorted(base_words.items(), 
                               key=lambda x: len(x[1]), 
                               reverse=True)[:15]
        
        for base, variations in sorted_examples:
            print(f"{base}: {', '.join(sorted(variations))}")

def main():
    """Main analysis function."""
    start_time = time.time()
    
    try:
        print("Loading current emoji mapping...")
        emoji_data = load_mappingsping()
        
        print(f"Analyzing transformations for {len(emoji_data):,} words...")
        transformations = analyze_transformations_parallel(list(emoji_data.keys()))
        
        print("Finding word families...")
        family_analysis = find_word_families(transformations)
        
        print("Generating analysis report...")
        print_analysis_results(emoji_data, transformations, family_analysis)
        
        elapsed = time.time() - start_time
        print(f"\nAnalysis completed in {elapsed:.2f} seconds")
        
    except FileNotFoundError as e:
        print(f"Error: Could not find emoji mapping file: {e}")
    except json.JSONDecodeError as e:
        print(f"Error: Could not parse JSON file: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
