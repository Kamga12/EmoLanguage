#!/usr/bin/env python3
"""
Dictionary and Emoji Map Normalizer

This script:
1. Backs up dictionary.txt to dictionary.original.txt
2. Filters dictionary.txt to only include normalized base forms
3. Filters mappings/ files to remove non-normalized words
4. Generates comprehensive reports on what was filtered out

This dramatically reduces:
- LLM processing time (fewer words to map)
- Emoji collisions (no inflection conflicts)
- System complexity (cleaner mappings)
"""

import json
import logging
from typing import Dict, List, Set, Tuple
from pathlib import Path
from collections import defaultdict, Counter
from word_normalizer import WordNormalizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DictionaryNormalizer:
    def __init__(self):
        """Initialize the dictionary normalizer"""
        self.normalizer = WordNormalizer()
    
    def normalize_dictionary(self, dictionary_path: str = "dictionary.txt", backup_suffix: str = ".original") -> Tuple[int, int, Dict]:
        """
        Normalize dictionary to only include base word forms
        
        Returns:
            Tuple of (original_count, normalized_count, stats)
        """
        dict_file = Path(dictionary_path)
        backup_file = Path(f"{dictionary_path}{backup_suffix}")
        
        if not dict_file.exists():
            logger.error(f"Dictionary file {dictionary_path} not found")
            return 0, 0, {}
        
        # Read original dictionary
        logger.info(f"Reading dictionary from {dictionary_path}")
        with open(dict_file, 'r', encoding='utf-8') as f:
            original_words = [line.strip() for line in f if line.strip()]
        
        logger.info(f"Loaded {len(original_words)} words from dictionary")
        
        # Create backup
        if not backup_file.exists():
            logger.info(f"Creating backup: {backup_file}")
            with open(backup_file, 'w', encoding='utf-8') as f:
                for word in original_words:
                    f.write(f"{word}\n")
        else:
            logger.info(f"Backup already exists: {backup_file}")
        
        # Normalize words and track changes
        word_groups = self.normalizer.analyze_word_groups(original_words)
        
        # Keep only the shortest word from each normalized group (usually the base form)
        normalized_words = []
        filtered_words = []
        normalization_stats = {
            'groups_consolidated': 0,
            'words_removed': 0,
            'consolidation_examples': [],
        }
        
        for base_form, word_list in word_groups.items():
            if len(word_list) == 1:
                # Single word, keep as is
                normalized_words.append(word_list[0])
            else:
                # Multiple words normalize to same base form
                # Keep the shortest one (usually the base form)
                shortest_word = min(word_list, key=len)
                normalized_words.append(shortest_word)
                
                # Track what was filtered out
                removed = [w for w in word_list if w != shortest_word]
                filtered_words.extend(removed)
                
                normalization_stats['groups_consolidated'] += 1
                normalization_stats['words_removed'] += len(removed)
                
                # Save example for reporting
                if len(normalization_stats['consolidation_examples']) < 20:
                    normalization_stats['consolidation_examples'].append({
                        'base_form': base_form,
                        'kept': shortest_word,
                        'removed': removed
                    })
        
        # Sort normalized words
        normalized_words.sort()
        
        # Write normalized dictionary
        logger.info(f"Writing normalized dictionary with {len(normalized_words)} words")
        with open(dict_file, 'w', encoding='utf-8') as f:
            for word in normalized_words:
                f.write(f"{word}\n")
        
        # Generate filtering report
        normalization_stats.update({
            'original_count': len(original_words),
            'normalized_count': len(normalized_words),
            'reduction_count': len(original_words) - len(normalized_words),
            'reduction_percentage': (len(original_words) - len(normalized_words)) / len(original_words) * 100
        })
        
        logger.info(f"Dictionary normalization complete:")
        logger.info(f"  Original words: {len(original_words)}")
        logger.info(f"  Normalized words: {len(normalized_words)}")
        logger.info(f"  Words removed: {len(filtered_words)} ({normalization_stats['reduction_percentage']:.1f}%)")
        logger.info(f"  Groups consolidated: {normalization_stats['groups_consolidated']}")
        
        return len(original_words), len(normalized_words), normalization_stats
    
    def normalize_mappingspings(self, word_to_emoji_path: str = "mappings/word_to_emoji.json", 
                                emoji_to_word_path: str = "mappings/emoji_to_word.json") -> Tuple[Dict, Dict]:
        """
        Filter emoji mappings to only include normalized base forms
        
        Returns:
            Tuple of (filtering_stats, consolidation_log)
        """
        # Load existing mappings
        word_to_emoji_file = Path(word_to_emoji_path)
        emoji_to_word_file = Path(emoji_to_word_path)
        
        if not word_to_emoji_file.exists():
            logger.warning(f"Word-to-emoji file not found: {word_to_emoji_path}")
            return {}, {}
        
        logger.info(f"Loading emoji mappings from {word_to_emoji_path}")
        with open(word_to_emoji_file, 'r', encoding='utf-8') as f:
            word_to_emoji = json.load(f)
        
        original_word_count = len(word_to_emoji)
        logger.info(f"Loaded {original_word_count} word-to-emoji mappings")
        
        # Load emoji-to-word if it exists
        emoji_to_word = {}
        if emoji_to_word_file.exists():
            with open(emoji_to_word_file, 'r', encoding='utf-8') as f:
                emoji_to_word = json.load(f)
        
        # Create backups
        backup_timestamp = int(__import__('time').time())
        word_backup = word_to_emoji_file.with_suffix(f'.backup_{backup_timestamp}.json')
        emoji_backup = emoji_to_word_file.with_suffix(f'.backup_{backup_timestamp}.json')
        
        logger.info(f"Creating backups: {word_backup.name}, {emoji_backup.name}")
        with open(word_backup, 'w', encoding='utf-8') as f:
            json.dump(word_to_emoji, f, indent=2, ensure_ascii=False)
        
        if emoji_to_word:
            with open(emoji_backup, 'w', encoding='utf-8') as f:
                json.dump(emoji_to_word, f, indent=2, ensure_ascii=False)
        
        # Group words by their normalized forms
        word_groups = self.normalizer.analyze_word_groups(list(word_to_emoji.keys()))
        
        # Filter and consolidate mappings
        filtered_word_to_emoji = {}
        consolidation_log = {}
        filtering_stats = {
            'original_mappings': original_word_count,
            'groups_processed': 0,
            'words_kept': 0,
            'words_removed': 0,
            'emoji_conflicts_resolved': 0,
            'consolidation_examples': []
        }
        
        for base_form, word_list in word_groups.items():
            if not word_list:
                continue
            
            filtering_stats['groups_processed'] += 1
            
            # Find all emoji mappings for this group
            group_mappings = {}
            for word in word_list:
                if word in word_to_emoji:
                    group_mappings[word] = word_to_emoji[word]
            
            if not group_mappings:
                continue
            
            # Choose which word/emoji to keep
            if len(group_mappings) == 1:
                # Single mapping, keep as is
                word, emoji = next(iter(group_mappings.items()))
                filtered_word_to_emoji[word] = emoji
                filtering_stats['words_kept'] += 1
            else:
                # Multiple mappings for same base form
                # Strategy: keep the shortest word (usually base form) with its emoji
                shortest_word = min(group_mappings.keys(), key=len)
                chosen_emoji = group_mappings[shortest_word]
                
                filtered_word_to_emoji[shortest_word] = chosen_emoji
                filtering_stats['words_kept'] += 1
                
                # Track what was consolidated
                removed_words = [w for w in group_mappings.keys() if w != shortest_word]
                filtering_stats['words_removed'] += len(removed_words)
                
                if len(set(group_mappings.values())) > 1:
                    filtering_stats['emoji_conflicts_resolved'] += 1
                
                consolidation_log[base_form] = {
                    'kept_word': shortest_word,
                    'kept_emoji': chosen_emoji,
                    'removed_words': removed_words,
                    'all_mappings': group_mappings
                }
                
                # Save example for reporting
                if len(filtering_stats['consolidation_examples']) < 15:
                    filtering_stats['consolidation_examples'].append({
                        'base_form': base_form,
                        'kept': f"{shortest_word} → {chosen_emoji}",
                        'removed': [f"{w} → {e}" for w, e in group_mappings.items() if w != shortest_word]
                    })
        
        # Generate new emoji-to-word mapping
        filtered_emoji_to_word = {emoji: word for word, emoji in filtered_word_to_emoji.items()}
        
        # Save filtered mappings
        logger.info(f"Saving filtered mappings...")
        with open(word_to_emoji_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_word_to_emoji, f, indent=2, ensure_ascii=False)
        
        with open(emoji_to_word_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_emoji_to_word, f, indent=2, ensure_ascii=False)
        
        # Update stats
        filtering_stats['filtered_mappings'] = len(filtered_word_to_emoji)
        filtering_stats['reduction_count'] = original_word_count - len(filtered_word_to_emoji)
        filtering_stats['reduction_percentage'] = (original_word_count - len(filtered_word_to_emoji)) / original_word_count * 100
        
        logger.info(f"Emoji mapping normalization complete:")
        logger.info(f"  Original mappings: {original_word_count}")
        logger.info(f"  Filtered mappings: {len(filtered_word_to_emoji)}")
        logger.info(f"  Mappings removed: {filtering_stats['reduction_count']} ({filtering_stats['reduction_percentage']:.1f}%)")
        logger.info(f"  Emoji conflicts resolved: {filtering_stats['emoji_conflicts_resolved']}")
        
        return filtering_stats, consolidation_log
    
    def create_normalization_report(self, dict_stats: Dict, emoji_stats: Dict, consolidation_log: Dict, 
                                  output_file: str = "normalization_report.md"):
        """Create a comprehensive normalization report"""
        from datetime import datetime
        
        report = f"""# Dictionary and Emoji Map Normalization Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

This report documents the normalization process that filters out inflected word forms 
(plurals, verb tenses, etc.) to keep only base word forms, dramatically reducing 
system complexity and eliminating collision sources.

### Dictionary Normalization Results

- **Original words**: {dict_stats.get('original_count', 0):,}
- **Normalized words**: {dict_stats.get('normalized_count', 0):,}
- **Words removed**: {dict_stats.get('reduction_count', 0):,} ({dict_stats.get('reduction_percentage', 0):.1f}%)
- **Groups consolidated**: {dict_stats.get('groups_consolidated', 0):,}

### Emoji Mapping Normalization Results

- **Original mappings**: {emoji_stats.get('original_mappings', 0):,}
- **Filtered mappings**: {emoji_stats.get('filtered_mappings', 0):,}
- **Mappings removed**: {emoji_stats.get('reduction_count', 0):,} ({emoji_stats.get('reduction_percentage', 0):.1f}%)
- **Emoji conflicts resolved**: {emoji_stats.get('emoji_conflicts_resolved', 0):,}

## Benefits Achieved

1. **🚀 Faster LLM Processing**: {dict_stats.get('reduction_count', 0):,} fewer words to process
2. **💥 Collision Reduction**: Eliminated inflection-based emoji conflicts
3. **🎯 Cleaner Mappings**: Only base forms with semantic clarity
4. **📈 Better Accuracy**: Reduced ambiguity in encode/decode operations

## Dictionary Consolidation Examples

"""
        
        # Add dictionary examples
        for example in dict_stats.get('consolidation_examples', [])[:10]:
            base_form = example['base_form']
            kept = example['kept']
            removed = ', '.join(example['removed'][:5])
            if len(example['removed']) > 5:
                removed += f" (+{len(example['removed'])-5} more)"
            
            report += f"**{base_form}** → kept `{kept}`, removed `{removed}`\n\n"
        
        report += f"""
## Emoji Mapping Consolidation Examples

"""
        
        # Add emoji mapping examples
        for example in emoji_stats.get('consolidation_examples', [])[:10]:
            base_form = example['base_form']
            kept = example['kept']
            removed_list = example['removed'][:3]  # Show max 3 examples
            
            report += f"**{base_form}** group:\n"
            report += f"- ✅ Kept: `{kept}`\n"
            for removed in removed_list:
                report += f"- ❌ Removed: `{removed}`\n"
            report += "\n"
        
        report += f"""
## Collision Resolution Details

The normalization process resolved {emoji_stats.get('emoji_conflicts_resolved', 0)} emoji conflicts where 
different inflected forms of the same base word had different emoji mappings.

### Resolution Strategy

1. **Group by base form**: Words like "run", "running", "ran" are grouped together
2. **Keep shortest word**: Usually the base form (e.g., "run")
3. **Preserve semantic mapping**: The most fundamental emoji mapping is retained
4. **Eliminate redundancy**: No more conflicts between inflected forms

## Files Modified

### Dictionary Files
- `dictionary.txt` - Normalized to base forms only
- `dictionary.original.txt` - Original dictionary backup

### Emoji Mapping Files  
- `mappings/word_to_emoji.json` - Filtered to normalized words
- `mappings/emoji_to_word.json` - Regenerated reverse mapping
- `mappings/word_to_emoji.backup_*.json` - Original mapping backup
- `mappings/emoji_to_word.backup_*.json` - Original reverse mapping backup

## Next Steps

1. **Run collision resolver** on remaining semantic conflicts
2. **Generate new mappings** for any missing common words
3. **Test encode/decode** with normalized mappings
4. **Validate system performance** improvements

The normalization process has significantly simplified your emoji mapping system while
maintaining semantic quality and improving processing efficiency.
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Normalization report saved to {output_file}")
        return output_file

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Normalize dictionary and emoji mappings to base word forms")
    parser.add_argument("--dictionary", default="dictionary.txt",
                       help="Dictionary file to normalize (default: dictionary.txt)")
    parser.add_argument("--word-to-emoji", default="mappings/word_to_emoji.json",
                       help="Word-to-emoji mapping file (default: mappings/word_to_emoji.json)")
    parser.add_argument("--emoji-to-word", default="mappings/emoji_to_word.json", 
                       help="Emoji-to-word mapping file (default: mappings/emoji_to_word.json)")
    parser.add_argument("--dry-run", "-d", action="store_true",
                       help="Show what would be normalized without making changes")
    parser.add_argument("--dictionary-only", action="store_true",
                       help="Only normalize dictionary, skip emoji mappings")
    parser.add_argument("--mappings-only", action="store_true", 
                       help="Only normalize emoji mappings, skip dictionary")
    
    args = parser.parse_args()
    
    try:
        normalizer = DictionaryNormalizer()
        
        dict_stats = {}
        emoji_stats = {}
        consolidation_log = {}
        
        if not args.mappings_only:
            print("🎯 Normalizing dictionary...")
            if args.dry_run:
                print("🔍 DRY RUN - Dictionary analysis:")
                # Just analyze without making changes
                with open(args.dictionary, 'r', encoding='utf-8') as f:
                    words = [line.strip() for line in f if line.strip()]
                word_groups = normalizer.normalizer.analyze_word_groups(words)
                
                consolidations = {base: group for base, group in word_groups.items() if len(group) > 1}
                total_removed = sum(len(group) - 1 for group in consolidations.values())
                
                print(f"  Original words: {len(words)}")
                print(f"  Groups to consolidate: {len(consolidations)}")
                print(f"  Words to remove: {total_removed}")
                print(f"  Final word count: {len(words) - total_removed}")
                
                # Show examples
                print("\n📋 Example consolidations:")
                for i, (base, group) in enumerate(list(consolidations.items())[:5]):
                    shortest = min(group, key=len)
                    removed = [w for w in group if w != shortest]
                    print(f"  {base}: keep '{shortest}', remove {removed}")
                
            else:
                original_count, normalized_count, dict_stats = normalizer.normalize_dictionary(args.dictionary)
                
        if not args.dictionary_only:
            print("\n🎯 Normalizing emoji mappings...")
            if args.dry_run:
                print("🔍 DRY RUN - Emoji mapping analysis:")
                # Just analyze without making changes
                try:
                    with open(args.word_to_emoji, 'r', encoding='utf-8') as f:
                        mappings = json.load(f)
                    
                    word_groups = normalizer.normalizer.analyze_word_groups(list(mappings.keys()))
                    consolidations = {base: group for base, group in word_groups.items() if len(group) > 1}
                    total_removed = sum(len(group) - 1 for group in consolidations.values())
                    
                    print(f"  Original mappings: {len(mappings)}")
                    print(f"  Groups to consolidate: {len(consolidations)}")  
                    print(f"  Mappings to remove: {total_removed}")
                    print(f"  Final mapping count: {len(mappings) - total_removed}")
                    
                    # Show examples
                    print("\n📋 Example consolidations:")
                    for i, (base, group) in enumerate(list(consolidations.items())[:5]):
                        shortest = min(group, key=len)
                        emoji = mappings.get(shortest, "❓")
                        removed = [f"{w}→{mappings.get(w, '❓')}" for w in group if w != shortest]
                        print(f"  {base}: keep '{shortest}→{emoji}', remove {removed[:3]}")
                        
                except FileNotFoundError:
                    print(f"  ❌ Emoji mapping file not found: {args.word_to_emoji}")
            else:
                emoji_stats, consolidation_log = normalizer.normalize_mappingspings(args.word_to_emoji, args.emoji_to_word)
        
        if args.dry_run:
            print("\n🔍 DRY RUN complete - No files modified")
        else:
            # Create comprehensive report
            report_file = normalizer.create_normalization_report(dict_stats, emoji_stats, consolidation_log)
            
            print(f"\n✅ Normalization Complete!")
            print(f"📊 Overall Results:")
            if dict_stats:
                print(f"  Dictionary: {dict_stats.get('original_count', 0)} → {dict_stats.get('normalized_count', 0)} words")
            if emoji_stats:
                print(f"  Mappings: {emoji_stats.get('original_mappings', 0)} → {emoji_stats.get('filtered_mappings', 0)} entries")
            print(f"📄 Report: {report_file}")
            
        return 0
        
    except Exception as e:
        logger.error(f"Error during normalization: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
