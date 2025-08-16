#!/usr/bin/env python3
"""
Analyze word transformation patterns in the current emoji mapping file.

This script loads only word_to_emoji.json file and analyzes word families
and transformation patterns within the current active mapping.
"""

import json
import re
from collections import defaultdict
from pathlib import Path

def load_mappingsping():
    """Load the current emoji mapping file."""
    current_file = Path('mappings/word_to_emoji.json')
    
    with open(current_file, 'r', encoding='utf-8') as f:
        current_data = json.load(f)
    
    return current_data

def identify_word_families(all_words):
    """Identify base words and their variations using improved logic."""
    word_families = defaultdict(set)
    
    # Create a sorted list by word length (shorter words first)
    sorted_words = sorted(all_words, key=len)
    
    for word in sorted_words:
        # Check if this word is already assigned to a family
        assigned = False
        
        # Look for potential base words (shorter words that this word could derive from)
        for potential_base in sorted_words:
            if len(potential_base) >= len(word):
                break  # No point checking longer words
            
            if potential_base == word:
                continue
                
            # Check various transformation patterns
            if is_derived_from(word, potential_base):
                word_families[potential_base].add(word)
                word_families[potential_base].add(potential_base)  # Include base word itself
                assigned = True
                break
        
        # If not assigned to any family, it's its own base
        if not assigned:
            word_families[word].add(word)
    
    # Convert sets back to lists and filter out single-word families for analysis
    result = {}
    for base, words in word_families.items():
        word_list = list(words)
        result[base] = word_list
    
    return result

def is_derived_from(word, base):
    """Check if 'word' could be derived from 'base' through common transformations."""
    if word == base:
        return False
    
    # Plurals
    if word == base + 's' or word == base + 'es':
        return True
    if base.endswith('y') and word == base[:-1] + 'ies':
        return True
    if base.endswith('f') and word == base[:-1] + 'ves':
        return True
    if base.endswith('fe') and word == base[:-2] + 'ves':
        return True
    
    # Verb conjugations
    if word == base + 'ing' or word == base + 'ed' or word == base + 's':
        return True
    if base.endswith('e') and (word == base[:-1] + 'ing' or word == base[:-1] + 'ed'):
        return True
    # Double consonant cases
    if len(base) >= 3 and base[-1] == base[-2] and (
        word == base + 'ing' or word == base + 'ed'
    ):
        return True
    # Simple consonant doubling
    if len(base) >= 2 and word == base + base[-1] + 'ing':
        return True
    if len(base) >= 2 and word == base + base[-1] + 'ed':
        return True
    
    # Comparatives and superlatives
    if word == base + 'er' or word == base + 'est':
        return True
    if base.endswith('e') and (word == base[:-1] + 'er' or word == base[:-1] + 'est'):
        return True
    if base.endswith('y') and (word == base[:-1] + 'ier' or word == base[:-1] + 'iest'):
        return True
    
    # Adverbs
    if word == base + 'ly':
        return True
    if base.endswith('y') and word == base[:-1] + 'ily':
        return True
    if base.endswith('ic') and word == base + 'ally':
        return True
    
    # Agent nouns
    if word == base + 'er' or word == base + 'or' or word == base + 'ist':
        return True
    
    # Abstract nouns  
    if word == base + 'ness' or word == base + 'ity' or word == base + 'ment':
        return True
    if word == base + 'tion' or word == base + 'sion':
        return True
    
    # Adjective forms
    if word == base + 'able' or word == base + 'ful' or word == base + 'less':
        return True
    if word == base + 'ive' or word == base + 'ous' or word == base + 'ic':
        return True
    if word == base + 'al':
        return True
    
    return False

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
        if len(variations) <= 1:  # Skip single-word families
            continue
            
        for word in variations:
            if word == base_word:
                continue
            
            transformation_type = classify_transformation(base_word, word)
            if transformation_type:
                transformations[transformation_type][base_word].append(word)
    
    return transformations

def classify_transformation(base, word):
    """Classify what type of transformation creates 'word' from 'base'."""
    
    # Plurals (check first as they can conflict with verb forms)
    if word == base + 's' and not is_likely_verb(base):
        return 'plurals'
    if word == base + 'es':
        return 'plurals'
    if base.endswith('y') and word == base[:-1] + 'ies':
        return 'plurals'
    if base.endswith('f') and word == base[:-1] + 'ves':
        return 'plurals'
    if base.endswith('fe') and word == base[:-2] + 'ves':
        return 'plurals'
    
    # Verb conjugations
    if word.endswith('ing'):
        if (word == base + 'ing' or 
            (base.endswith('e') and word == base[:-1] + 'ing') or
            (len(base) >= 2 and word == base + base[-1] + 'ing')):
            return 'verb_conjugations'
    
    if word.endswith('ed'):
        if (word == base + 'ed' or
            (base.endswith('e') and word == base[:-1] + 'ed') or
            (len(base) >= 2 and word == base + base[-1] + 'ed')):
            return 'verb_conjugations'
    
    if word == base + 's' and is_likely_verb(base):
        return 'verb_conjugations'
    
    # Comparatives and superlatives  
    if word.endswith('er') and not word.endswith('eer'):
        if (word == base + 'er' or
            (base.endswith('e') and word == base[:-1] + 'er') or
            (base.endswith('y') and word == base[:-1] + 'ier')):
            # Could be comparative or agent noun - check context
            if is_likely_adjective(base):
                return 'comparatives'
            else:
                return 'agent_nouns'
    
    if word.endswith('est'):
        if (word == base + 'est' or
            (base.endswith('e') and word == base[:-1] + 'est') or
            (base.endswith('y') and word == base[:-1] + 'iest')):
            return 'comparatives'
    
    # Adverbs
    if word.endswith('ly'):
        if (word == base + 'ly' or
            (base.endswith('y') and word == base[:-1] + 'ily') or
            (base.endswith('ic') and word == base + 'ally')):
            return 'adverbs'
    
    # Agent nouns (non-comparative -er)
    if word.endswith('er') and word == base + 'er' and not is_likely_adjective(base):
        return 'agent_nouns'
    if word.endswith('or') and word == base + 'or':
        return 'agent_nouns' 
    if word.endswith('ist') and word == base + 'ist':
        return 'agent_nouns'
    
    # Abstract nouns
    if word.endswith('ness') and word == base + 'ness':
        return 'abstract_nouns'
    if word.endswith('ity') and word == base + 'ity':
        return 'abstract_nouns'
    if word.endswith('ment') and word == base + 'ment':
        return 'abstract_nouns'
    if word.endswith('tion') and word == base + 'tion':
        return 'abstract_nouns'
    if word.endswith('sion') and word == base + 'sion':
        return 'abstract_nouns'
    
    # Adjective forms
    if word.endswith('able') and word == base + 'able':
        return 'adjective_forms'
    if word.endswith('ful') and word == base + 'ful':
        return 'adjective_forms'  
    if word.endswith('less') and word == base + 'less':
        return 'adjective_forms'
    if word.endswith('ive') and word == base + 'ive':
        return 'adjective_forms'
    if word.endswith('ous') and word == base + 'ous':
        return 'adjective_forms'
    if word.endswith('ic') and word == base + 'ic':
        return 'adjective_forms'
    if word.endswith('al') and word == base + 'al':
        return 'adjective_forms'
    
    return None

def is_likely_verb(word):
    """Heuristic to determine if a word is likely a verb."""
    # Common verb patterns and endings
    verb_endings = ['ate', 'ize', 'ify', 'en']
    verb_words = {'run', 'walk', 'talk', 'work', 'play', 'make', 'take', 'give', 'get', 'come', 'go'}
    
    return any(word.endswith(ending) for ending in verb_endings) or word in verb_words

def is_likely_adjective(word):
    """Heuristic to determine if a word is likely an adjective."""
    # Common adjective patterns
    adj_endings = ['ful', 'less', 'ous', 'ive', 'able', 'ic', 'al', 'ed', 'ing']
    return any(word.endswith(ending) for ending in adj_endings) or len(word) <= 6

def find_interesting_families(transformations):
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

def print_comprehensive_analysis(emoji_data, transformations, family_analysis):
    """Print a comprehensive analysis of the word transformation patterns."""
    
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
    
    # Sort by complexity (number of transformation types, then total variations)
    complex_families = sorted(
        [(base, data) for base, data in family_analysis.items() 
         if data['transformation_types'] >= 3],
        key=lambda x: (x[1]['transformation_types'], x[1]['total_variations']),
        reverse=True
    )
    
    print(f"\nFound {len(complex_families)} families with 3+ transformation types:")
    
    for i, (base, data) in enumerate(complex_families[:15], 1):
        print(f"\n{i}. '{base}' family:")
        print(f"   Types: {data['transformation_types']}, Variations: {data['total_variations']}")
        
        for trans_type, variations in data['transformations'].items():
            print(f"   • {trans_type}: {', '.join(variations)}")
    
    # Show some examples of each transformation type
    print("\n" + "=" * 60)
    print("DETAILED EXAMPLES BY TRANSFORMATION TYPE") 
    print("=" * 60)
    
    for category, base_words in transformations.items():
        if not base_words:
            continue
            
        print(f"\n{category.replace('_', ' ').title().upper()}:")
        print("-" * 50)
        
        # Show interesting examples
        sorted_examples = sorted(base_words.items(), 
                               key=lambda x: len(x[1]), 
                               reverse=True)[:10]
        
        for base, variations in sorted_examples:
            print(f"{base}: {', '.join(variations)}")

def main():
    """Main analysis function."""
    try:
        print("Loading current emoji mapping...")
        emoji_data = load_mappingsping()
        
        print("Identifying word families...")
        word_families = identify_word_families(set(emoji_data.keys()))
        
        print("Categorizing transformations...")  
        transformations = categorize_transformations(word_families)
        
        print("Analyzing complex word families...")
        family_analysis = find_interesting_families(transformations)
        
        print_comprehensive_analysis(emoji_data, transformations, family_analysis)
        
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
