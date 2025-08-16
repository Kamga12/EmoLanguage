#!/usr/bin/env python3
"""
Advanced Collision Resolution System

This script systematically resolves emoji collisions by:
1. Prioritizing high-frequency words for unique emojis
2. Finding alternative emojis for less frequent words
3. Using semantic differentiation strategies
4. Maintaining mapping quality and reversibility
"""

import json
import logging
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path
from collections import defaultdict, Counter
import unicodedata
import re
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CollisionResolver:
    def __init__(self, word_frequency_file: Optional[str] = None):
        """Initialize collision resolver with optional word frequency data"""
        self.word_frequencies = {}
        self.emoji_alternatives = self._build_emoji_alternatives()
        self.semantic_categories = self._build_semantic_categories()
        
        # Load word frequencies if available
        if word_frequency_file and Path(word_frequency_file).exists():
            self._load_word_frequencies(word_frequency_file)
        else:
            logger.info("No word frequency file provided, using basic frequency estimation")
    
    def _load_word_frequencies(self, freq_file: str):
        """Load word frequency data from file"""
        try:
            with open(freq_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        word = parts[0].lower()
                        freq = float(parts[1])
                        self.word_frequencies[word] = freq
            logger.info(f"Loaded {len(self.word_frequencies)} word frequencies")
        except Exception as e:
            logger.warning(f"Could not load word frequencies: {e}")
    
    def _estimate_word_frequency(self, word: str) -> float:
        """Estimate word frequency based on length and common patterns"""
        if word in self.word_frequencies:
            return self.word_frequencies[word]
        
        # Basic frequency estimation
        base_freq = 1.0
        
        # Very short words tend to be more frequent
        if len(word) <= 3:
            base_freq *= 10
        elif len(word) <= 5:
            base_freq *= 5
        elif len(word) >= 12:
            base_freq *= 0.1
        
        # Common word patterns
        common_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'
        }
        
        if word in common_words:
            base_freq *= 100
        
        return base_freq
    
    def _build_emoji_alternatives(self) -> Dict[str, List[str]]:
        """Build a mapping of emoji alternatives for collision resolution"""
        alternatives = {
            # Faces and emotions
            '😀': ['😃', '😄', '😁', '😊', '🙂', '😋'],
            '😢': ['😭', '😥', '😰', '😓', '😔', '😞'],
            '😡': ['😠', '🤬', '👿', '💢', '😤', '🔥'],
            '❤️': ['💖', '💕', '💓', '💗', '💝', '🧡', '💛', '💚', '💙', '💜'],
            
            # Animals
            '🐶': ['🐕', '🦮', '🐕‍🦺', '🐩', '🐺', '🦊'],
            '🐱': ['🐈', '🐈‍⬛', '🦁', '🐯', '🐅', '🐆'],
            '🐭': ['🐹', '🐰', '🐇', '🦫', '🦔', '🐿️'],
            '🐦': ['🐤', '🐣', '🐥', '🦅', '🦆', '🦉', '🦜'],
            
            # Food
            '🍎': ['🍏', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓'],
            '🍞': ['🥖', '🥯', '🧈', '🥐', '🍰', '🧁', '🍪'],
            '🥗': ['🥘', '🍲', '🍛', '🍜', '🍝', '🥙', '🌯'],
            
            # Objects
            '📱': ['💻', '🖥️', '⌨️', '🖱️', '📟', '☎️'],
            '🚗': ['🚙', '🚐', '🚛', '🚚', '🚜', '🏎️', '🚓'],
            '🏠': ['🏡', '🏘️', '🏰', '🏯', '🏛️', '🗼', '🏢'],
            
            # Nature
            '🌳': ['🌲', '🌴', '🌵', '🌿', '🍀', '🌱', '🌾'],
            '🌸': ['🌺', '🌻', '🌹', '🌷', '🌼', '💐', '🌿'],
            '⭐': ['🌟', '✨', '💫', '🌠', '🔆', '☀️', '🌞'],
            
            # Actions
            '🏃': ['🚶', '🧎', '🕺', '💃', '🤸', '🏋️', '🚴'],
            '✍️': ['📝', '🖊️', '🖋️', '✏️', '📄', '📋', '📑'],
            '🔨': ['🔧', '⚙️', '🛠️', '⚒️', '🪛', '🔩', '⚗️'],
        }
        
        return alternatives
    
    def _build_semantic_categories(self) -> Dict[str, Set[str]]:
        """Build semantic categories for intelligent collision resolution"""
        categories = {
            'emotions': {'happy', 'sad', 'angry', 'love', 'hate', 'joy', 'fear', 'surprised', 'excited', 'calm', 'worried', 'confused', 'proud', 'shy', 'guilt', 'shame', 'jealous', 'lonely', 'grateful', 'hope'},
            'actions': {'run', 'walk', 'jump', 'swim', 'fly', 'drive', 'cook', 'eat', 'drink', 'sleep', 'work', 'play', 'read', 'write', 'sing', 'dance', 'fight', 'help', 'teach', 'learn'},
            'animals': {'dog', 'cat', 'bird', 'fish', 'mouse', 'lion', 'tiger', 'bear', 'wolf', 'fox', 'rabbit', 'horse', 'cow', 'pig', 'sheep', 'chicken', 'duck', 'snake', 'frog', 'bee'},
            'food': {'apple', 'banana', 'bread', 'cake', 'pizza', 'burger', 'salad', 'soup', 'rice', 'pasta', 'cheese', 'milk', 'water', 'coffee', 'tea', 'beer', 'wine', 'sugar', 'salt', 'pepper'},
            'objects': {'car', 'house', 'phone', 'computer', 'book', 'chair', 'table', 'bed', 'door', 'window', 'key', 'money', 'bag', 'shoe', 'hat', 'watch', 'ring', 'glass', 'knife', 'spoon'},
            'nature': {'tree', 'flower', 'grass', 'mountain', 'river', 'ocean', 'sun', 'moon', 'star', 'cloud', 'rain', 'snow', 'fire', 'earth', 'water', 'air', 'rock', 'sand', 'leaf', 'branch'},
            'colors': {'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'brown', 'black', 'white', 'gray', 'grey'},
            'numbers': {'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'hundred', 'thousand', 'million', 'first', 'second', 'third'},
            'time': {'second', 'minute', 'hour', 'day', 'week', 'month', 'year', 'morning', 'afternoon', 'evening', 'night', 'today', 'yesterday', 'tomorrow', 'now', 'then', 'early', 'late'},
            'size': {'big', 'small', 'large', 'tiny', 'huge', 'giant', 'little', 'mini', 'massive', 'enormous'},
        }
        
        return categories
    
    def _get_semantic_category(self, word: str) -> Optional[str]:
        """Get the semantic category for a word"""
        word_lower = word.lower()
        for category, words in self.semantic_categories.items():
            if word_lower in words or any(word_lower.startswith(w) for w in words):
                return category
        return None
    
    def _find_alternative_emoji(self, original_emoji: str, used_emojis: Set[str], category: Optional[str] = None) -> Optional[str]:
        """Find an alternative emoji that hasn't been used yet"""
        # Direct alternatives
        if original_emoji in self.emoji_alternatives:
            for alt in self.emoji_alternatives[original_emoji]:
                if alt not in used_emojis:
                    return alt
        
        # Category-based alternatives
        if category:
            category_emojis = self._get_category_emojis(category)
            for emoji in category_emojis:
                if emoji not in used_emojis:
                    return emoji
        
        # Fallback: add a modifier
        modifiers = ['⚪', '⚫', '🔴', '🔵', '🟢', '🟡', '🟠', '🟣', '🔶', '🔷']
        for modifier in modifiers:
            candidate = original_emoji + modifier
            if candidate not in used_emojis:
                return candidate
        
        return None
    
    def _get_category_emojis(self, category: str) -> List[str]:
        """Get appropriate emojis for a semantic category"""
        category_emojis = {
            'emotions': ['😀', '😃', '😄', '😁', '😊', '🙂', '😋', '😍', '🤩', '😘', '😗', '😙', '😚', '🤗', '🤔', '😐', '😑', '😶', '🙄', '😏', '😣', '😥', '😮', '🤐', '😯', '😪', '😫', '😴', '😌', '😛', '😜', '😝', '🤤'],
            'actions': ['🏃', '🚶', '🧎', '🕺', '💃', '🤸', '🏋️', '🚴', '🏊', '🤽', '🤾', '🏌️', '🏇', '🧘', '🛀', '🛌', '👶', '🧒', '👦', '👧', '🧑', '👱', '👨', '👩'],
            'animals': ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯', '🦁', '🐮', '🐷', '🐽', '🐸', '🐵', '🙈', '🙉', '🙊', '🐒', '🐔', '🐧', '🐦', '🐤', '🐣', '🐥'],
            'food': ['🍎', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🍈', '🍒', '🍑', '🥭', '🍍', '🥥', '🥝', '🍅', '🍆', '🥑', '🥦', '🥬', '🥒', '🌶️', '🌽', '🥕', '🧄', '🧅'],
            'objects': ['🚗', '🚙', '🚐', '🚛', '🚚', '🚜', '🏎️', '🚓', '🚑', '🚒', '🚐', '🛻', '🚚', '🚛', '🚜', '🏍️', '🛵', '🚲', '🛴', '🛹', '🛼', '🚁', '🛸', '🚀', '✈️'],
            'nature': ['🌳', '🌲', '🌴', '🌵', '🌿', '☘️', '🍀', '🎍', '🎋', '🍃', '🍂', '🍁', '🍄', '🐚', '🌾', '💐', '🌷', '🌹', '🥀', '🌺', '🌸', '🌼', '🌻', '🌞', '🌝'],
            'colors': ['🔴', '🟠', '🟡', '🟢', '🔵', '🟣', '⚫', '⚪', '🟤', '🔺', '🔻', '🔶', '🔷', '🔸', '🔹', '🔰'],
            'numbers': ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟', '#️⃣', '*️⃣', '🥇', '🥈', '🥉'],
            'time': ['⏰', '⏲️', '⏱️', '⏳', '⌛', '🕐', '🕑', '🕒', '🕓', '🕔', '🕕', '🕖', '🕗', '🕘', '🕙', '🕚', '🕛', '🌅', '🌄', '🌇', '🌆'],
            'size': ['🔍', '🔎', '📏', '📐', '⚖️', '🎯', '🔺', '🔻', '⬆️', '⬇️', '↗️', '↘️', '📈', '📉', '📊'],
        }
        
        return category_emojis.get(category, [])
    
    def analyze_collisions(self, word_to_emoji: Dict[str, str]) -> Dict[str, Dict]:
        """Analyze collisions and prepare resolution data"""
        emoji_usage = defaultdict(list)
        for word, emoji in word_to_emoji.items():
            emoji_usage[emoji].append(word)
        
        collisions = {}
        for emoji, words in emoji_usage.items():
            if len(words) > 1:
                # Sort words by estimated frequency (descending)
                words_with_freq = [(word, self._estimate_word_frequency(word)) for word in words]
                words_with_freq.sort(key=lambda x: x[1], reverse=True)
                
                collisions[emoji] = {
                    'words': [w[0] for w in words_with_freq],
                    'frequencies': [w[1] for w in words_with_freq],
                    'priority_word': words_with_freq[0][0],  # Highest frequency word
                    'alternatives_needed': len(words) - 1
                }
        
        return collisions
    
    def resolve_collisions(self, word_to_emoji: Dict[str, str], max_collisions_to_resolve: int = None) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
        """Resolve emoji collisions by reassigning alternative emojis"""
        logger.info(f"Analyzing collisions in {len(word_to_emoji)} word mappings...")
        
        collisions = self.analyze_collisions(word_to_emoji)
        logger.info(f"Found {len(collisions)} emoji collisions affecting {sum(c['alternatives_needed'] for c in collisions.values())} words")
        
        if max_collisions_to_resolve:
            collision_items = list(collisions.items())[:max_collisions_to_resolve]
            logger.info(f"Resolving first {len(collision_items)} collision groups")
        else:
            collision_items = collisions.items()
        
        resolved_mappings = word_to_emoji.copy()
        used_emojis = set(word_to_emoji.values())
        resolution_log = {}
        
        total_resolved = 0
        
        for emoji, collision_data in collision_items:
            words = collision_data['words']
            priority_word = collision_data['priority_word']
            
            logger.info(f"Resolving collision for {emoji}: {len(words)} words, priority: '{priority_word}'")
            
            # Keep the highest frequency word with original emoji
            alternatives_assigned = []
            
            # Find alternatives for other words
            for word in words[1:]:  # Skip priority word
                category = self._get_semantic_category(word)
                alternative = self._find_alternative_emoji(emoji, used_emojis, category)
                
                if alternative:
                    resolved_mappings[word] = alternative
                    used_emojis.add(alternative)
                    alternatives_assigned.append((word, alternative))
                    total_resolved += 1
                else:
                    logger.warning(f"Could not find alternative for '{word}' (original: {emoji})")
            
            if alternatives_assigned:
                resolution_log[emoji] = {
                    'priority_word': priority_word,
                    'kept_original': emoji,
                    'reassigned': alternatives_assigned
                }
        
        logger.info(f"Successfully resolved {total_resolved} collision instances")
        
        return resolved_mappings, resolution_log
    
    def create_resolution_report(self, resolution_log: Dict, output_file: str = None):
        """Create a detailed report of collision resolutions"""
        if not output_file:
            output_file = "collision_resolution_report.md"
        
        report = f"""# Collision Resolution Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Total collision groups resolved**: {len(resolution_log)}
- **Total words reassigned**: {sum(len(data['reassigned']) for data in resolution_log.values())}

## Resolution Details

"""
        
        for original_emoji, data in resolution_log.items():
            report += f"### {original_emoji} Collision Group\n\n"
            report += f"**Priority word (kept original)**: `{data['priority_word']}` → {original_emoji}\n\n"
            report += f"**Reassigned words**:\n"
            for word, new_emoji in data['reassigned']:
                report += f"- `{word}` → {new_emoji}\n"
            report += "\n"
        
        report += f"""
## Usage

The resolved mappings maintain semantic coherence while eliminating collisions:
- High-frequency words retain their original, intuitive emoji mappings
- Less frequent words receive semantically appropriate alternatives
- All mappings remain reversible for decoding

## Files Updated
- `mappings/word_to_emoji.json` - Updated with resolved mappings
- `mappings/emoji_to_word.json` - Regenerated reverse mapping

"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Resolution report saved to {output_file}")
        
        return output_file

def main():
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Resolve emoji mapping collisions intelligently")
    parser.add_argument("--word-to-emoji", default="mappings/word_to_emoji.json",
                       help="Path to word-to-emoji mapping file")
    parser.add_argument("--output-dir", default="mappings",
                       help="Output directory for resolved mappings")
    parser.add_argument("--word-freq", 
                       help="Optional word frequency file (word freq per line)")
    parser.add_argument("--max-resolve", type=int,
                       help="Maximum number of collision groups to resolve (for testing)")
    parser.add_argument("--dry-run", "-d", action="store_true",
                       help="Show analysis without making changes")
    parser.add_argument("--backup", action="store_true", default=True,
                       help="Create backup of original files")
    
    args = parser.parse_args()
    
    # Load word-to-emoji mappings
    try:
        with open(args.word_to_emoji, 'r', encoding='utf-8') as f:
            word_to_emoji = json.load(f)
    except FileNotFoundError:
        logger.error(f"Word-to-emoji file not found: {args.word_to_emoji}")
        return 1
    
    logger.info(f"Loaded {len(word_to_emoji)} word-to-emoji mappings")
    
    # Initialize resolver
    resolver = CollisionResolver(word_frequency_file=args.word_freq)
    
    # Analyze collisions
    collisions = resolver.analyze_collisions(word_to_emoji)
    total_collision_instances = sum(c['alternatives_needed'] for c in collisions.values())
    
    print(f"\n📊 Collision Analysis Results:")
    print(f"  Total mappings: {len(word_to_emoji):,}")
    print(f"  Collision groups: {len(collisions):,}")
    print(f"  Collision instances: {total_collision_instances:,}")
    print(f"  Collision rate: {total_collision_instances/len(word_to_emoji)*100:.1f}%")
    
    if len(collisions) > 0:
        print(f"\n🔸 Top 5 Collision Examples:")
        for i, (emoji, data) in enumerate(list(collisions.items())[:5]):
            words_display = ', '.join(data['words'][:5])
            if len(data['words']) > 5:
                words_display += f" (+{len(data['words'])-5} more)"
            print(f"  {emoji} → {words_display}")
    
    if args.dry_run:
        print("\n🔍 DRY RUN - No files modified")
        return 0
    
    # Resolve collisions
    resolved_mappings, resolution_log = resolver.resolve_collisions(
        word_to_emoji, max_collisions_to_resolve=args.max_resolve
    )
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Backup original files
    if args.backup:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_word = output_dir / f"word_to_emoji_backup_{timestamp}.json"
        backup_emoji = output_dir / f"emoji_to_word_backup_{timestamp}.json"
        
        with open(backup_word, 'w', encoding='utf-8') as f:
            json.dump(word_to_emoji, f, indent=2, ensure_ascii=False)
        
        # Try to backup emoji-to-word if it exists
        emoji_to_word_path = output_dir / "emoji_to_word.json"
        if emoji_to_word_path.exists():
            with open(emoji_to_word_path, 'r', encoding='utf-8') as f:
                emoji_to_word_orig = json.load(f)
            with open(backup_emoji, 'w', encoding='utf-8') as f:
                json.dump(emoji_to_word_orig, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created backups: {backup_word.name}, {backup_emoji.name}")
    
    # Save resolved mappings
    word_output = output_dir / "word_to_emoji.json"
    with open(word_output, 'w', encoding='utf-8') as f:
        json.dump(resolved_mappings, f, indent=2, ensure_ascii=False)
    
    # Generate reverse mapping
    emoji_to_word_resolved = {emoji: word for word, emoji in resolved_mappings.items()}
    emoji_output = output_dir / "emoji_to_word.json"
    with open(emoji_output, 'w', encoding='utf-8') as f:
        json.dump(emoji_to_word_resolved, f, indent=2, ensure_ascii=False)
    
    # Create resolution report
    report_file = resolver.create_resolution_report(resolution_log)
    
    # Final statistics
    final_collisions = resolver.analyze_collisions(resolved_mappings)
    final_collision_instances = sum(c['alternatives_needed'] for c in final_collisions.values())
    
    print(f"\n✅ Resolution Complete!")
    print(f"📊 Results:")
    print(f"  Original collisions: {total_collision_instances:,}")
    print(f"  Remaining collisions: {final_collision_instances:,}")
    print(f"  Resolved: {total_collision_instances - final_collision_instances:,} ({(total_collision_instances - final_collision_instances)/total_collision_instances*100:.1f}%)")
    print(f"  New collision rate: {final_collision_instances/len(resolved_mappings)*100:.1f}%")
    print(f"\n📄 Files saved:")
    print(f"  Word mappings: {word_output}")
    print(f"  Emoji mappings: {emoji_output}")
    print(f"  Report: {report_file}")
    
    return 0

if __name__ == "__main__":
    exit(main())
