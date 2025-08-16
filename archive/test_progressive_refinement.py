#!/usr/bin/env python3
# Test Progressive Refinement System
# ✅ Tests the refinement system with a small sample
# ✅ Verifies all components work together
# ✅ Provides safe testing without affecting main mappings

import json
import logging
import os
from progressive_refinement import ProgressiveRefinementSystem
from refinement_integration import RefinementIntegration

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_mappings():
    """Create a small test set of mappings for testing"""
    test_mappings = {
        "happy": "😊",
        "computer": "💻", 
        "cat": "🐱",
        "run": "🏃",
        "love": "❤️",
        "book": "📚",
        "tree": "🌳",
        "water": "💧",
        "sun": "☀️",
        "music": "🎵",
        "fire": "🔥",
        "house": "🏠",
        "car": "🚗",
        "food": "🍽️",
        "sleep": "😴"
    }
    
    # Create test directory
    test_dir = "test_mappings"
    os.makedirs(test_dir, exist_ok=True)
    
    # Save test mappings
    test_file = os.path.join(test_dir, "word_to_emoji.json")
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_mappings, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Created test mappings file: {test_file}")
    return test_file, test_mappings

def test_refinement_system():
    """Test the progressive refinement system"""
    logger.info("🧪 Testing Progressive Refinement System")
    
    # Create test mappings
    test_file, test_mappings = create_test_mappings()
    
    try:
        # Initialize refinement system
        refinement_system = ProgressiveRefinementSystem()
        
        # Test individual components
        logger.info("Testing readability test generation...")
        test_cases = refinement_system.generate_readability_tests("happy", "😊", num_tests=2)
        logger.info(f"Generated {len(test_cases)} readability tests")
        
        if test_cases:
            logger.info(f"Sample test: {test_cases[0].sentence_english} → {test_cases[0].sentence_emoji}")
        
        # Test a small refinement run
        logger.info("Testing refinement iteration...")
        small_sample = dict(list(test_mappings.items())[:5])  # Use only 5 mappings
        
        iteration_result = refinement_system.run_refinement_iteration(small_sample)
        
        logger.info("✅ Refinement iteration completed successfully!")
        logger.info(f"Processed {iteration_result.mappings_reviewed} mappings")
        logger.info(f"Found {iteration_result.problems_identified} problems")
        logger.info(f"Generated {iteration_result.improvements_suggested} improvement suggestions")
        logger.info(f"Average readability score: {iteration_result.avg_readability_score:.2f}")
        
        # Save test results
        refinement_system.save_refinement_results({
            "test_iteration": iteration_result.__dict__,
            "final_problems": dict(refinement_system.problematic_mappings),
            "final_improvements": {
                word: [improvement.__dict__ for improvement in improvements]
                for word, improvements in refinement_system.improvement_suggestions.items()
            },
            "manual_review_queue": refinement_system.manual_review_queue,
            "recommendations": ["This was a test run"]
        }, output_dir="test_refinement_results")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

def test_integration_system():
    """Test the refinement integration system (without actual LLM calls)"""
    logger.info("🧪 Testing Refinement Integration System")
    
    try:
        # Initialize integration system
        integration = RefinementIntegration()
        
        # Test configuration
        logger.info(f"Integration config: {integration.config}")
        
        # Create a mock improvement for testing
        from progressive_refinement import MappingImprovement
        mock_improvement = MappingImprovement(
            word="test",
            current_emoji="🤖",
            suggested_emoji="🧪", 
            reasoning="Test improvement",
            expected_improvement=1.0,
            confidence=0.9,
            validation_needed=False
        )
        
        # Test threshold checking
        should_apply = integration._should_apply_improvement(mock_improvement)
        logger.info(f"Mock improvement should be applied: {should_apply}")
        
        # Test rejection reason generation
        low_confidence_improvement = MappingImprovement(
            word="test2",
            current_emoji="🤖",
            suggested_emoji="🧪",
            reasoning="Low confidence test",
            expected_improvement=0.8,
            confidence=0.3,  # Below threshold
            validation_needed=False
        )
        
        rejection_reason = integration._get_rejection_reason(low_confidence_improvement)
        logger.info(f"Rejection reason for low confidence: {rejection_reason}")
        
        logger.info("✅ Integration system basic tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Starting Progressive Refinement System Tests")
    
    # Test refinement system
    refinement_success = test_refinement_system()
    
    # Test integration system
    integration_success = test_integration_system()
    
    # Summary
    logger.info("=" * 50)
    logger.info("TEST SUMMARY:")
    logger.info(f"✅ Refinement System: {'PASS' if refinement_success else 'FAIL'}")
    logger.info(f"✅ Integration System: {'PASS' if integration_success else 'FAIL'}")
    
    if refinement_success and integration_success:
        logger.info("🎉 All tests passed! Progressive Refinement System is ready.")
        logger.info("")
        logger.info("To run with real mappings:")
        logger.info("  python progressive_refinement.py")
        logger.info("  python refinement_integration.py")
        logger.info("")
        logger.info("Check test_refinement_results/ for test output")
    else:
        logger.error("❌ Some tests failed. Please check the errors above.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
