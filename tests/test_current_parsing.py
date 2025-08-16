#!/usr/bin/env python3
"""
Test the current LLM parsing with the exact problematic response
"""

import json
import re
from typing import Dict, List, Any, Optional

def extract_json_from_markdown(text: str) -> List[str]:
    """Extract JSON blocks from markdown, trying different patterns"""
    blocks = []
    
    # 1) Look for ```json blocks first
    for m in re.finditer(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE):
        blocks.append(m.group(1))
    if blocks:
        return blocks

    # 2) Any fenced code blocks
    for m in re.finditer(r"```\w*\s*(.*?)\s*```", text, re.DOTALL):
        blocks.append(m.group(1))
    if blocks:
        return blocks
    
    # 3) Return the original text if no code blocks found
    return [text]

def parse_json_response(response_text: str) -> Optional[List[Dict[str, Any]]]:
    """Parse JSON array from LLM response, handling markdown code blocks"""
    if not response_text:
        return None
    
    # Extract JSON from markdown code blocks if present
    json_blocks = extract_json_from_markdown(response_text)
    
    # Try to parse JSON from extracted blocks
    for block in json_blocks:
        try:
            # Try to find JSON array in the block
            start_idx = block.find('[')
            end_idx = block.rfind(']') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = block[start_idx:end_idx]
                return json.loads(json_str)
        except json.JSONDecodeError:
            continue
    
    # Fallback to original method if markdown extraction failed
    start_idx = response_text.find('[')
    end_idx = response_text.rfind(']') + 1
    if start_idx >= 0 and end_idx > start_idx:
        json_str = response_text[start_idx:end_idx]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    return None

def parse_word_emoji_mappings(response_text: str) -> Optional[Dict[str, str]]:
    """Parse word-to-emoji mappings from LLM response"""
    parsed_response = parse_json_response(response_text)
    if parsed_response is None:
        print("❌ Failed to parse JSON response")
        return None
    
    word_to_emoji = {}
    for i, item in enumerate(parsed_response):
        if isinstance(item, dict):
            word_key = None
            emoji_key = None
            word_value = None
            emoji_value = None
            
            # Handle single key-value pair (expected format)
            if len(item) == 1:
                word, emoji = next(iter(item.items()))
                if word and emoji:
                    word_to_emoji[word] = emoji
                    continue
            
            # Handle multiple key-value pairs (malformed format)
            elif len(item) == 2:
                # Find word key (starts with 'w') and emoji key (starts with 'e')
                for key, value in item.items():
                    key_lower = key.lower()
                    if key_lower.startswith('w') and value:  # word, words, etc.
                        word_key = key
                        word_value = value
                    elif key_lower.startswith('e') and value:  # emoji, emoji_combo, emojis, etc.
                        emoji_key = key
                        emoji_value = value
                
                if word_value and emoji_value:
                    word_to_emoji[word_value] = emoji_value
                    print(f"✅ Recovered malformed response: {word_key}='{word_value}' -> {emoji_key}='{emoji_value}'")
                    continue
                else:
                    print(f"⚠️ Could not extract word/emoji from malformed item: {item}")
            else:
                print(f"⚠️ Unexpected response format in item {i}: {item}")
        else:
            print(f"⚠️ Non-dict item at index {i}: {item}")
    
    print(f"🔍 Successfully parsed {len(word_to_emoji)} word-emoji mappings")
    return word_to_emoji if word_to_emoji else None

def test_problematic_response():
    """Test the exact response that's failing"""
    
    problematic_response = '''[
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
]
2025-08-13 12:57:08,725 - INFO - ==================================================
2025-08-13 12:57:08,725 - INFO - ⏱️ LLM call took 128.38 seconds
2025-08-13 12:57:08,726 - ERROR - Failed to parse JSON response
2025-08-13 12:57:08,726 - ERROR - Error in LLM call (attempt 1): No valid word-emoji mappings found in response'''
    
    print("Testing problematic response parsing...")
    print("="*60)
    
    # Test step by step
    print("1. Testing JSON extraction...")
    json_blocks = extract_json_from_markdown(problematic_response)
    print(f"   Found {len(json_blocks)} JSON blocks")
    
    print("\n2. Testing JSON parsing...")
    parsed = parse_json_response(problematic_response)
    if parsed:
        print(f"   ✅ Successfully parsed JSON with {len(parsed)} items")
        print(f"   First item: {parsed[0]}")
        print(f"   Last item: {parsed[-1]}")
    else:
        print("   ❌ Failed to parse JSON")
        return False
    
    print("\n3. Testing word-emoji mapping extraction...")
    result = parse_word_emoji_mappings(problematic_response)
    
    if result:
        print(f"\n✅ SUCCESS! Parsed {len(result)} mappings:")
        for word, emoji in list(result.items())[:5]:  # Show first 5
            print(f"   {word}: {emoji}")
        if len(result) > 5:
            print(f"   ... and {len(result) - 5} more")
        return True
    else:
        print("\n❌ FAILED to extract word-emoji mappings")
        return False

if __name__ == "__main__":
    success = test_problematic_response()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
