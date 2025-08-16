#!/usr/bin/env python3
# Test Script for Semantic Validation System
# Demonstrates the validation capabilities with example mappings

import json
import os
from semantic_validator import SemanticValidator, ValidationStatus

def test_semantic_validation():
    """Test the semantic validation system with example mappings"""
    
    print("🧪 Testing Semantic Validation System")
    print("=" * 50)
    
    # Initialize validator
    print("Initializing validator...")
    validator = SemanticValidator()
    
    # Test mappings with varying quality levels
    test_mappings = {
        # High quality mappings (should score well)
        "cat": "🐱",           # Direct animal representation
        "sun": "☀️",           # Clear visual representation
        "happy": "😊",         # Direct emotional expression
        "fire": "🔥",          # Obvious visual match
        
        # Medium quality mappings
        "love": "❤️",          # Common but could conflict with 'heart'
        "book": "📚",          # Good but could be more specific
        "music": "🎵",         # Clear but musical note vs broader music
        
        # Potentially problematic mappings
        "algorithm": "🔀",     # Abstract concept, shuffle symbol
        "freedom": "🕊️",       # Metaphorical (dove = peace/freedom)
        "red": "❤️",           # Color represented by heart (conflicts with love)
        
        # Likely poor mappings (for testing)
        "computer": "🏠",      # Completely wrong (computer as house)
        "water": "🚗",         # No connection (water as car)
    }
    
    print(f"Testing {len(test_mappings)} mappings...\n")
    
    # Validate individual mappings
    print("📋 Individual Validation Results:")
    print("-" * 40)
    
    individual_results = {}
    for word, emoji in test_mappings.items():
        print(f"Validating: '{word}' → {emoji}")
        
        # Add some reasoning for better results
        reasoning = f"Mapping {word} to {emoji} for semantic representation"
        
        validation = validator.validate_single_mapping(word, emoji, reasoning)
        individual_results[word] = validation
        
        # Display summary
        status_emoji = {
            ValidationStatus.EXCELLENT: "🌟",
            ValidationStatus.GOOD: "✅", 
            ValidationStatus.ACCEPTABLE: "⚖️",
            ValidationStatus.WEAK: "⚠️",
            ValidationStatus.REJECTED: "❌"
        }
        
        print(f"  Result: {status_emoji.get(validation.status, '❓')} "
              f"{validation.status.value.upper()} "
              f"(Score: {validation.overall_score:.2f}/5.0)")
        
        if validation.issues:
            print(f"  Issues: {', '.join(validation.issues[:2])}")  # Show first 2 issues
        
        print()
    
    # Batch validation with consistency analysis
    print("📊 Batch Validation with Consistency Analysis:")
    print("-" * 50)
    
    batch_validations = validator.validate_mapping_batch(test_mappings)
    
    # Analyze results
    status_counts = {}
    total_score = 0
    
    for validation in batch_validations.values():
        status = validation.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
        total_score += validation.overall_score
    
    avg_score = total_score / len(batch_validations)
    
    print(f"Overall Results:")
    print(f"  Average Score: {avg_score:.2f}/5.0")
    print(f"  Status Distribution:")
    for status, count in status_counts.items():
        percentage = (count / len(batch_validations)) * 100
        print(f"    {status.capitalize()}: {count} ({percentage:.1f}%)")
    
    print()
    
    # Quality analysis
    print("📈 Quality Analysis:")
    print("-" * 30)
    
    quality_stats = validator.analyze_mapping_quality(test_mappings)
    
    print(f"Quality Summary:")
    print(f"  High Quality Rate: {quality_stats['quality_summary']['high_quality_rate']:.1f}%")
    print(f"  Acceptable Rate: {quality_stats['quality_summary']['acceptable_rate']:.1f}%")
    print(f"  Needs Improvement: {quality_stats['quality_summary']['needs_improvement_rate']:.1f}%")
    
    if quality_stats['recommendations']:
        print(f"\nRecommendations:")
        for rec in quality_stats['recommendations'][:3]:  # Show first 3
            print(f"  • {rec}")
    
    # Identify problematic mappings
    print("\n🚨 Problematic Mappings Identified:")
    print("-" * 40)
    
    problem_mappings = [
        (word, val) for word, val in batch_validations.items()
        if val.status in [ValidationStatus.WEAK, ValidationStatus.REJECTED]
    ]
    
    if problem_mappings:
        for word, validation in sorted(problem_mappings, key=lambda x: x[1].overall_score):
            print(f"❌ '{word}' → {validation.emoji}")
            print(f"   Score: {validation.overall_score:.2f}, Status: {validation.status.value}")
            if validation.alternative_suggestions:
                print(f"   Suggestion: {validation.alternative_suggestions[0]}")
            print()
    else:
        print("✅ No major problems identified!")
    
    # Consistency issues
    consistency_issues = [
        (word, val) for word, val in batch_validations.items()
        if val.consistency_notes
    ]
    
    if consistency_issues:
        print("⚖️ Consistency Issues:")
        print("-" * 25)
        for word, validation in consistency_issues:
            print(f"• {word} → {validation.emoji}")
            for note in validation.consistency_notes[:2]:  # Show first 2 notes
                print(f"  - {note}")
        print()
    
    # Save test results
    print("💾 Saving Test Results...")
    print("-" * 25)
    
    # Create test output directory
    test_output_dir = "test_validation_results"
    os.makedirs(test_output_dir, exist_ok=True)
    
    # Save validation results
    validator.save_validation_results(batch_validations, test_output_dir)
    
    # Save test summary
    test_summary = {
        "test_mappings": test_mappings,
        "average_score": avg_score,
        "status_distribution": status_counts,
        "quality_summary": quality_stats['quality_summary'],
        "problem_count": len(problem_mappings),
        "consistency_issues_count": len(consistency_issues)
    }
    
    with open(os.path.join(test_output_dir, "test_summary.json"), 'w') as f:
        json.dump(test_summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Test results saved to {test_output_dir}/")
    print("   • validation_report.md - Human-readable report")
    print("   • validation_results.json - Complete validation data")
    print("   • test_summary.json - Test execution summary")
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎯 SEMANTIC VALIDATION TEST COMPLETE")
    print("=" * 60)
    
    print(f"Tested: {len(test_mappings)} word-emoji mappings")
    print(f"Average Quality Score: {avg_score:.2f}/5.0")
    
    high_quality = status_counts.get('excellent', 0) + status_counts.get('good', 0)
    print(f"High Quality Mappings: {high_quality}/{len(test_mappings)} ({high_quality/len(test_mappings)*100:.1f}%)")
    
    if avg_score >= 4.0:
        print("🌟 Overall Quality: EXCELLENT")
    elif avg_score >= 3.0:
        print("✅ Overall Quality: GOOD")
    elif avg_score >= 2.0:
        print("⚠️ Overall Quality: NEEDS IMPROVEMENT") 
    else:
        print("❌ Overall Quality: POOR")
    
    print(f"\nDetailed analysis available in: {test_output_dir}/")
    print("\nNext steps:")
    print("• Review validation_report.md for detailed findings")
    print("• Address problematic mappings identified")
    print("• Consider applying suggested improvements")
    print("• Re-run validation after improvements")

if __name__ == "__main__":
    try:
        test_semantic_validation()
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print("Make sure the LLM server is running at http://127.0.0.1:1234")
        print("Or adjust the LLM URL in the semantic_validator.py configuration")
