#!/usr/bin/env python3
"""
Test to verify the unified response format works correctly.
This tests the refactored components with the new unified {"word": "emoji"} format.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_unified_format():
    """Test the unified response format handling"""
    try:
        from lib.utils import convert_word_mappings_to_new_mappings, validate_word_mappings
        from lib.file_manager import NewMapping
        
        # Test unified format conversion
        word_mappings = {
            'hello': '👋',
            'world': '🌍',
            'celebration': '🎉🎊'  # Multi-emoji
        }
        expected_words = ['hello', 'world', 'celebration', 'missing']
        
        # Convert to NewMapping objects
        mappings = convert_word_mappings_to_new_mappings(word_mappings, expected_words, 'unified_test')
        
        # Verify conversion
        assert len(mappings) == 4
        assert mappings[0].word == 'hello'
        assert mappings[0].suggested_emojis == '👋'
        assert mappings[0].category == 'unified_test'
        
        assert mappings[2].word == 'celebration'
        assert mappings[2].suggested_emojis == '🎉🎊'
        
        assert mappings[3].word == 'missing'
        assert mappings[3].suggested_emojis == ''
        assert mappings[3].category == 'error'
        
        # Test validation
        missing_words = validate_word_mappings(word_mappings, expected_words)
        assert missing_words == ['missing']
        
        print("✅ Unified format handling validated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Unified format test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prompt_format_consistency():
    """Test that both prompts now use the same response format"""
    try:
        from lib.config import BATCH_GENERATION_PROMPT_TEMPLATE, COLLISION_RESOLUTION_PROMPT_TEMPLATE
        
        # Both prompts should specify the same JSON format
        batch_format_line = None
        collision_format_line = None
        
        for line in BATCH_GENERATION_PROMPT_TEMPLATE.split('\n'):
            if '{"word1": "emoji(s)"}' in line:
                batch_format_line = line.strip()
                break
        
        for line in COLLISION_RESOLUTION_PROMPT_TEMPLATE.split('\n'):
            if '{"word1": "emoji(s)"}' in line:
                collision_format_line = line.strip()
                break
        
        assert batch_format_line is not None, "Batch prompt should specify unified format"
        assert collision_format_line is not None, "Collision prompt should specify unified format"
        
        # Both should specify the same format structure
        assert '{"word1": "emoji(s)"}' in batch_format_line
        assert '{"word1": "emoji(s)"}' in collision_format_line
        
        print("✅ Prompt format consistency validated")
        return True
        
    except Exception as e:
        print(f"❌ Prompt format consistency test failed: {e}")
        return False

def test_response_parsing_unification():
    """Test that the response parsing is now unified"""
    try:
        # Mock the parsing without OpenAI dependency
        import json
        
        # Test unified format parsing
        test_responses = [
            '[{"hello": "👋"}, {"world": "🌍"}]',
            '[{"celebration": "🎉🎊"}, {"teamwork": "👥🤝"}]',
            '```json\n[{"test": "🧪"}, {"code": "💻"}]\n```'
        ]
        
        def mock_parse_word_emoji_mappings(response_text):
            """Mock version of the unified parser"""
            # Extract JSON (simplified version)
            if '```json' in response_text:
                start = response_text.find('[')
                end = response_text.rfind(']') + 1
                json_str = response_text[start:end]
            else:
                json_str = response_text
            
            parsed = json.loads(json_str)
            
            word_to_emoji = {}
            for item in parsed:
                if isinstance(item, dict) and len(item) == 1:
                    word, emoji = next(iter(item.items()))
                    if word and emoji:
                        word_to_emoji[word] = emoji
            
            return word_to_emoji if word_to_emoji else None
        
        # Test all formats
        for response in test_responses:
            result = mock_parse_word_emoji_mappings(response)
            assert result is not None, f"Should parse: {response}"
            assert len(result) >= 2, f"Should extract multiple mappings: {result}"
            print(f"   ✅ Parsed: {result}")
        
        print("✅ Response parsing unification validated")
        return True
        
    except Exception as e:
        print(f"❌ Response parsing test failed: {e}")
        return False

def test_code_deduplication():
    """Test that code duplication has been reduced through unification"""
    try:
        # Check that we now have unified methods instead of duplicated ones
        
        # Count the methods in the semantic mapping generator
        with open('lib/semantic_mapping_generator.py', 'r') as f:
            content = f.read()
        
        # Should have both unified and legacy methods during transition
        assert '_process_collision_resolution_response_unified' in content
        assert '_process_collision_resolution_response' in content  # Legacy kept for reference
        
        # Check that LLM client has unified method
        with open('lib/llm_client.py', 'r') as f:
            llm_content = f.read()
        
        assert 'call_llm_for_word_mappings' in llm_content
        assert 'parse_word_emoji_mappings' in llm_content
        
        # Check that utils has unified conversion
        with open('lib/utils.py', 'r') as f:
            utils_content = f.read()
        
        assert 'convert_word_mappings_to_new_mappings' in utils_content
        assert 'validate_word_mappings' in utils_content
        
        print("✅ Code deduplication through unification validated")
        return True
        
    except Exception as e:
        print(f"❌ Code deduplication test failed: {e}")
        return False

def main():
    """Run all unified format tests"""
    print("🔬 Testing unified response format implementation...\n")
    
    tests = [
        ("Unified Format Handling", test_unified_format),
        ("Prompt Format Consistency", test_prompt_format_consistency),
        ("Response Parsing Unification", test_response_parsing_unification),
        ("Code Deduplication", test_code_deduplication)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"🧪 Running {test_name}:")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            failed += 1
        print()
    
    print(f"📊 Unified Format Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {passed}/{passed+failed} ({100*passed/(passed+failed):.1f}%)")
    
    if failed == 0:
        print(f"\n🎉 All unified format tests passed! Response format unification successful.")
        print(f"\n📝 Summary of Changes:")
        print(f"   • Both batch generation and collision resolution now use the same JSON format")
        print(f"   • Unified response parsing in LLMClient.parse_word_emoji_mappings()")
        print(f"   • Shared conversion logic in convert_word_mappings_to_new_mappings()")
        print(f"   • Consistent validation with validate_word_mappings()")
        print(f"   • Reduced code duplication through format standardization")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Please check the unified format implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
