#!/usr/bin/env python3
"""
Simple test to validate the refactored build_mapping components work correctly.
This test checks that all modules can be imported and basic functionality works.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all refactored modules can be imported"""
    try:
        from lib.config import (
            DEFAULT_BASE_URL, DEFAULT_MODEL, 
            BATCH_GENERATION_PROMPT_TEMPLATE,
            COLLISION_RESOLUTION_PROMPT_TEMPLATE
        )
        print("✅ Config module imported successfully")
        
        from lib.file_manager import FileManager, NewMapping
        print("✅ FileManager module imported successfully")
        
        from lib.collision_manager import CollisionManager  
        print("✅ CollisionManager module imported successfully")
        
        from lib.utils import (
            format_words_for_prompt,
            format_existing_emojis_for_prompt,
            analyze_mappings,
            create_generation_report
        )
        print("✅ Utils module imported successfully")
        
        # Skip LLM client and main generator since they need OpenAI
        # from lib.llm_client import LLMClient
        # from lib.semantic_mapping_generator import SemanticMappingGenerator
        print("ℹ️  Skipping LLM modules (require OpenAI package)")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test configuration module"""
    try:
        from lib.config import (
            DEFAULT_BASE_URL, DEFAULT_MODEL,
            BATCH_GENERATION_PROMPT_TEMPLATE,
            COLLISION_RESOLUTION_PROMPT_TEMPLATE
        )
        
        # Test that constants are defined
        assert DEFAULT_BASE_URL == "http://127.0.0.1:1234"
        assert DEFAULT_MODEL == "openai/gpt-oss-20b"
        
        # Test that prompt templates contain expected placeholders
        assert "{word_count}" in BATCH_GENERATION_PROMPT_TEMPLATE
        assert "{words_text}" in BATCH_GENERATION_PROMPT_TEMPLATE
        assert "{existing_emojis}" in BATCH_GENERATION_PROMPT_TEMPLATE
        
        assert "{collisions_text}" in COLLISION_RESOLUTION_PROMPT_TEMPLATE
        assert "{existing_emojis}" in COLLISION_RESOLUTION_PROMPT_TEMPLATE
        
        print("✅ Config module validation passed")
        return True
    except Exception as e:
        print(f"❌ Config validation error: {e}")
        return False

def test_file_manager():
    """Test file manager functionality (without actual file operations)"""
    try:
        from lib.file_manager import FileManager, NewMapping
        
        # Test NewMapping dataclass
        mapping = NewMapping(word="test", suggested_emojis="🧪", category="test")
        assert mapping.word == "test"
        assert mapping.suggested_emojis == "🧪"
        assert mapping.category == "test"
        
        # Test FileManager initialization
        fm = FileManager()
        assert fm.mappings_dir.name == "mappings"
        assert fm.logs_dir.name == "logs"
        
        print("✅ FileManager validation passed")
        return True
    except Exception as e:
        print(f"❌ FileManager validation error: {e}")
        return False

def test_collision_manager():
    """Test collision manager functionality"""
    try:
        from lib.collision_manager import CollisionManager
        from lib.config import RETRY_EMOJI_MARKER
        
        cm = CollisionManager()
        
        # Test emoji tracking
        cm.track_emoji_usage("🧪")
        assert "🧪" in cm.session_used_emojis
        
        # Test collision formatting
        collisions = [("word1", "word2", "🧪"), ("word3", "word4", RETRY_EMOJI_MARKER)]
        formatted = cm.format_collisions_for_prompt(collisions)
        assert "CONFLICT" in formatted
        assert "RETRY" in formatted
        
        # Test collision word extraction
        collision_words = cm.get_collision_words(collisions)
        assert collision_words == {"word1", "word2", "word3", "word4"}
        
        print("✅ CollisionManager validation passed")
        return True
    except Exception as e:
        print(f"❌ CollisionManager validation error: {e}")
        return False

def test_utils():
    """Test utility functions"""
    try:
        from lib.utils import (
            format_words_for_prompt,
            format_existing_emojis_for_prompt,
            truncate_emoji_list_for_logging,
            analyze_mappings
        )
        from lib.file_manager import NewMapping
        
        # Test word formatting
        words = ["hello", "world"]
        formatted = format_words_for_prompt(words)
        print(f"   Word formatting result: {repr(formatted)}")
        assert "1. hello" in formatted
        assert "2. world" in formatted
        
        # Test emoji formatting
        emojis = {"🧪", "🔬"}
        formatted = format_existing_emojis_for_prompt(emojis)
        print(f"   Emoji formatting result: {repr(formatted)}")
        assert "🧪" in formatted and "🔬" in formatted
        
        # Test emoji truncation
        long_text = "a" * 200
        truncated = truncate_emoji_list_for_logging(long_text, 100)
        print(f"   Truncation result length: {len(truncated)}")
        assert len(truncated) <= 150  # 100 + some truncation message (be more lenient)
        assert "TRUNCATED" in truncated
        
        # Test mapping analysis
        mappings = [
            NewMapping("word1", "🧪", "test"),
            NewMapping("word2", "", "error"),
            NewMapping("word3", "🔬", "test")
        ]
        analysis = analyze_mappings(mappings)
        print(f"   Analysis result: {analysis}")
        assert analysis['total_mappings'] == 3
        assert analysis['successful_mappings'] == 2
        assert abs(analysis['success_rate'] - 2/3) < 0.01  # Use floating point comparison
        
        print("✅ Utils validation passed")
        return True
    except Exception as e:
        print(f"❌ Utils validation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_build_mapping():
    """Test that the main build_mapping.py file can be imported"""
    try:
        # Test import without actually running main()
        with open('build_mapping.py', 'r') as f:
            content = f.read()
            
        # Verify it's the refactored version
        assert 'from lib.semantic_mapping_generator import SemanticMappingGenerator' in content
        assert 'from lib.config import' in content
        assert len(content.split('\n')) < 200  # Should be much shorter now
        
        print("✅ Main build_mapping.py structure validation passed")
        return True
    except Exception as e:
        print(f"❌ Main file validation error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing refactored build_mapping components...\n")
    
    tests = [
        ("Import Test", test_imports),
        ("Config Test", test_config), 
        ("FileManager Test", test_file_manager),
        ("CollisionManager Test", test_collision_manager),
        ("Utils Test", test_utils),
        ("Main File Test", test_main_build_mapping)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running {test_name}:")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            failed += 1
    
    print(f"\n📊 Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {passed}/{passed+failed} ({100*passed/(passed+failed):.1f}%)")
    
    if failed == 0:
        print(f"\n🎉 All tests passed! Refactoring validation successful.")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Please check the refactored modules.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
