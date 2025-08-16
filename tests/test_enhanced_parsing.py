#!/usr/bin/env python3
"""
Test the enhanced response parsing to handle malformed LLM responses
"""

import json
import sys
import os

# Add the lib directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from llm_client import LLMClient

def test_malformed_response_parsing():
    """Test that the enhanced parser can handle various malformed response formats"""
    
    # Initialize LLM client (we'll just use the parser, not make actual calls)
    client = LLMClient()
    
    # Test case 1: Normal expected format (should still work)
    normal_response = '''[
        {"anger": "🔥😡"},
        {"happiness": "😊"},
        {"sadness": "😢"}
    ]'''
    
    result = client.parse_word_emoji_mappings(normal_response)
    print("✅ Normal format test:")
    print(f"   Result: {result}")
    assert result == {"anger": "🔥😡", "happiness": "😊", "sadness": "😢"}
    
    # Test case 2: Malformed format with word/emoji_combo (the issue you mentioned)
    malformed_response = '''[
        {"word":"anger","emoji_combo":"🔥😡"},
        {"word":"ire","emoji_combo":"😠⚡"},
        {"word":"rebel","emoji_combo":"🤝🏴‍☠️"},
        {"word":"jab","emoji_combo":"🤜💥"},
        {"word":"mouth","emoji_combo":"👄"}
    ]'''
    
    result = client.parse_word_emoji_mappings(malformed_response)
    print("\n✅ Malformed format test (word/emoji_combo):")
    print(f"   Result: {result}")
    expected = {
        "anger": "🔥😡",
        "ire": "😠⚡", 
        "rebel": "🤝🏴‍☠️",
        "jab": "🤜💥",
        "mouth": "👄"
    }
    assert result == expected
    
    # Test case 3: Mixed variations of emoji key names
    mixed_response = '''[
        {"word":"test1","emoji":"🎯"},
        {"word":"test2","emoji_combo":"🔥🎯"},
        {"word":"test3","emojis":"🌟✨"},
        {"word":"test4","emoji_sequence":"🎵🎶"}
    ]'''
    
    result = client.parse_word_emoji_mappings(mixed_response)
    print("\n✅ Mixed emoji key variations test:")
    print(f"   Result: {result}")
    expected = {
        "test1": "🎯",
        "test2": "🔥🎯",
        "test3": "🌟✨", 
        "test4": "🎵🎶"
    }
    assert result == expected
    
    # Test case 4: Your actual data sample
    your_data = '''[
        {"word":"anger","emoji_combo":"🔥😡"},
        {"word":"ire","emoji_combo":"😠⚡"},
        {"word":"rebel","emoji_combo":"🤝🏴‍☠️"},
        {"word":"jab","emoji_combo":"🤜💥"},
        {"word":"mouth","emoji_combo":"👄"},
        {"word":"jaw","emoji_combo":"🦴💬"},
        {"word":"abaft","emoji_combo":"📏⛵"},
        {"word":"jib","emoji_combo":"⛵🛥️"},
        {"word":"to","emoji_combo":"👉"},
        {"word":"jut","emoji_combo":"🚀💥"},
        {"word":"fib","emoji_combo":"🤥"},
        {"word":"lie","emoji_combo":"😢⚡"},
        {"word":"falling","emoji_combo":"⬇️"},
        {"word":"low","emoji_combo":"🌑⏰"},
        {"word":"is","emoji_combo":"👁️🔒"},
        {"word":"man","emoji_combo":"👤"},
        {"word":"axe","emoji_combo":"🔧"},
        {"word":"mod","emoji_combo":"🔩⚙️"},
        {"word":"moment","emoji_combo":"⏳📚"},
        {"word":"now","emoji_combo":"⏰"},
        {"word":"planet","emoji_combo":"🌎"},
        {"word":"out","emoji_combo":"🛤️❌"}
    ]'''
    
    result = client.parse_word_emoji_mappings(your_data)
    print("\n✅ Your actual data test:")
    print(f"   Parsed {len(result)} mappings successfully")
    print("   Sample mappings:")
    for i, (word, emoji) in enumerate(result.items()):
        if i < 5:  # Show first 5
            print(f"     '{word}' -> '{emoji}'")
        elif i == 5:
            print("     ...")
            break
    
    # Verify a few specific mappings
    assert result["anger"] == "🔥😡"
    assert result["planet"] == "🌎"
    assert result["moment"] == "⏳📚"
    
    print(f"\n🎉 All tests passed! Enhanced parser can handle:")
    print(f"   • Normal format: {{'word': 'emoji'}}")
    print(f"   • Malformed format: {{'word': 'value', 'emoji_*': 'value'}}")
    print(f"   • Various emoji key names (emoji, emoji_combo, emojis, etc.)")
    print(f"   • Mixed formats in the same response")

if __name__ == "__main__":
    test_malformed_response_parsing()
