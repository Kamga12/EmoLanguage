#!/usr/bin/env python3
"""
Word Normalization Semantic Completeness Test

This test focuses specifically on validating that the word normalization/lemmatization
system maintains semantic completeness by testing transformation pairs and edge cases.

Usage:
    python3 documents/word_normalization_semantic_test.py
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from word_normalizer import WordNormalizer

class WordNormalizationSemanticTest:
    def __init__(self):
        """Initialize the word normalization semantic test"""
        self.normalizer = WordNormalizer()
        
    def create_comprehensive_test_pairs(self) -> List[Dict]:
        """Create comprehensive test pairs for semantic completeness validation"""
        return [
            # CATEGORY 1: ALWAYS ELIMINATE (Should normalize to base form)
            
            # Regular plurals
            {"base": "cat", "transformed": "cats", "type": "plural_regular", 
             "should_normalize": True, "semantic_impact": "low", "rule": "always_eliminate"},
            {"base": "dog", "transformed": "dogs", "type": "plural_regular", 
             "should_normalize": True, "semantic_impact": "low", "rule": "always_eliminate"},
            {"base": "book", "transformed": "books", "type": "plural_regular", 
             "should_normalize": True, "semantic_impact": "low", "rule": "always_eliminate"},
            {"base": "house", "transformed": "houses", "type": "plural_regular", 
             "should_normalize": True, "semantic_impact": "low", "rule": "always_eliminate"},
            
            # Past tense regular
            {"base": "walk", "transformed": "walked", "type": "past_regular", 
             "should_normalize": True, "semantic_impact": "low", "rule": "always_eliminate"},
            {"base": "play", "transformed": "played", "type": "past_regular", 
             "should_normalize": True, "semantic_impact": "low", "rule": "always_eliminate"},
            {"base": "work", "transformed": "worked", "type": "past_regular", 
             "should_normalize": True, "semantic_impact": "low", "rule": "always_eliminate"},
            
            # Present continuous
            {"base": "run", "transformed": "running", "type": "progressive", 
             "should_normalize": True, "semantic_impact": "low", "rule": "always_eliminate"},
            {"base": "walk", "transformed": "walking", "type": "progressive", 
             "should_normalize": True, "semantic_impact": "low", "rule": "always_eliminate"},
            {"base": "think", "transformed": "thinking", "type": "progressive", 
             "should_normalize": True, "semantic_impact": "low", "rule": "always_eliminate"},
            
            # Third person singular
            {"base": "run", "transformed": "runs", "type": "third_person", 
             "should_normalize": True, "semantic_impact": "low", "rule": "always_eliminate"},
            {"base": "walk", "transformed": "walks", "type": "third_person", 
             "should_normalize": True, "semantic_impact": "low", "rule": "always_eliminate"},
            {"base": "think", "transformed": "thinks", "type": "third_person", 
             "should_normalize": True, "semantic_impact": "low", "rule": "always_eliminate"},
            
            # CATEGORY 2: CASE-BY-CASE EVALUATION
            
            # Irregular plurals (semantic significance varies)
            {"base": "child", "transformed": "children", "type": "plural_irregular", 
             "should_normalize": False, "semantic_impact": "medium", "rule": "case_by_case",
             "reasoning": "Different connotations - collective vs individual"},
            {"base": "person", "transformed": "people", "type": "plural_irregular", 
             "should_normalize": False, "semantic_impact": "medium", "rule": "case_by_case",
             "reasoning": "Collective meaning vs individual"},
            {"base": "foot", "transformed": "feet", "type": "plural_irregular", 
             "should_normalize": True, "semantic_impact": "low", "rule": "case_by_case",
             "reasoning": "Same core concept"},
            {"base": "mouse", "transformed": "mice", "type": "plural_irregular", 
             "should_normalize": True, "semantic_impact": "low", "rule": "case_by_case",
             "reasoning": "Same core concept"},
            
            # Adverbs with -ly (semantic shift varies)
            {"base": "quick", "transformed": "quickly", "type": "adverb_manner", 
             "should_normalize": True, "semantic_impact": "low", "rule": "case_by_case",
             "reasoning": "Just manner of being quick"},
            {"base": "slow", "transformed": "slowly", "type": "adverb_manner", 
             "should_normalize": True, "semantic_impact": "low", "rule": "case_by_case",
             "reasoning": "Just manner of being slow"},
            {"base": "hard", "transformed": "hardly", "type": "adverb_semantic_shift", 
             "should_normalize": False, "semantic_impact": "high", "rule": "case_by_case",
             "reasoning": "Completely different meaning"},
            {"base": "late", "transformed": "lately", "type": "adverb_semantic_shift", 
             "should_normalize": False, "semantic_impact": "high", "rule": "case_by_case",
             "reasoning": "Temporal vs descriptive meaning"},
            
            # Comparatives and superlatives
            {"base": "big", "transformed": "bigger", "type": "comparative", 
             "should_normalize": True, "semantic_impact": "low", "rule": "case_by_case",
             "reasoning": "Degree information can be captured elsewhere"},
            {"base": "fast", "transformed": "fastest", "type": "superlative", 
             "should_normalize": True, "semantic_impact": "low", "rule": "case_by_case",
             "reasoning": "Degree information can be captured elsewhere"},
            {"base": "good", "transformed": "better", "type": "irregular_comparative", 
             "should_normalize": False, "semantic_impact": "medium", "rule": "case_by_case",
             "reasoning": "Lexicalized form with distinct usage"},
            {"base": "good", "transformed": "best", "type": "irregular_superlative", 
             "should_normalize": False, "semantic_impact": "medium", "rule": "case_by_case",
             "reasoning": "Lexicalized form with distinct usage"},
            
            # CATEGORY 3: ALWAYS PRESERVE (Should NOT normalize)
            
            # Opposites/Negation
            {"base": "happy", "transformed": "unhappy", "type": "negation_prefix", 
             "should_normalize": False, "semantic_impact": "high", "rule": "always_preserve",
             "reasoning": "Creates antonym with distinct meaning"},
            {"base": "possible", "transformed": "impossible", "type": "negation_prefix", 
             "should_normalize": False, "semantic_impact": "high", "rule": "always_preserve",
             "reasoning": "Creates antonym with distinct meaning"},
            {"base": "legal", "transformed": "illegal", "type": "negation_prefix", 
             "should_normalize": False, "semantic_impact": "high", "rule": "always_preserve",
             "reasoning": "Creates antonym with distinct meaning"},
            {"base": "hope", "transformed": "hopeless", "type": "negation_suffix", 
             "should_normalize": False, "semantic_impact": "high", "rule": "always_preserve",
             "reasoning": "Creates antonym with distinct meaning"},
            
            # Role/Agent transformations
            {"base": "teach", "transformed": "teacher", "type": "agent_noun", 
             "should_normalize": False, "semantic_impact": "high", "rule": "always_preserve",
             "reasoning": "Person who teaches vs action"},
            {"base": "write", "transformed": "writer", "type": "agent_noun", 
             "should_normalize": False, "semantic_impact": "high", "rule": "always_preserve",
             "reasoning": "Person vs action"},
            {"base": "piano", "transformed": "pianist", "type": "agent_specialist", 
             "should_normalize": False, "semantic_impact": "high", "rule": "always_preserve",
             "reasoning": "Person vs instrument"},
            {"base": "library", "transformed": "librarian", "type": "agent_specialist", 
             "should_normalize": False, "semantic_impact": "high", "rule": "always_preserve",
             "reasoning": "Person vs place"},
            
            # State/Quality transformations
            {"base": "happy", "transformed": "happiness", "type": "quality_noun", 
             "should_normalize": False, "semantic_impact": "high", "rule": "always_preserve",
             "reasoning": "State vs quality distinction"},
            {"base": "complex", "transformed": "complexity", "type": "quality_noun", 
             "should_normalize": False, "semantic_impact": "high", "rule": "always_preserve",
             "reasoning": "Abstract concept vs adjective"},
            {"base": "move", "transformed": "movement", "type": "action_noun", 
             "should_normalize": False, "semantic_impact": "high", "rule": "always_preserve",
             "reasoning": "Concept vs action"},
            {"base": "create", "transformed": "creation", "type": "action_noun", 
             "should_normalize": False, "semantic_impact": "high", "rule": "always_preserve",
             "reasoning": "Result vs action"},
            
            # EDGE CASES AND SPECIAL SCENARIOS
            
            # Compound transformations (multiple suffixes)
            {"base": "happy", "transformed": "unhappiness", "type": "compound_transform", 
             "should_normalize": False, "semantic_impact": "high", "rule": "special_case",
             "reasoning": "Both negation and state transformation preserved"},
            {"base": "care", "transformed": "uncaring", "type": "compound_transform", 
             "should_normalize": False, "semantic_impact": "high", "rule": "special_case",
             "reasoning": "Negation of agent-like adjective"},
            
            # Context-dependent cases
            {"base": "bank", "transformed": "banks", "type": "homonym_plural", 
             "should_normalize": True, "semantic_impact": "low", "rule": "context_dependent",
             "reasoning": "Same for both river bank and financial bank"},
            {"base": "bear", "transformed": "bears", "type": "homonym_plural", 
             "should_normalize": True, "semantic_impact": "low", "rule": "context_dependent",
             "reasoning": "Same for both animal and verb meanings"},
            
            # Technical/Domain-specific
            {"base": "datum", "transformed": "data", "type": "technical_plural", 
             "should_normalize": False, "semantic_impact": "medium", "rule": "domain_specific",
             "reasoning": "Plural is standard form in common usage"},
            {"base": "formula", "transformed": "formulas", "type": "technical_plural", 
             "should_normalize": True, "semantic_impact": "low", "rule": "domain_specific",
             "reasoning": "Regular plural pattern"},
        ]
    
    def test_normalization_rules(self, test_pairs: List[Dict]) -> Dict:
        """Test normalization behavior against expected rules"""
        results = {
            "total_pairs": len(test_pairs),
            "correct_decisions": 0,
            "incorrect_decisions": 0,
            "results_by_rule": defaultdict(list),
            "results_by_impact": defaultdict(list),
            "incorrect_examples": []
        }
        
        for pair in test_pairs:
            base_word = pair["base"]
            transformed_word = pair["transformed"]
            should_normalize = pair["should_normalize"]
            semantic_impact = pair["semantic_impact"]
            rule_type = pair["rule"]
            
            # Test normalization
            normalized_base = self.normalizer.normalize_word(base_word)
            normalized_transformed = self.normalizer.normalize_word(transformed_word)
            
            # Check if transformation was normalized
            was_normalized = normalized_base == normalized_transformed
            
            # Determine if decision was correct
            correct_decision = was_normalized == should_normalize
            
            result = {
                "base": base_word,
                "transformed": transformed_word,
                "type": pair["type"],
                "rule": rule_type,
                "semantic_impact": semantic_impact,
                "normalized_base": normalized_base,
                "normalized_transformed": normalized_transformed,
                "was_normalized": was_normalized,
                "should_normalize": should_normalize,
                "correct_decision": correct_decision,
                "reasoning": pair.get("reasoning", "")
            }
            
            # Categorize results
            results["results_by_rule"][rule_type].append(result)
            results["results_by_impact"][semantic_impact].append(result)
            
            if correct_decision:
                results["correct_decisions"] += 1
            else:
                results["incorrect_decisions"] += 1
                results["incorrect_examples"].append(result)
        
        # Calculate accuracy by rule type
        results["accuracy_by_rule"] = {}
        for rule_type, rule_results in results["results_by_rule"].items():
            correct = sum(1 for r in rule_results if r["correct_decision"])
            total = len(rule_results)
            accuracy = (correct / total) * 100 if total > 0 else 0
            results["accuracy_by_rule"][rule_type] = {
                "correct": correct,
                "total": total,
                "accuracy": accuracy
            }
        
        # Calculate accuracy by semantic impact
        results["accuracy_by_impact"] = {}
        for impact_level, impact_results in results["results_by_impact"].items():
            correct = sum(1 for r in impact_results if r["correct_decision"])
            total = len(impact_results)
            accuracy = (correct / total) * 100 if total > 0 else 0
            results["accuracy_by_impact"][impact_level] = {
                "correct": correct,
                "total": total,
                "accuracy": accuracy
            }
        
        # Overall accuracy
        results["overall_accuracy"] = (results["correct_decisions"] / results["total_pairs"]) * 100
        
        return results
    
    def test_edge_cases(self) -> Dict:
        """Test specific edge cases for normalization"""
        edge_cases = [
            # Words that might be over-normalized
            {"word": "news", "expected_base": "news", "reason": "Always plural, no singular form"},
            {"word": "scissors", "expected_base": "scissors", "reason": "Always plural tool"},
            {"word": "pants", "expected_base": "pants", "reason": "Always plural clothing"},
            {"word": "glasses", "expected_base": "glasses", "reason": "Ambiguous - eyewear vs drinking vessel"},
            
            # Words that shouldn't be normalized due to meaning change
            {"word": "better", "expected_base": "better", "reason": "Lexicalized comparative"},
            {"word": "best", "expected_base": "best", "reason": "Lexicalized superlative"},
            {"word": "worse", "expected_base": "worse", "reason": "Lexicalized comparative"},
            {"word": "worst", "expected_base": "worst", "reason": "Lexicalized superlative"},
            
            # Technical terms that might be problematic
            {"word": "analysis", "expected_base": "analysis", "reason": "Technical term"},
            {"word": "analyses", "expected_base": "analysis", "reason": "Irregular plural of analysis"},
            {"word": "hypothesis", "expected_base": "hypothesis", "reason": "Technical term"},
            {"word": "hypotheses", "expected_base": "hypothesis", "reason": "Irregular plural"},
            
            # Common irregular verbs
            {"word": "went", "expected_base": "go", "reason": "Irregular past tense"},
            {"word": "came", "expected_base": "come", "reason": "Irregular past tense"},
            {"word": "saw", "expected_base": "see", "reason": "Irregular past tense"},
            {"word": "thought", "expected_base": "think", "reason": "Irregular past tense"},
        ]
        
        results = {
            "total_cases": len(edge_cases),
            "correct_normalizations": 0,
            "incorrect_normalizations": 0,
            "case_results": []
        }
        
        for case in edge_cases:
            word = case["word"]
            expected = case["expected_base"]
            reason = case["reason"]
            
            # Test normalization
            actual = self.normalizer.normalize_word(word)
            correct = actual == expected
            
            case_result = {
                "word": word,
                "expected": expected,
                "actual": actual,
                "correct": correct,
                "reason": reason
            }
            
            results["case_results"].append(case_result)
            
            if correct:
                results["correct_normalizations"] += 1
            else:
                results["incorrect_normalizations"] += 1
        
        results["accuracy"] = (results["correct_normalizations"] / results["total_cases"]) * 100
        
        return results
    
    def test_semantic_preservation_scenarios(self) -> Dict:
        """Test scenarios where semantic meaning should be preserved"""
        scenarios = [
            {
                "scenario": "Professional roles should remain distinct from actions",
                "pairs": [
                    ("teach", "teacher"), ("write", "writer"), ("paint", "painter"),
                    ("manage", "manager"), ("develop", "developer")
                ],
                "expected": "preserve_distinct"
            },
            {
                "scenario": "Negations should remain distinct from base words",
                "pairs": [
                    ("happy", "unhappy"), ("able", "unable"), ("fair", "unfair"),
                    ("kind", "unkind"), ("lock", "unlock")
                ],
                "expected": "preserve_distinct"
            },
            {
                "scenario": "Quality abstractions should remain distinct",
                "pairs": [
                    ("beautiful", "beauty"), ("strong", "strength"), ("wise", "wisdom"),
                    ("true", "truth"), ("deep", "depth")
                ],
                "expected": "preserve_distinct"
            },
            {
                "scenario": "Regular inflections should normalize",
                "pairs": [
                    ("cat", "cats"), ("run", "running"), ("walk", "walked"),
                    ("quick", "quickly"), ("big", "bigger")
                ],
                "expected": "normalize_same"
            }
        ]
        
        results = {
            "total_scenarios": len(scenarios),
            "scenario_results": []
        }
        
        for scenario in scenarios:
            scenario_name = scenario["scenario"]
            pairs = scenario["pairs"]
            expected_behavior = scenario["expected"]
            
            correct_pairs = 0
            total_pairs = len(pairs)
            pair_results = []
            
            for base, transformed in pairs:
                normalized_base = self.normalizer.normalize_word(base)
                normalized_transformed = self.normalizer.normalize_word(transformed)
                
                if expected_behavior == "preserve_distinct":
                    # Words should normalize to different forms
                    correct = normalized_base != normalized_transformed
                elif expected_behavior == "normalize_same":
                    # Words should normalize to the same form
                    correct = normalized_base == normalized_transformed
                else:
                    correct = False
                
                pair_result = {
                    "base": base,
                    "transformed": transformed,
                    "normalized_base": normalized_base,
                    "normalized_transformed": normalized_transformed,
                    "correct": correct
                }
                
                pair_results.append(pair_result)
                if correct:
                    correct_pairs += 1
            
            scenario_result = {
                "scenario": scenario_name,
                "expected_behavior": expected_behavior,
                "accuracy": (correct_pairs / total_pairs) * 100,
                "correct_pairs": correct_pairs,
                "total_pairs": total_pairs,
                "pair_results": pair_results
            }
            
            results["scenario_results"].append(scenario_result)
        
        # Calculate overall scenario accuracy
        total_correct = sum(sr["correct_pairs"] for sr in results["scenario_results"])
        total_pairs = sum(sr["total_pairs"] for sr in results["scenario_results"])
        results["overall_accuracy"] = (total_correct / total_pairs) * 100 if total_pairs > 0 else 0
        
        return results
    
    def generate_semantic_completeness_report(self, rule_results: Dict, edge_results: Dict, scenario_results: Dict) -> str:
        """Generate comprehensive report on semantic completeness"""
        report = []
        report.append("# Word Normalization Semantic Completeness Test Report")
        report.append(f"Generated: {self._get_timestamp()}")
        report.append("")
        
        # Executive Summary
        report.append("## Executive Summary")
        report.append("")
        overall_accuracy = rule_results["overall_accuracy"]
        edge_accuracy = edge_results["accuracy"]
        scenario_accuracy = scenario_results["overall_accuracy"]
        
        report.append(f"- **Rule Compliance Accuracy**: {overall_accuracy:.1f}%")
        report.append(f"- **Edge Case Handling**: {edge_accuracy:.1f}%")
        report.append(f"- **Semantic Scenario Accuracy**: {scenario_accuracy:.1f}%")
        
        # Overall assessment
        avg_accuracy = (overall_accuracy + edge_accuracy + scenario_accuracy) / 3
        if avg_accuracy >= 90:
            assessment = "🌟 **EXCELLENT** - High semantic completeness maintained"
        elif avg_accuracy >= 80:
            assessment = "✅ **GOOD** - Strong semantic preservation with minor issues"
        elif avg_accuracy >= 70:
            assessment = "⚖️ **ACCEPTABLE** - Generally good but needs improvement"
        else:
            assessment = "⚠️ **NEEDS IMPROVEMENT** - Significant semantic completeness issues"
        
        report.append(f"\n**Overall Assessment**: {assessment}")
        report.append("")
        
        # Rule Compliance Analysis
        report.append("## Rule Compliance Analysis")
        report.append("")
        report.append(f"**Overall Accuracy**: {overall_accuracy:.1f}% ({rule_results['correct_decisions']}/{rule_results['total_pairs']})")
        report.append("")
        
        report.append("### Accuracy by Rule Type")
        for rule_type, stats in rule_results["accuracy_by_rule"].items():
            rule_name = rule_type.replace('_', ' ').title()
            report.append(f"- **{rule_name}**: {stats['accuracy']:.1f}% ({stats['correct']}/{stats['total']})")
        
        report.append("")
        report.append("### Accuracy by Semantic Impact Level")
        for impact_level, stats in rule_results["accuracy_by_impact"].items():
            impact_name = impact_level.replace('_', ' ').title()
            report.append(f"- **{impact_name} Impact**: {stats['accuracy']:.1f}% ({stats['correct']}/{stats['total']})")
        
        # Critical Errors (High Impact Incorrect Decisions)
        high_impact_errors = [
            ex for ex in rule_results["incorrect_examples"] 
            if ex["semantic_impact"] == "high"
        ]
        
        if high_impact_errors:
            report.append("")
            report.append("### ⚠️ Critical Semantic Errors (High Impact)")
            for error in high_impact_errors[:10]:  # Show top 10
                decision = "normalized" if error["was_normalized"] else "preserved"
                should = "normalize" if error["should_normalize"] else "preserve"
                report.append(f"- **{error['base']} → {error['transformed']}**: {decision} (should {should})")
                report.append(f"  *{error['reasoning']}*")
        
        # Edge Case Analysis
        report.append("")
        report.append("## Edge Case Analysis")
        report.append("")
        report.append(f"**Accuracy**: {edge_accuracy:.1f}% ({edge_results['correct_normalizations']}/{edge_results['total_cases']})")
        
        # Show problematic edge cases
        problematic_cases = [case for case in edge_results["case_results"] if not case["correct"]]
        if problematic_cases:
            report.append("")
            report.append("### Problematic Edge Cases")
            for case in problematic_cases:
                report.append(f"- **{case['word']}**: expected '{case['expected']}', got '{case['actual']}'")
                report.append(f"  *{case['reason']}*")
        
        # Semantic Preservation Scenarios
        report.append("")
        report.append("## Semantic Preservation Scenarios")
        report.append("")
        report.append(f"**Overall Scenario Accuracy**: {scenario_accuracy:.1f}%")
        report.append("")
        
        for scenario in scenario_results["scenario_results"]:
            report.append(f"### {scenario['scenario']}")
            report.append(f"**Accuracy**: {scenario['accuracy']:.1f}% ({scenario['correct_pairs']}/{scenario['total_pairs']})")
            
            # Show examples of incorrect handling
            incorrect_pairs = [pr for pr in scenario["pair_results"] if not pr["correct"]]
            if incorrect_pairs:
                report.append("**Issues found**:")
                for pair in incorrect_pairs[:3]:  # Show first 3
                    report.append(f"- {pair['base']} → {pair['transformed']}: "
                               f"normalized to ({pair['normalized_base']}, {pair['normalized_transformed']})")
            report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        report.append("")
        
        recommendations = []
        
        # Rule-based recommendations
        if rule_results["accuracy_by_rule"].get("always_preserve", {}).get("accuracy", 100) < 90:
            recommendations.append("🚨 **Critical**: Fix 'always preserve' rule violations - these cause semantic loss")
        
        if rule_results["accuracy_by_rule"].get("case_by_case", {}).get("accuracy", 100) < 80:
            recommendations.append("📝 **Review case-by-case decisions** - refine semantic impact assessment")
        
        # Impact-based recommendations
        high_impact_accuracy = rule_results["accuracy_by_impact"].get("high", {}).get("accuracy", 100)
        if high_impact_accuracy < 85:
            recommendations.append(f"⚠️ **High impact errors**: {100-high_impact_accuracy:.1f}% of high-impact transformations handled incorrectly")
        
        # Edge case recommendations
        if edge_accuracy < 85:
            recommendations.append("🔍 **Address edge cases** - add special handling for problematic word patterns")
        
        # Scenario recommendations
        for scenario in scenario_results["scenario_results"]:
            if scenario["accuracy"] < 80:
                recommendations.append(f"🎯 **Improve {scenario['scenario'].lower()}** handling")
        
        if not recommendations:
            recommendations.append("✅ **System performing well** - semantic completeness is well maintained")
        
        for rec in recommendations:
            report.append(rec)
        
        report.append("")
        report.append("### Priority Actions")
        report.append("1. Fix high semantic impact errors first")
        report.append("2. Review and refine case-by-case evaluation criteria")  
        report.append("3. Add special rules for identified edge cases")
        report.append("4. Validate improvements with expanded test coverage")
        
        return "\n".join(report)
    
    def run_complete_test(self) -> Dict:
        """Run the complete semantic completeness test suite"""
        print("🧪 Word Normalization Semantic Completeness Test")
        print("=" * 60)
        
        # Create test pairs
        test_pairs = self.create_comprehensive_test_pairs()
        print(f"📝 Testing {len(test_pairs)} transformation pairs...")
        
        # Test 1: Rule compliance
        rule_results = self.test_normalization_rules(test_pairs)
        
        # Test 2: Edge cases  
        edge_results = self.test_edge_cases()
        
        # Test 3: Semantic preservation scenarios
        scenario_results = self.test_semantic_preservation_scenarios()
        
        # Generate report
        report = self.generate_semantic_completeness_report(rule_results, edge_results, scenario_results)
        
        # Save results
        output_dir = Path("documents")
        report_path = output_dir / "word_normalization_semantic_report.md"
        results_path = output_dir / "word_normalization_semantic_results.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Combine all results
        all_results = {
            "rule_compliance": rule_results,
            "edge_cases": edge_results, 
            "semantic_scenarios": scenario_results,
            "summary": {
                "rule_accuracy": rule_results["overall_accuracy"],
                "edge_accuracy": edge_results["accuracy"],
                "scenario_accuracy": scenario_results["overall_accuracy"],
                "overall_average": (rule_results["overall_accuracy"] + 
                                  edge_results["accuracy"] + 
                                  scenario_results["overall_accuracy"]) / 3
            }
        }
        
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print(f"\n📊 Test Results:")
        print(f"  Rule Compliance: {rule_results['overall_accuracy']:.1f}%")
        print(f"  Edge Case Handling: {edge_results['accuracy']:.1f}%") 
        print(f"  Semantic Scenarios: {scenario_results['overall_accuracy']:.1f}%")
        print(f"  Average: {all_results['summary']['overall_average']:.1f}%")
        
        print(f"\n📝 Report saved to: {report_path}")
        print(f"📋 Results saved to: {results_path}")
        
        return all_results
    
    def _get_timestamp(self) -> str:
        """Get formatted timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    """Run the word normalization semantic completeness test"""
    tester = WordNormalizationSemanticTest()
    results = tester.run_complete_test()
    
    print("\n✅ Testing complete!")
    
    # Show key findings
    summary = results["summary"]
    if summary["overall_average"] >= 85:
        print("🌟 Semantic completeness is well maintained!")
    elif summary["overall_average"] >= 75:
        print("✅ Good semantic preservation with room for improvement")
    else:
        print("⚠️ Significant semantic completeness issues found")

if __name__ == "__main__":
    main()
