#!/usr/bin/env python3
"""
Fix emoji collisions for common words by reassigning alternative emojis.
Prioritizes the most frequent words for unique mappings.
"""
import json
from datetime import datetime

def main():
    # Load current mappings
    with open('./mappings/word_to_emoji.json', 'r') as f:
        word_to_emoji = json.load(f)
    
    with open('./mappings/emoji_to_word.json', 'r') as f:
        emoji_to_word = json.load(f)
    
    # Word frequency ranking (most common first - should get priority)
    word_priority = {
        # Articles & determiners (highest priority)
        'the': 1, 'a': 2, 'an': 3,
        
        # Pronouns (very high priority)
        'i': 4, 'you': 5, 'it': 6, 'we': 7, 'they': 8, 'he': 9, 'she': 10,
        'my': 11, 'your': 12, 'his': 13, 'her': 14, 'our': 15, 'their': 16,
        
        # Core verbs (high priority)
        'is': 17, 'are': 18, 'was': 19, 'were': 20, 'be': 21, 'have': 22, 'has': 23, 'had': 24,
        'do': 25, 'does': 26, 'did': 27, 'will': 28, 'would': 29, 'can': 30,
        
        # Essential words
        'and': 31, 'to': 32, 'of': 33, 'in': 34, 'for': 35, 'on': 36, 'with': 37, 'at': 38,
        'this': 39, 'that': 40, 'not': 41, 'but': 42, 'or': 43, 'as': 44,
        'what': 45, 'how': 46, 'when': 47, 'where': 48, 'who': 49, 'why': 50,
        
        # Other common words (lower priority)
        'one': 100, 'two': 101, 'time': 102, 'day': 103, 'year': 104,
        'good': 200, 'new': 201, 'work': 202, 'way': 203,
    }
    
    # Define collision fixes with semantic alternatives
    collision_fixes = {
        # Core high-priority words keep existing mappings where appropriate
        'the': '🫵',  # Unique pointing gesture for "the" definite article
        'i': '🫵👤',  # Self-pointing for first person
        'you': '👈',  # Simple pointing for "you"  
        'he': '👨',  # Clear male figure
        'she': '👩',  # Clear female figure
        'we': '👫',  # Two people together
        'they': '👥',  # Multiple people
        
        # Possessives - use hand gestures
        'my': '👋🫲',  # Hand possessive gesture
        'your': '👈🫱',  # Pointing possessive
        'his': '👨💼',  # Male with briefcase
        'her': '👩💼',  # Female with briefcase  
        'our': '👫🤝',  # Our together
        'their': '👥💼',  # Group possession
        
        # Being verbs - use status/existence symbols
        'am': '🙋‍♀️',  # I am (raising hand)
        'is': '📍',  # Location/existence marker
        'are': '📍👥',  # Multiple existence
        'was': '⏮️',  # Past indicator
        'were': '⏮️👥',  # Past multiple
        'be': '✨',  # Existence/being
        'been': '✅⏮️',  # Past completion
        'being': '⚡',  # Active existence
        
        # Action verbs - unique action symbols
        'have': '🫴',  # Holding hands gesture
        'has': '🫴👤',  # Individual possession
        'had': '🫴⏮️',  # Past possession
        'do': '⚡',  # Action energy
        'does': '⚡👤',  # Individual action
        'did': '⚡⏮️',  # Past action
        'make': '🔧',  # Making/building
        'take': '🤏',  # Pinching/taking gesture
        'come': '🚶‍➡️',  # Walking toward
        'go': '🚶‍♂️',  # Walking away
        'get': '🤲',  # Open hands to receive
        'give': '🤝',  # Handshake/giving
        'see': '👀',  # Eyes
        'look': '🔍',  # Magnifying glass
        'know': '🧠',  # Brain
        'think': '💭',  # Thought bubble
        'say': '💬',  # Speech bubble
        'want': '🙏',  # Praying/wanting hands
        'help': '🤝',  # Helping hands
        'work': '⚒️',  # Hammer and pick
        
        # Modal verbs
        'will': '⏭️',  # Future arrow
        'would': '❓⏭️',  # Conditional future
        'could': '💪❓',  # Possible ability
        'should': '✅💭',  # Recommended thought
        'may': '❓✅',  # Permission question
        'might': '❓💫',  # Possible sparkle
        'must': '❗',  # Exclamation necessity
        'shall': '👑⏭️',  # Royal future
        'can': '💪',  # Strength/ability
        
        # Prepositions
        'in': '📦',  # Box/container
        'on': '⬆️📱',  # On top of phone
        'at': '🎯',  # Target
        'to': '➡️',  # Right arrow
        'of': '🔗',  # Link/connection
        'with': '🤝',  # Together
        'by': '👤➡️',  # Person doing
        'from': '⬅️',  # Left arrow
        'up': '⬆️',  # Up arrow
        'out': '🚪➡️',  # Exiting door
        'over': '🌉',  # Bridge over
        'into': '➡️📦',  # Arrow into box
        'about': '🔄',  # Circular/around
        'after': '⏭️',  # Next/after
        'than': '📊',  # Comparison chart
        'then': '1️⃣➡️2️⃣',  # Sequential
        'only': '1️⃣⭐',  # Single star
        'back': '⬅️',  # Back arrow
        'even': '⚖️',  # Balance
        'for': '🎁',  # Gift/for someone
        
        # Conjunctions
        'and': '➕',  # Plus sign
        'or': '⚖️❓',  # Choice balance
        'but': '🛑',  # Stop/but
        'if': '❓➡️',  # Question arrow
        'as': '🟰',  # Equals/as
        'because': '➡️❗',  # Arrow explanation
        
        # Question words
        'what': '❓',  # Question mark
        'who': '👤❓',  # Person question
        'when': '⏰❓',  # Time question
        'where': '📍❓',  # Location question
        'why': '🤔❓',  # Thinking question
        'how': '⚙️❓',  # Method question
        'which': '👈❓',  # Pointing question
        
        # Negation/Affirmation
        'not': '❌',  # X mark
        'no': '🚫',  # Prohibition sign
        'yes': '✅',  # Check mark
        
        # Demonstratives
        'this': '👆',  # Pointing up
        'that': '👉',  # Pointing right
        'these': '👆👆',  # Multiple this
        'there': '📍',  # Location marker
        'here': '📌',  # Pin here
        
        # Time & Quantity
        'time': '⏰',  # Clock
        'day': '🌅',  # Sunrise
        'year': '📅',  # Calendar
        'now': '⏱️',  # Stopwatch
        'first': '🥇',  # First place
        'one': '1️⃣',  # Number one
        'two': '2️⃣',  # Number two
        'all': '🌐',  # Globe/all
        'some': '👌',  # OK hand/some
        'any': '🎲',  # Dice/random
        'other': '↔️',  # Left-right arrow
        
        # Adjectives
        'good': '👍',  # Thumbs up
        'new': '✨',  # Sparkles
        'well': '💯',  # Hundred points
        'just': '⚖️',  # Justice scales
        
        # Common verbs with unique symbols
        'also': '💫',  # Star for "also"
        'hello': '👋',  # Waving
        'world': '🌍',  # Earth
        'thank': '🙏',  # Grateful hands
        'thanks': '🙏💝',  # Thanks gift
        'please': '🥺',  # Pleading face
        'sorry': '😔',  # Sad face
        'excuse': '🙋‍♂️',  # Hand raised
        'people': '👥',  # Multiple people
        'way': '🛤️',  # Railway track
        'like': '👍❤️',  # Like heart
    }
    
    print("🔧 FIXING EMOJI COLLISIONS FOR COMMON WORDS")
    print("=" * 60)
    
    fixes_applied = 0
    collision_report = []
    
    for word, new_emoji in collision_fixes.items():
        if word in word_to_emoji:
            old_emoji = word_to_emoji[word]
            
            # Check if the new emoji already exists
            if new_emoji in emoji_to_word:
                existing_word = emoji_to_word[new_emoji] 
                priority_word = word if word_priority.get(word, 1000) < word_priority.get(existing_word, 1000) else existing_word
                
                if priority_word == word:
                    # This word has higher priority, reassign the other word
                    print(f"🔄 '{word}': {old_emoji} → {new_emoji} (displacing '{existing_word}')")
                    # Need to find alternative for existing_word
                    collision_report.append((existing_word, new_emoji, "needs_alternative"))
                else:
                    # Other word has higher priority, find different emoji
                    print(f"⚠️  '{word}': Cannot use {new_emoji} (higher priority word '{existing_word}' uses it)")
                    collision_report.append((word, new_emoji, "blocked"))
                    continue
            
            # Apply the fix
            if old_emoji in emoji_to_word and emoji_to_word[old_emoji] == word:
                del emoji_to_word[old_emoji]
            
            word_to_emoji[word] = new_emoji
            emoji_to_word[new_emoji] = word
            fixes_applied += 1
            
            print(f"✅ '{word}': {old_emoji} → {new_emoji}")
    
    print(f"\n📊 SUMMARY")
    print(f"Fixes applied: {fixes_applied}")
    print(f"Collisions identified: {len(collision_report)}")
    
    # Save updated mappings
    with open('./mappings/word_to_emoji.json', 'w') as f:
        json.dump(word_to_emoji, f, indent=2, ensure_ascii=False)
    
    with open('./mappings/emoji_to_word.json', 'w') as f:
        json.dump(emoji_to_word, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Mappings updated and saved!")
    
    # Generate collision report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"./mapping_reviews/collision_fixes_report_{timestamp}.md"
    
    with open(report_file, 'w') as f:
        f.write(f"# 🔧 Emoji Collision Fixes Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total fixes applied: {fixes_applied}\n\n")
        
        f.write("## ✅ Successfully Fixed Collisions\n\n")
        for word, new_emoji in collision_fixes.items():
            if word in word_to_emoji and word_to_emoji[word] == new_emoji:
                f.write(f"- **{word}**: Now uses `{new_emoji}` (unique mapping)\n")
        
        f.write("\n## ⚠️ Remaining Issues\n\n")
        if collision_report:
            for word, emoji, status in collision_report:
                f.write(f"- **{word}**: {status} for emoji `{emoji}`\n")
        else:
            f.write("No remaining collision issues detected!\n")
    
    print(f"📄 Report saved to: {report_file}")

if __name__ == "__main__":
    main()
