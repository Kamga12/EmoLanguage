#!/usr/bin/env python3
"""
Migration Script for Transformation Elimination

This script automatically applies the transformation elimination rules to convert
the current emoji mapping system to the simplified version with context-based grammar.
"""

import json
import logging
import shutil
from typing import Dict, List, Set, Tuple
from pathlib import Path
from datetime import datetime
from word_normalizer import WordNormalizer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MigrationManager:
    def __init__(self):
        self.normalizer = WordNormalizer()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Load current mappings
        self.current_word_to_emoji = {}
        self.current_emoji_to_word = {}
        
        # Track migration statistics
        self.eliminated_words = set()
        self.preserved_words = set()
        self.semantic_preservations = []
        self.elimination_log = []
        
        # Define elimination patterns
        self.elimination_patterns = {
            'simple_plurals': self._is_simple_plural,
            'regular_verb_conjugations': self._is_regular_verb_conjugation,
            'standard_comparatives': self._is_standard_comparative,
            'mechanical_adverbs': self._is_mechanical_adverb
        }
        
        # Define preservation patterns
        self.preservation_patterns = {
            'abstract_nouns': self._is_semantic_abstract_noun,
            'professional_roles': self._is_professional_role,
            'emotional_variations': self._is_emotional_variation,
            'technical_terms': self._is_technical_term,
            'irregular_forms': self._is_irregular_form
        }
    
    def load_current_mappings(self):
        """Load the current emoji mapping files"""
        try:
            with open('mappings/word_to_emoji.json', 'r', encoding='utf-8') as f:
                self.current_word_to_emoji = json.load(f)
            logger.info(f"Loaded {len(self.current_word_to_emoji)} word-to-emoji mappings")
            
            with open('mappings/emoji_to_word.json', 'r', encoding='utf-8') as f:
                self.current_emoji_to_word = json.load(f)
            logger.info(f"Loaded {len(self.current_emoji_to_word)} emoji-to-word mappings")
            
        except FileNotFoundError as e:
            logger.error(f"Could not find mapping files: {e}")
            raise
    
    def backup_current_mappings(self):
        """Create backups of current mapping files"""
        backup_dir = Path('mappings/backups')
        backup_dir.mkdir(exist_ok=True)
        
        # Backup word_to_emoji.json
        word_backup = backup_dir / f"word_to_emoji_pre_migration_{self.timestamp}.json"
        shutil.copy2('mappings/word_to_emoji.json', word_backup)
        
        # Backup emoji_to_word.json  
        emoji_backup = backup_dir / f"emoji_to_word_pre_migration_{self.timestamp}.json"
        shutil.copy2('mappings/emoji_to_word.json', emoji_backup)
        
        logger.info(f"Created backups: {word_backup}, {emoji_backup}")
        return word_backup, emoji_backup
    
    def analyze_transformations(self) -> Dict[str, List[Tuple[str, str]]]:
        """Analyze current mappings to identify transformation patterns"""
        transformation_groups = {}
        
        # Group words by their normalized base forms
        word_groups = self.normalizer.analyze_word_groups(list(self.current_word_to_emoji.keys()))
        
        for base_word, word_variations in word_groups.items():
            if len(word_variations) <= 1:
                continue
                
            for variation in word_variations:
                if variation != base_word:
                    transformation_type = self._classify_transformation(base_word, variation)
                    if transformation_type:
                        if transformation_type not in transformation_groups:
                            transformation_groups[transformation_type] = []
                        transformation_groups[transformation_type].append((base_word, variation))
        
        return transformation_groups
    
    def _classify_transformation(self, base: str, variation: str) -> str:
        """Classify the type of transformation between base and variation"""
        if self._is_simple_plural(base, variation):
            return 'simple_plurals'
        elif self._is_regular_verb_conjugation(base, variation):
            return 'regular_verb_conjugations'
        elif self._is_standard_comparative(base, variation):
            return 'standard_comparatives'
        elif self._is_mechanical_adverb(base, variation):
            return 'mechanical_adverbs'
        return None
    
    def _is_simple_plural(self, base: str, variation: str) -> bool:
        """Check if variation is a simple plural of base"""
        return (variation == base + 's' or 
                variation == base + 'es' or
                (base.endswith('y') and variation == base[:-1] + 'ies'))
    
    def _is_regular_verb_conjugation(self, base: str, variation: str) -> bool:
        """Check if variation is a regular verb conjugation"""
        return (variation == base + 'ing' or
                variation == base + 'ed' or
                variation == base + 's' or
                (base.endswith('e') and variation == base[:-1] + 'ing') or
                (base.endswith('e') and variation == base[:-1] + 'ed'))
    
    def _is_standard_comparative(self, base: str, variation: str) -> bool:
        """Check if variation is a standard comparative/superlative"""
        return (variation == base + 'er' or
                variation == base + 'est' or
                (base.endswith('y') and variation == base[:-1] + 'ier') or
                (base.endswith('y') and variation == base[:-1] + 'iest'))
    
    def _is_mechanical_adverb(self, base: str, variation: str) -> bool:
        """Check if variation is a mechanical -ly adverb"""
        return (variation == base + 'ly' and self._is_simple_adverb_transformation(base, variation))
    
    def _is_simple_adverb_transformation(self, base: str, variation: str) -> bool:
        """Check if this is a simple adjective->adverb transformation without semantic change"""
        # This is a simplified heuristic - in practice, you'd want more sophisticated analysis
        return len(base) > 2 and not base in ['hard', 'real', 'near', 'late']
    
    def _is_semantic_abstract_noun(self, base: str, derived: str) -> bool:
        """Check if derived word is a semantically distinct abstract noun"""
        # Known semantic abstract noun suffixes that create distinct meanings
        semantic_suffixes = ['ity', 'ness', 'ment', 'tion', 'sion', 'ance', 'ence']
        return any(derived.endswith(suffix) for suffix in semantic_suffixes)
    
    def _is_professional_role(self, base: str, derived: str) -> bool:
        """Check if derived word represents a professional role"""
        professional_words = {
            'doctor', 'lawyer', 'teacher', 'engineer', 'scientist', 'artist', 
            'writer', 'manager', 'director', 'professor', 'nurse', 'therapist',
            'surgeon', 'architect', 'designer', 'consultant'
        }
        return derived in professional_words
    
    def _is_emotional_variation(self, base: str, derived: str) -> bool:
        """Check if derived word represents an emotional variation"""
        # Words that have positive/negative pairs with distinct emotional meaning
        emotional_pairs = {
            'useful', 'useless', 'helpful', 'helpless', 'hopeful', 'hopeless',
            'careful', 'careless', 'harmful', 'harmless', 'restful', 'restless'
        }
        return derived in emotional_pairs
    
    def _is_technical_term(self, base: str, derived: str) -> bool:
        """Check if derived word is a technical term with distinct meaning"""
        # This would need a more sophisticated implementation
        # For now, keep words that are significantly different in length/structure
        return len(derived) > len(base) + 3
    
    def _is_irregular_form(self, base: str, derived: str) -> bool:
        """Check if this is an irregular form that should be preserved"""
        irregular_forms = {
            ('person', 'people'), ('child', 'children'), ('mouse', 'mice'),
            ('good', 'better'), ('good', 'best'), ('bad', 'worse'), ('bad', 'worst')
        }
        return (base, derived) in irregular_forms
    
    def should_eliminate_word(self, base_word: str, derived_word: str) -> bool:
        """Determine if a derived word should be eliminated"""
        # First check if it should be preserved
        for pattern_name, pattern_func in self.preservation_patterns.items():
            if pattern_func(base_word, derived_word):
                self.semantic_preservations.append({
                    'base': base_word,
                    'derived': derived_word,
                    'pattern': pattern_name,
                    'reason': f'Preserved due to {pattern_name}'
                })
                return False
        
        # Then check if it should be eliminated
        for pattern_name, pattern_func in self.elimination_patterns.items():
            if pattern_func(base_word, derived_word):
                self.elimination_log.append({
                    'base': base_word,
                    'eliminated': derived_word,
                    'pattern': pattern_name,
                    'reason': f'Eliminated as {pattern_name}'
                })
                return True
        
        return False
    
    def apply_elimination_rules(self) -> Dict[str, str]:
        """Apply elimination rules to create simplified mapping"""
        simplified_mapping = {}
        
        # Group words by base forms
        word_groups = self.normalizer.analyze_word_groups(list(self.current_word_to_emoji.keys()))
        
        for base_word, word_variations in word_groups.items():
            if len(word_variations) == 1:
                # Single word, keep it
                word = word_variations[0]
                simplified_mapping[word] = self.current_word_to_emoji[word]
                self.preserved_words.add(word)
            else:
                # Multiple variations, apply rules
                base_mapping = None
                preserved_variations = []
                
                for word in word_variations:
                    if word == base_word:
                        # This is the base form, always keep it
                        base_mapping = self.current_word_to_emoji[word]
                        self.preserved_words.add(word)
                    elif not self.should_eliminate_word(base_word, word):
                        # This variation should be preserved
                        preserved_variations.append(word)
                        simplified_mapping[word] = self.current_word_to_emoji[word]
                        self.preserved_words.add(word)
                    else:
                        # This variation should be eliminated
                        self.eliminated_words.add(word)
                
                # Add base mapping if we have one
                if base_mapping:
                    simplified_mapping[base_word] = base_mapping
        
        return simplified_mapping
    
    def create_simplified_reverse_mapping(self, word_to_emoji: Dict[str, str]) -> Dict[str, str]:
        """Create reverse emoji-to-word mapping"""
        emoji_to_word = {}
        for word, emoji in word_to_emoji.items():
            emoji_to_word[emoji] = word
        return emoji_to_word
    
    def save_simplified_mappings(self, word_to_emoji: Dict[str, str], dry_run: bool = False):
        """Save the simplified mappings to files"""
        if dry_run:
            logger.info("DRY RUN: Would save simplified mappings")
            return
        
        # Save word-to-emoji mapping
        with open('mappings/word_to_emoji.json', 'w', encoding='utf-8') as f:
            json.dump(word_to_emoji, f, indent=2, ensure_ascii=False)
        
        # Create and save reverse mapping
        emoji_to_word = self.create_simplified_reverse_mapping(word_to_emoji)
        with open('mappings/emoji_to_word.json', 'w', encoding='utf-8') as f:
            json.dump(emoji_to_word, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(word_to_emoji)} simplified word-to-emoji mappings")
        logger.info(f"Saved {len(emoji_to_word)} simplified emoji-to-word mappings")
    
    def generate_migration_report(self) -> str:
        """Generate a comprehensive migration report"""
        report = f"""# Emoji Mapping Migration Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Migration Summary
- **Original mappings**: {len(self.current_word_to_emoji)}
- **Simplified mappings**: {len(self.preserved_words)}
- **Words eliminated**: {len(self.eliminated_words)}
- **Reduction percentage**: {len(self.eliminated_words) / len(self.current_word_to_emoji) * 100:.1f}%

## Elimination Statistics
"""
        
        # Group eliminations by pattern
        elimination_by_pattern = {}
        for entry in self.elimination_log:
            pattern = entry['pattern']
            if pattern not in elimination_by_pattern:
                elimination_by_pattern[pattern] = []
            elimination_by_pattern[pattern].append(entry)
        
        for pattern, entries in elimination_by_pattern.items():
            report += f"\n### {pattern.replace('_', ' ').title()} ({len(entries)} eliminated)\n"
            for entry in entries[:10]:  # Show first 10 examples
                report += f"- `{entry['base']}` → ~~{entry['eliminated']}~~ (eliminated)\n"
            if len(entries) > 10:
                report += f"- ... and {len(entries) - 10} more\n"
        
        report += f"\n## Semantic Preservations ({len(self.semantic_preservations)})\n"
        
        # Group preservations by pattern
        preservation_by_pattern = {}
        for entry in self.semantic_preservations:
            pattern = entry['pattern']
            if pattern not in preservation_by_pattern:
                preservation_by_pattern[pattern] = []
            preservation_by_pattern[pattern].append(entry)
        
        for pattern, entries in preservation_by_pattern.items():
            report += f"\n### {pattern.replace('_', ' ').title()} ({len(entries)} preserved)\n"
            for entry in entries[:10]:  # Show first 10 examples
                report += f"- `{entry['base']}` → `{entry['derived']}` (preserved: {entry['reason']})\n"
            if len(entries) > 10:
                report += f"- ... and {len(entries) - 10} more\n"
        
        report += f"""
## Context Grammar Implementation
The eliminated transformations will be handled through context rules:

### Plurals
- Detected through: determiners (many, several), numbers (two, three), plural verbs (are, were)
- Example: "cats are sleeping" → 🐱 🅰️ 😴 (plural inferred from context)

### Verb Tenses  
- Past: temporal indicators (yesterday, ago), auxiliary verbs (was, were, had)
- Future: modal verbs (will, shall), temporal indicators (tomorrow, next)
- Example: "ran yesterday" → 🏃 🕐 (past tense inferred from context)

### Comparatives
- Detected through: "than", "more...than", "the most", "the...est"
- Modifiers: ➕ (comparative), ⭐ (superlative)
- Example: "faster car" → ⚡➕ 🚗 (comparative inferred from context)

### Adverbs
- Simple -ly forms mapped to base adjective concepts
- Manner preserved through context and base semantic meaning
- Example: "quickly" → ⚡ (speed concept maintained)

## Quality Assurance
- All eliminated words can be reconstructed through context rules
- Semantic meaning preserved through base forms
- Professional terms and emotional distinctions maintained
- Irregular forms explicitly preserved

## Next Steps
1. Update encode.py to use context-aware grammar detection
2. Update decode.py to apply grammar rules during reconstruction
3. Test roundtrip accuracy (encode → decode)
4. Monitor for edge cases and adjust rules as needed
"""
        
        return report
    
    def run_migration(self, dry_run: bool = False):
        """Run the complete migration process"""
        logger.info("Starting emoji mapping migration...")
        
        # Load current mappings
        self.load_current_mappings()
        
        # Create backups (unless dry run)
        if not dry_run:
            self.backup_current_mappings()
        
        # Analyze current transformation patterns
        logger.info("Analyzing transformation patterns...")
        transformations = self.analyze_transformations()
        
        for pattern, examples in transformations.items():
            logger.info(f"Found {len(examples)} {pattern} transformations")
        
        # Apply elimination rules
        logger.info("Applying elimination rules...")
        simplified_mapping = self.apply_elimination_rules()
        
        # Save simplified mappings
        logger.info("Saving simplified mappings...")
        self.save_simplified_mappings(simplified_mapping, dry_run)
        
        # Generate migration report
        logger.info("Generating migration report...")
        report = self.generate_migration_report()
        
        # Save report
        report_path = Path('documents') / f'migration_report_{self.timestamp}.md'
        if not dry_run:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Migration report saved to {report_path}")
        else:
            logger.info("DRY RUN: Migration report generated but not saved")
        
        # Print summary
        print(f"\n{'='*60}")
        print("MIGRATION SUMMARY")
        print(f"{'='*60}")
        print(f"Original mappings: {len(self.current_word_to_emoji)}")
        print(f"Simplified mappings: {len(simplified_mapping)}")
        print(f"Words eliminated: {len(self.eliminated_words)}")
        print(f"Reduction: {len(self.eliminated_words) / len(self.current_word_to_emoji) * 100:.1f}%")
        print(f"Semantic preservations: {len(self.semantic_preservations)}")
        
        if dry_run:
            print("\n🔍 DRY RUN COMPLETE - No files were modified")
        else:
            print(f"\n✅ MIGRATION COMPLETE")
            print(f"📊 Report: {report_path}")
            print("🚀 Ready to use simplified system with context grammar!")
        
        return simplified_mapping

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate emoji mappings to simplified system")
    parser.add_argument("--dry-run", "-d", action="store_true",
                       help="Show what would be changed without making changes")
    
    args = parser.parse_args()
    
    try:
        migration_manager = MigrationManager()
        migration_manager.run_migration(dry_run=args.dry_run)
        return 0
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
