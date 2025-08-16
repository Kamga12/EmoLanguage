#!/usr/bin/env python3

import json
from collections import defaultdict
from word_normalizer import WordNormalizer

class SimpleConflictResolver:
    def __init__(self):
        self.normalizer = WordNormalizer()
        # Priority words that should keep their emojis
        self.priority_words = {
            # Common words that should get priority
            'the', 'and', 'or', 'but', 'for', 'with', 'from', 'by', 'at', 'in', 'on', 'to',
            'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'did', 'does', 'will', 'would', 'should', 'could',
            # Basic descriptive words
            'quick', 'fast', 'slow', 'big', 'small', 'good', 'bad', 'new', 'old', 'hot', 'cold',
            # Colors
            'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'brown', 'black', 'white', 'gray',
            # Animals
            'cat', 'dog', 'bird', 'fish', 'fox', 'bear', 'lion', 'tiger', 'elephant',
            # Actions
            'run', 'walk', 'jump', 'sit', 'stand', 'go', 'come', 'see', 'look', 'hear', 'say', 'tell', 'know', 'think',
            # Body parts
            'head', 'hand', 'foot', 'eye', 'ear', 'nose', 'mouth', 'arm', 'leg',
            # Numbers
            'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
        }
    
    def get_word_priority(self, word):
        """Calculate word priority (higher = more important)"""
        priority = 0
        
        # Priority words get highest score
        if word in self.priority_words:
            priority += 1000
        
        # Shorter words get higher priority (usually more common)
        if len(word) <= 3:
            priority += 100
        elif len(word) <= 5:
            priority += 50
        elif len(word) <= 7:
            priority += 25
        
        # Base words get priority over inflected forms
        normalized = self.normalizer.normalize_word(word)
        if normalized == word:  # It's already a base form
            priority += 30
        
        # Common suffixes get lower priority
        if word.endswith(('ly', 'ing', 'ed', 'er', 'est', 'tion', 'sion', 'ness', 'ment')):
            priority -= 20
        
        # Very technical or obscure words get lower priority
        if any(x in word for x in ['ology', 'ism', 'ist', 'ance', 'ence', 'ical']):
            priority -= 10
        
        # Alphabetical tie-breaker (consistent ordering)
        priority -= ord(word[0]) / 1000.0
        
        return priority
    
    def resolve_conflicts(self, word_to_emoji):
        """Resolve emoji conflicts by keeping highest priority word for each emoji"""
        # Find conflicts
        emoji_to_words = defaultdict(list)
        for word, emoji in word_to_emoji.items():
            emoji_to_words[emoji].append(word)
        
        conflicts = {emoji: words for emoji, words in emoji_to_words.items() if len(words) > 1}
        
        print(f"Found {len(conflicts)} emoji conflicts")
        
        # Resolve conflicts
        resolved_mapping = {}
        removed_mappings = []
        
        for emoji, words in emoji_to_words.items():
            if len(words) == 1:
                # No conflict
                resolved_mapping[words[0]] = emoji
            else:
                # Conflict - pick highest priority word
                words_with_priority = [(word, self.get_word_priority(word)) for word in words]
                words_with_priority.sort(key=lambda x: x[1], reverse=True)
                
                # Keep the highest priority word
                chosen_word = words_with_priority[0][0]
                resolved_mapping[chosen_word] = emoji
                
                # Record removed words
                for word, priority in words_with_priority[1:]:
                    removed_mappings.append((word, emoji, chosen_word))
                
                # Print conflict resolution for important cases
                if any(word in self.priority_words for word in words):
                    print(f"Resolved {emoji}: kept '{chosen_word}' over {[w for w, _ in words_with_priority[1:]]}")
        
        return resolved_mapping, removed_mappings
    
    def generate_new_emojis_for_removed_words(self, removed_mappings):
        """Generate new unique emoji assignments for removed words"""
        # This is a simplified approach - in practice you'd want more sophisticated emoji generation
        new_mappings = {}
        
        # Simple strategy: add a modifier to create unique variants
        modifiers = ['🔴', '🔵', '🟢', '🟡', '🟠', '🟣', '⚫', '⚪', '🟤']
        modifier_index = 0
        
        for removed_word, original_emoji, chosen_word in removed_mappings:
            # Create a variant by adding a modifier
            if modifier_index < len(modifiers):
                new_emoji = original_emoji + modifiers[modifier_index]
                new_mappings[removed_word] = new_emoji
                modifier_index = (modifier_index + 1) % len(modifiers)
            else:
                # If we run out of modifiers, use the original word
                new_mappings[removed_word] = removed_word
        
        return new_mappings

def main():
    print("Loading emoji mappings...")
    
    # Load current mappings
    with open('mappings/word_to_emoji.json', 'r') as f:
        word_to_emoji = json.load(f)
    
    print(f"Loaded {len(word_to_emoji)} word-to-emoji mappings")
    
    # Resolve conflicts
    resolver = SimpleConflictResolver()
    resolved_mapping, removed_mappings = resolver.resolve_conflicts(word_to_emoji)
    
    print(f"\nResolution summary:")
    print(f"  Resolved mappings: {len(resolved_mapping)}")
    print(f"  Removed mappings: {len(removed_mappings)}")
    
    # Generate new emojis for some removed words
    new_mappings = resolver.generate_new_emojis_for_removed_words(removed_mappings[:1000])  # Limit to first 1000
    
    # Combine resolved and new mappings
    final_mapping = {**resolved_mapping, **new_mappings}
    
    print(f"  New variant mappings: {len(new_mappings)}")
    print(f"  Final mapping size: {len(final_mapping)}")
    
    # Backup original
    import shutil
    import time
    timestamp = int(time.time())
    shutil.copy('mappings/word_to_emoji.json', f'mappings/backups/word_to_emoji.conflict_backup_{timestamp}.json')
    
    # Save resolved mapping
    with open('mappings/word_to_emoji.json', 'w') as f:
        json.dump(final_mapping, f, indent=2, ensure_ascii=False)
    
    # Generate reverse mapping
    emoji_to_word = {}
    for word, emoji in final_mapping.items():
        emoji_to_word[emoji] = word
    
    shutil.copy('mappings/emoji_to_word.json', f'mappings/backups/emoji_to_word.conflict_backup_{timestamp}.json')
    
    with open('mappings/emoji_to_word.json', 'w') as f:
        json.dump(emoji_to_word, f, indent=2, ensure_ascii=False)
    
    print(f"\nMappings saved. Backups created with timestamp {timestamp}")
    
    # Test key mappings
    test_words = ['quick', 'brown', 'fox', 'jump']
    print(f"\nTesting key word mappings:")
    for word in test_words:
        if word in final_mapping:
            emoji = final_mapping[word]
            reverse_word = emoji_to_word.get(emoji, 'NOT FOUND')
            status = "✅" if reverse_word == word else "❌"
            print(f"  {word} -> {emoji} -> {reverse_word} {status}")
        else:
            print(f"  {word} -> NOT FOUND ❌")
    
    # Show some removed mappings
    print(f"\nSample removed mappings (first 10):")
    for i, (word, original_emoji, chosen_word) in enumerate(removed_mappings[:10]):
        print(f"  {word} ({original_emoji}) -> lost to '{chosen_word}'")

if __name__ == "__main__":
    main()
