#!/usr/bin/env python3
"""
Debug the LLM client parsing specifically
"""

import sys
import os
import json

# Add the lib directory to the path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

def test_llm_client_parsing():
    """Test the LLM client parsing with the problematic response"""
    
    try:
        from llm_client import LLMClient
    except ImportError as e:
        print(f"Cannot import LLMClient: {e}")
        return False
    
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
    
    print("Testing LLMClient parsing:")
    print("=" * 50)
    
    client = LLMClient()
    
    # Test the internal JSON response parsing
    print("1. Testing _parse_json_response...")
    parsed_json = client._parse_json_response(response)
    if parsed_json:
        print(f"✅ _parse_json_response succeeded! Found {len(parsed_json)} items")
        print(f"First item: {parsed_json[0]}")
    else:
        print("❌ _parse_json_response failed!")
        return False
    
    # Test the full word-emoji mapping parser
    print("\n2. Testing parse_word_emoji_mappings...")
    word_mappings = client.parse_word_emoji_mappings(response)
    if word_mappings:
        print(f"✅ parse_word_emoji_mappings succeeded! Found {len(word_mappings)} mappings")
        print("Sample mappings:")
        for i, (word, emoji) in enumerate(word_mappings.items()):
            print(f"  {word}: {emoji}")
            if i >= 4:  # Show first 5
                print(f"  ... and {len(word_mappings) - 5} more")
                break
        return True
    else:
        print("❌ parse_word_emoji_mappings failed!")
        return False

if __name__ == "__main__":
    try:
        success = test_llm_client_parsing()
        if success:
            print("\n🎉 LLMClient parsing works correctly!")
        else:
            print("\n💥 LLMClient parsing failed!")
    except Exception as e:
        print(f"\n💥 Error during testing: {e}")
        import traceback
        traceback.print_exc()
