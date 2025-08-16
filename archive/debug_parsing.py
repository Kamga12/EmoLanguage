#!/usr/bin/env python3
"""
Debug the current LLM response parsing issue
"""

import json

def test_current_response():
    """Test parsing the current problematic response"""
    
    # The current response that's failing
    response = '''[
    {"word":"toe","emoji_combo":"👣"},
    {"word":"gait","emoji_combo":"👣➡️"},
    {"word":"chamois","emoji_combo":"🐐"},
    {"word":"gall","emoji_combo":"🐴🦀"},
    {"word":"eye","emoji_combo":"👀"},
    {"word":"gawk","emoji_combo":"👀🔭"},
    {"word":"gun","emoji_combo":"⚙️"},
    {"word":"gear","emoji_combo":"⚙️💡"},
    {"word":"gal","emoji_combo":"👧🌸"},
    {"word":"girl","emoji_combo":"👧"},
    {"word":"bind","emoji_combo":"🔗"},
    {"word":"girt","emoji_combo":"🩹🧰"},
    {"word":"daft","emoji_combo":"🤡🎭"},
    {"word":"glop","emoji_combo":"🤢"},
    {"word":"bel","emoji_combo":"🔔🧩"},
    {"word":"gong","emoji_combo":"🔔"},
    {"word":"I","emoji_combo":"🧑"},
    {"word":"gook","emoji_combo":"👤🌎"},
    {"word":"welt","emoji_combo":"😳"},
    {"word":"gosh","emoji_combo":"😮🎉"},
    {"word":"own","emoji_combo":"📦💳"},
    {"word":"grab","emoji_combo":"🤲"},
    {"word":"cozy","emoji_combo":"🛋️🌙"},
    {"word":"rug","emoji_combo":"🛋️"},
    {"word":"keg","emoji_combo":"🥃"},
    {"word":"rum","emoji_combo":"🍸🥃"}
]'''
    
    print("Testing JSON parsing:")
    print("=" * 50)
    
    # Test basic JSON parsing
    try:
        parsed = json.loads(response)
        print(f"✅ JSON parsing successful! Found {len(parsed)} items")
        print(f"First item: {parsed[0]}")
        print(f"Last item: {parsed[-1]}")
        
        # Test conversion to word-emoji mappings
        word_to_emoji = {}
        for item in parsed:
            if isinstance(item, dict) and len(item) == 2:
                if "word" in item and "emoji_combo" in item:
                    word_to_emoji[item["word"]] = item["emoji_combo"]
        
        print(f"\n✅ Conversion successful! Found {len(word_to_emoji)} mappings")
        print("Sample mappings:")
        for i, (word, emoji) in enumerate(word_to_emoji.items()):
            print(f"  {word}: {emoji}")
            if i >= 4:  # Show first 5
                print(f"  ... and {len(word_to_emoji) - 5} more")
                break
                
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        print(f"Error at position {e.pos}")
        if hasattr(e, 'lineno'):
            print(f"Line {e.lineno}, Column {e.colno}")
        
        # Show the problematic area
        start = max(0, e.pos - 50)
        end = min(len(response), e.pos + 50)
        print(f"Context around error:")
        print(repr(response[start:end]))
        
        return False

if __name__ == "__main__":
    success = test_current_response()
    if not success:
        print("\n💡 The response looks like valid JSON. The issue might be elsewhere.")
