#!/usr/bin/env python3
"""
Test collision resolution format without OpenAI dependency
"""

def test_collision_format():
    """Test that collision format produces the right prompt"""
    from lib.collision_manager import CollisionManager
    from lib.config import COLLISION_RESOLUTION_PROMPT_TEMPLATE
    
    # Test collision formatting
    cm = CollisionManager()
    collisions = [('be', 'ken', '🧠'), ('by', 'axon', '🔗')]
    
    collisions_text = cm.format_collisions_for_prompt(collisions)
    print("Formatted collisions:")
    print(collisions_text)
    print()
    
    # Test prompt generation
    existing_emojis = "🧪, 🔬, 💻"
    prompt = COLLISION_RESOLUTION_PROMPT_TEMPLATE.format(
        collisions_text=collisions_text,
        existing_emojis=existing_emojis
    )
    
    print("Generated prompt (last 500 chars):")
    print("..." + prompt[-500:])
    print()
    
    # Verify the prompt asks for actual words
    assert "actual_word_from_conflict" in prompt
    assert "EXACT words mentioned in the conflicts" in prompt
    print("✅ Prompt correctly instructs to use actual words")

def test_response_parsing():
    """Test parsing a mock collision resolution response"""
    import json
    
    # Mock response using actual collision words
    mock_response = '''[
    {"be": "🧠"},
    {"ken": "👨‍💼"},
    {"by": "🔗"},
    {"axon": "🧠🔗"}
]'''
    
    # Test parsing
    parsed = json.loads(mock_response)
    print("Mock LLM response:")
    print(parsed)
    
    # Extract word mappings
    word_to_emoji = {}
    for item in parsed:
        if isinstance(item, dict) and len(item) == 1:
            word, emoji = next(iter(item.items()))
            if word and emoji:
                word_to_emoji[word] = emoji
    
    print("Extracted mappings:")
    print(word_to_emoji)
    
    # Verify we got the expected words
    expected_words = {'be', 'ken', 'by', 'axon'}
    actual_words = set(word_to_emoji.keys())
    assert expected_words == actual_words, f"Expected {expected_words}, got {actual_words}"
    print("✅ Extracted correct collision words")

if __name__ == "__main__":
    print("Testing collision resolution format...\n")
    test_collision_format()
    print()
    test_response_parsing()
    print("\n🎉 All tests passed!")
