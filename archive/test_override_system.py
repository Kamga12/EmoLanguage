#!/usr/bin/env python3
# Test Script for Manual Override System
# ✅ Validates core functionality without requiring LLM
# ✅ Tests data structures and integration points

import os
import json
import tempfile
import shutil
from typing import Dict, List
from manual_override_system import (
    ManualOverrideSystem, OverridePriority, OverrideStatus,
    OverrideEntry, OverrideAlternative
)

class MockLLMOverrideSystem(ManualOverrideSystem):
    """Mock version that doesn't require LLM for testing"""
    
    def generate_llm_alternatives(self, word: str, current_emoji: str, count: int = 5) -> List[OverrideAlternative]:
        """Generate mock alternatives for testing"""
        
        mock_alternatives = {
            'happy': [
                OverrideAlternative('😊', 'Smiling face with happy eyes', 'mock_llm', 0.95, 0.9, 0.9, 0.9, 'test_llm', '2025-01-06'),
                OverrideAlternative('🙂', 'Slightly smiling face', 'mock_llm', 0.8, 0.8, 0.85, 0.9, 'test_llm', '2025-01-06'),
                OverrideAlternative('😁', 'Beaming face with happy eyes', 'mock_llm', 0.85, 0.85, 0.8, 0.85, 'test_llm', '2025-01-06')
            ],
            'cat': [
                OverrideAlternative('🐱', 'Cat face', 'mock_llm', 0.98, 0.95, 0.95, 0.95, 'test_llm', '2025-01-06'),
                OverrideAlternative('🐈', 'Cat', 'mock_llm', 0.9, 0.9, 0.9, 0.9, 'test_llm', '2025-01-06'),
                OverrideAlternative('😺', 'Smiling cat', 'mock_llm', 0.75, 0.8, 0.7, 0.8, 'test_llm', '2025-01-06')
            ],
            'computer': [
                OverrideAlternative('💻', 'Laptop computer', 'mock_llm', 0.95, 0.95, 0.9, 0.9, 'test_llm', '2025-01-06'),
                OverrideAlternative('🖥️', 'Desktop computer', 'mock_llm', 0.85, 0.85, 0.85, 0.85, 'test_llm', '2025-01-06'),
                OverrideAlternative('⌨️', 'Keyboard', 'mock_llm', 0.6, 0.7, 0.8, 0.7, 'test_llm', '2025-01-06')
            ]
        }
        
        return mock_alternatives.get(word, [
            OverrideAlternative('🔤', f'Generic alternative for {word}', 'mock_llm', 0.5, 0.5, 0.5, 0.5, 'test_llm', '2025-01-06')
        ])

def test_basic_functionality():
    """Test basic override system functionality"""
    print("🧪 Testing basic functionality...")
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        mappings_dir = os.path.join(temp_dir, "mappings")
        override_dir = os.path.join(temp_dir, "manual_overrides")
        
        os.makedirs(mappings_dir, exist_ok=True)
        
        # Create test mapping file
        test_mappings = {
            "happy": "😀",
            "cat": "🐾",
            "computer": "⚙️",
            "love": "❤️",
            "dog": "🐕"
        }
        
        with open(os.path.join(mappings_dir, "word_to_emoji.json"), 'w') as f:
            json.dump(test_mappings, f)
        
        # Initialize mock system
        override_system = MockLLMOverrideSystem(mappings_dir, override_dir, "http://mock-llm:1234")
        
        print(f"✅ System initialized with {len(override_system.word_to_emoji)} mappings")
        
        # Test creating override entries
        print("\n🔧 Testing override entry creation...")
        
        entry1 = override_system.create_override_entry("happy", OverridePriority.CRITICAL)
        assert entry1.word == "happy"
        assert entry1.current_emoji == "😀"
        assert entry1.status == OverrideStatus.PENDING_REVIEW
        assert entry1.priority == OverridePriority.CRITICAL
        assert len(entry1.alternatives) > 0
        print(f"✅ Created override entry for 'happy' with {len(entry1.alternatives)} alternatives")
        
        entry2 = override_system.create_override_entry("cat")  # Auto-priority
        assert entry2.word == "cat"
        assert entry2.priority in [OverridePriority.CRITICAL, OverridePriority.HIGH, OverridePriority.MEDIUM, OverridePriority.LOW]
        print(f"✅ Created override entry for 'cat' with auto-priority: {entry2.priority.value}")
        
        # Test review functionality
        print("\n📝 Testing override review...")
        
        # Approve an override (select first alternative)
        selected_emoji = entry1.alternatives[0].emoji
        success = override_system.review_override("happy", selected_emoji, "Better semantic match", "test_reviewer")
        assert success
        
        reviewed_entry = override_system.override_entries["happy"]
        assert reviewed_entry.status == OverrideStatus.APPROVED
        assert reviewed_entry.selected_override == selected_emoji
        assert reviewed_entry.reviewed_by == "test_reviewer"
        print(f"✅ Successfully reviewed 'happy': {entry1.current_emoji} → {selected_emoji}")
        
        # Keep current mapping (which is actually approved with no change)
        success = override_system.review_override("cat", entry2.current_emoji, "Current mapping is fine", "test_reviewer")
        assert success
        
        reviewed_entry = override_system.override_entries["cat"]
        assert reviewed_entry.status == OverrideStatus.APPROVED  # It's approved, just no change
        assert reviewed_entry.selected_override == entry2.current_emoji  # Same as current
        print(f"✅ Successfully kept 'cat' current mapping")
        
        # Test export functionality
        print("\n📤 Testing export functionality...")
        
        approved_overrides = override_system.export_approved_overrides()
        assert "happy" in approved_overrides
        assert approved_overrides["happy"] == selected_emoji
        assert "cat" not in approved_overrides  # Rejected, so not exported
        print(f"✅ Exported {len(approved_overrides)} approved overrides")
        
        # Test save/load functionality
        print("\n💾 Testing save/load functionality...")
        
        override_system.save_all_data()
        
        # Verify files were created
        assert os.path.exists(os.path.join(override_dir, "override_entries.json"))
        assert os.path.exists(os.path.join(override_dir, "critical_words.json"))
        assert os.path.exists(os.path.join(override_dir, "override_statistics.json"))
        assert os.path.exists(os.path.join(mappings_dir, "manual_overrides.json"))
        print("✅ All data files created successfully")
        
        # Test loading
        new_system = MockLLMOverrideSystem(mappings_dir, override_dir, "http://mock-llm:1234")
        assert len(new_system.override_entries) == 2
        assert "happy" in new_system.override_entries
        assert "cat" in new_system.override_entries
        print("✅ Successfully loaded existing override entries")
        
        # Test statistics generation
        print("\n📊 Testing statistics generation...")
        
        stats = override_system._generate_statistics()
        assert stats["total_override_entries"] == 2
        assert stats["status_distribution"]["approved"] == 2  # Both were approved
        assert stats["status_distribution"].get("rejected", 0) == 0  # None rejected
        assert stats["approved_improvements"] == 1  # Only one was actually a change
        print(f"✅ Generated statistics: {stats['total_override_entries']} entries, {stats['completion_rate']:.1f}% complete")
        
        # Test report generation
        print("\n📄 Testing report generation...")
        
        report = override_system.generate_report()
        assert "Manual Override System Report" in report
        assert "happy" in report
        print("✅ Generated system report successfully")
        
        print("\n🎉 All basic functionality tests passed!")

def test_high_frequency_identification():
    """Test high-frequency word identification"""
    print("\n🧪 Testing high-frequency word identification...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        mappings_dir = os.path.join(temp_dir, "mappings")
        override_dir = os.path.join(temp_dir, "manual_overrides")
        
        os.makedirs(mappings_dir, exist_ok=True)
        
        # Create test mapping with known high-frequency words
        test_mappings = {
            "the": "🔷",
            "and": "➕", 
            "happy": "😊",
            "cat": "🐱",
            "love": "❤️",
            "computer": "💻",
            "run": "🏃",
            "red": "🔴",
            "obscure": "🔤",  # Low frequency word
            "xylophone": "🎵"  # Very low frequency word
        }
        
        with open(os.path.join(mappings_dir, "word_to_emoji.json"), 'w') as f:
            json.dump(test_mappings, f)
        
        override_system = MockLLMOverrideSystem(mappings_dir, override_dir, "http://mock-llm:1234")
        
        # Check critical word identification
        critical_words = override_system.critical_words
        
        # High-frequency words should be in critical list
        high_freq_in_critical = [word for word in ["the", "and", "happy", "cat", "love", "red"] if word in critical_words]
        assert len(high_freq_in_critical) > 0, "Some high-frequency words should be identified as critical"
        
        # Check that emotion words are included
        emotion_words_in_critical = [word for word in ["happy", "love"] if word in critical_words]
        assert len(emotion_words_in_critical) > 0, "Emotion words should be in critical list"
        
        print(f"✅ Identified {len(critical_words)} critical words")
        print(f"   High-frequency words in critical: {high_freq_in_critical}")
        print(f"   Total critical emotion words: {len(emotion_words_in_critical)}")

def test_batch_operations():
    """Test batch creation of overrides"""
    print("\n🧪 Testing batch operations...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        mappings_dir = os.path.join(temp_dir, "mappings")
        override_dir = os.path.join(temp_dir, "manual_overrides")
        
        os.makedirs(mappings_dir, exist_ok=True)
        
        # Create test mappings for batch operations
        test_mappings = {}
        # Add some high-priority words that should be in critical list
        critical_test_words = ["happy", "sad", "cat", "dog", "run", "walk", "red", "blue", "computer", "phone"]
        for i, word in enumerate(critical_test_words):
            test_mappings[word] = f"🔤{i}"  # Dummy emoji
        
        with open(os.path.join(mappings_dir, "word_to_emoji.json"), 'w') as f:
            json.dump(test_mappings, f)
        
        override_system = MockLLMOverrideSystem(mappings_dir, override_dir, "http://mock-llm:1234")
        
        # Test batch creation
        initial_count = len(override_system.override_entries)
        created_count = override_system.batch_create_critical_overrides(limit=5)
        
        assert created_count > 0, "Should create some override entries"
        assert len(override_system.override_entries) == initial_count + created_count
        
        print(f"✅ Batch created {created_count} override entries")
        
        # Verify created entries have correct priority
        critical_entries = [entry for entry in override_system.override_entries.values() 
                           if entry.priority == OverridePriority.CRITICAL]
        assert len(critical_entries) > 0, "Should have created some critical priority entries"
        
        print(f"✅ Created {len(critical_entries)} critical priority entries")

def run_all_tests():
    """Run all tests"""
    print("🚀 Running Manual Override System Tests")
    print("=" * 50)
    
    try:
        test_basic_functionality()
        test_high_frequency_identification() 
        test_batch_operations()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED! Manual Override System is working correctly.")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    return True

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
