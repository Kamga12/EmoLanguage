#!/usr/bin/env python3
"""
Semantic Completeness Test System for EmoLanguage

This system validates that the simplified emoji language maintains semantic completeness
by testing encoding/decoding accuracy, identifying ambiguities, and comparing 
transformations before and after normalization.

Usage:
    python documents/semantic_completeness_test.py
    python documents/semantic_completeness_test.py --sample-size 100
    python documents/semantic_completeness_test.py --test-type ambiguity
"""

import json
import logging
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict
import re

# Add project root to path to import project modules
sys.path.append(str(Path(__file__).parent.parent))

try:
    from encode import encode
    from decode import decode
    from word_normalizer import WordNormalizer
except ImportError as e:
    print(f"Error importing project modules: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SemanticCompletenessTest:
    def __init__(self):
        """Initialize the semantic completeness test system"""
        self.normalizer = WordNormalizer()
        
        # Load mapping files
        try:
            with open("mappings/word_to_emoji.json", 'r', encoding='utf-8') as f:
                self.word_to_emoji = json.load(f)
            with open("mappings/emoji_to_word.json", 'r', encoding='utf-8') as f:
                self.emoji_to_word = json.load(f)
        except FileNotFoundError as e:
            logger.error(f"Error loading mapping files: {e}")
            raise

        # Test sentence collections
        self.test_sentences = self._create_test_sentences()
        self.transformation_pairs = self._create_transformation_pairs()
        
    def _create_test_sentences(self) -> List[Dict]:
        """Create comprehensive test sentences for validation"""
        return [
            # Basic semantic preservation
            {
                "category": "basic",
                "original": "The cat sits on the mat.",
                "description": "Simple present tense with common nouns"
            },
            {
                "category": "basic", 
                "original": "Dogs bark loudly at strangers.",
                "description": "Plural nouns with adverb"
            },
            {
                "category": "basic",
                "original": "She walks quickly to work.",
                "description": "Third person singular with adverb"
            },
            
            # Temporal variations (should normalize)
            {
                "category": "temporal",
                "original": "The children played in the park yesterday.",
                "description": "Past tense with irregular plural"
            },
            {
                "category": "temporal",
                "original": "He is running faster than before.",
                "description": "Progressive tense with comparative"
            },
            {
                "category": "temporal",
                "original": "They have been working all day.",
                "description": "Perfect progressive tense"
            },
            
            # Inflectional variations (test normalization)
            {
                "category": "inflection",
                "original": "The biggest dog runs fastest.",
                "description": "Superlatives and third person singular"
            },
            {
                "category": "inflection",
                "original": "Books contain interesting stories.",
                "description": "Plural nouns with present tense"
            },
            {
                "category": "inflection",
                "original": "The teacher teaches students daily.",
                "description": "Agent noun with verb form"
            },
            
            # Semantic distinctions (should be preserved)
            {
                "category": "semantic",
                "original": "The happy child smiled joyfully.",
                "description": "Emotion words with manner adverb"
            },
            {
                "category": "semantic",
                "original": "Unhappy people feel sadness deeply.",
                "description": "Negation and emotion states"
            },
            {
                "category": "semantic",
                "original": "Teachers love teaching hopeful students.",
                "description": "Agent nouns vs. action verbs"
            },
            
            # Edge cases for ambiguity detection
            {
                "category": "ambiguity",
                "original": "The better solution works better.",
                "description": "Comparative as noun vs. adverb"
            },
            {
                "category": "ambiguity",
                "original": "Children love playing with children.",
                "description": "Repeated irregular plurals"
            },
            {
                "category": "ambiguity",
                "original": "Running quickly, he runs daily.",
                "description": "Gerund vs. verb forms"
            },
            
            # Complex sentences with multiple transformations
            {
                "category": "complex",
                "original": "The fastest runners were running their best races.",
                "description": "Multiple tenses, superlatives, and progressives"
            },
            {
                "category": "complex",
                "original": "Unhappy teachers rarely teach effectively.",
                "description": "Negation, adverbs, and agent nouns"
            },
            {
                "category": "complex",
                "original": "The children's books were carefully organized.",
                "description": "Possessives, plurals, and adverbs"
            },
            
            # Technical and abstract concepts
            {
                "category": "technical",
                "original": "The algorithm processes data efficiently.",
                "description": "Technical terms with manner adverb"
            },
            {
                "category": "technical",
                "original": "Computers enable faster communication.",
                "description": "Technology and comparative terms"
            }
        ]
    
    def _create_transformation_pairs(self) -> List[Dict]:
        """Create word pairs showing transformations for testing"""
        return [
            # Regular plurals (should be eliminated)
            {"base": "cat", "transformed": "cats", "type": "plural_regular", "should_normalize": True},
            {"base": "dog", "transformed": "dogs", "type": "plural_regular", "should_normalize": True},
            {"base": "book", "transformed": "books", "type": "plural_regular", "should_normalize": True},
            
            # Irregular plurals (case-by-case)
            {"base": "child", "transformed": "children", "type": "plural_irregular", "should_normalize": False},
            {"base": "person", "transformed": "people", "type": "plural_irregular", "should_normalize": False},
            {"base": "foot", "transformed": "feet", "type": "plural_irregular", "should_normalize": True},
            
            # Verb tenses (should be eliminated)
            {"base": "walk", "transformed": "walked", "type": "past_tense", "should_normalize": True},
            {"base": "run", "transformed": "running", "type": "progressive", "should_normalize": True},
            {"base": "play", "transformed": "plays", "type": "third_person", "should_normalize": True},
            
            # Irregular verbs (should be eliminated)
            {"base": "run", "transformed": "ran", "type": "irregular_past", "should_normalize": True},
            {"base": "go", "transformed": "went", "type": "irregular_past", "should_normalize": True},
            {"base": "be", "transformed": "was", "type": "irregular_past", "should_normalize": True},
            
            # Comparatives (case-by-case)
            {"base": "big", "transformed": "bigger", "type": "comparative", "should_normalize": True},
            {"base": "good", "transformed": "better", "type": "irregular_comparative", "should_normalize": False},
            {"base": "fast", "transformed": "fastest", "type": "superlative", "should_normalize": True},
            
            # Agent/role transformations (should be preserved)
            {"base": "teach", "transformed": "teacher", "type": "agent_noun", "should_normalize": False},
            {"base": "write", "transformed": "writer", "type": "agent_noun", "should_normalize": False},
            {"base": "piano", "transformed": "pianist", "type": "agent_noun", "should_normalize": False},
            
            # Negation (should be preserved)
            {"base": "happy", "transformed": "unhappy", "type": "negation", "should_normalize": False},
            {"base": "possible", "transformed": "impossible", "type": "negation", "should_normalize": False},
            {"base": "legal", "transformed": "illegal", "type": "negation", "should_normalize": False},
            
            # State/quality transformations (should be preserved)  
            {"base": "happy", "transformed": "happiness", "type": "quality_noun", "should_normalize": False},
            {"base": "complex", "transformed": "complexity", "type": "quality_noun", "should_normalize": False},
            {"base": "move", "transformed": "movement", "type": "action_noun", "should_normalize": False},
            
            # Adverbs (case-by-case)
            {"base": "quick", "transformed": "quickly", "type": "manner_adverb", "should_normalize": True},
            {"base": "hard", "transformed": "hardly", "type": "semantic_shift_adverb", "should_normalize": False},
            {"base": "late", "transformed": "lately", "type": "semantic_shift_adverb", "should_normalize": False},
        ]
    
    def test_encoding_decoding_accuracy(self, test_sample: List[Dict] = None) -> Dict:
        """Test round-trip accuracy of encoding and decoding"""
        logger.info("Testing encoding/decoding accuracy...")
        
        if test_sample is None:
            test_sample = self.test_sentences
        
        results = {
            "total_tests": len(test_sample),
            "perfect_matches": 0,
            "semantic_matches": 0,
            "failures": 0,
            "detailed_results": [],
            "failure_examples": []
        }
        
        for test in test_sample:
            original = test["original"]
            category = test["category"]
            
            # Encode then decode
            encoded = encode(original)
            decoded = decode(encoded)
            
            # Analyze accuracy
            perfect_match = original.lower().strip() == decoded.lower().strip()
            semantic_match = self._assess_semantic_equivalence(original, decoded)
            
            result = {
                "original": original,
                "encoded": encoded,
                "decoded": decoded,
                "category": category,
                "perfect_match": perfect_match,
                "semantic_match": semantic_match,
                "description": test["description"]
            }
            
            results["detailed_results"].append(result)
            
            if perfect_match:
                results["perfect_matches"] += 1
            elif semantic_match:
                results["semantic_matches"] += 1
            else:
                results["failures"] += 1
                results["failure_examples"].append(result)
        
        # Calculate accuracy percentages
        total = results["total_tests"]
        results["perfect_accuracy"] = (results["perfect_matches"] / total) * 100
        results["semantic_accuracy"] = ((results["perfect_matches"] + results["semantic_matches"]) / total) * 100
        results["failure_rate"] = (results["failures"] / total) * 100
        
        return results
    
    def test_transformation_preservation(self) -> Dict:
        """Test that semantic transformations are properly handled"""
        logger.info("Testing transformation preservation...")
        
        results = {
            "total_pairs": len(self.transformation_pairs),
            "correct_decisions": 0,
            "incorrect_decisions": 0,
            "ambiguous_cases": 0,
            "results_by_type": defaultdict(list),
            "incorrect_examples": []
        }
        
        for pair in self.transformation_pairs:
            base_word = pair["base"]
            transformed_word = pair["transformed"]
            transform_type = pair["type"]
            should_normalize = pair["should_normalize"]
            
            # Test if normalization behaves as expected
            normalized_base = self.normalizer.normalize_word(base_word)
            normalized_transformed = self.normalizer.normalize_word(transformed_word)
            
            # Check if transformation was normalized (reduced to base form)
            was_normalized = normalized_base == normalized_transformed
            
            # Compare with expected behavior
            correct_decision = was_normalized == should_normalize
            
            result = {
                "base": base_word,
                "transformed": transformed_word,
                "type": transform_type,
                "normalized_base": normalized_base,
                "normalized_transformed": normalized_transformed,
                "was_normalized": was_normalized,
                "should_normalize": should_normalize,
                "correct_decision": correct_decision
            }
            
            results["results_by_type"][transform_type].append(result)
            
            if correct_decision:
                results["correct_decisions"] += 1
            else:
                results["incorrect_decisions"] += 1
                results["incorrect_examples"].append(result)
        
        # Calculate accuracy by transformation type
        results["accuracy_by_type"] = {}
        for transform_type, type_results in results["results_by_type"].items():
            correct = sum(1 for r in type_results if r["correct_decision"])
            total = len(type_results)
            accuracy = (correct / total) * 100 if total > 0 else 0
            results["accuracy_by_type"][transform_type] = {
                "correct": correct,
                "total": total,
                "accuracy": accuracy
            }
        
        # Overall accuracy
        total = results["total_pairs"]
        results["overall_accuracy"] = (results["correct_decisions"] / total) * 100
        
        return results
    
    def test_ambiguity_detection(self) -> Dict:
        """Identify cases where elimination causes ambiguity"""
        logger.info("Testing for ambiguity cases...")
        
        # Find words that normalize to the same base form but have different meanings
        base_to_words = defaultdict(list)
        for word in self.word_to_emoji.keys():
            base = self.normalizer.normalize_word(word)
            base_to_words[base].append(word)
        
        ambiguous_groups = {}
        semantic_conflicts = []
        
        for base, words in base_to_words.items():
            if len(words) > 1:
                # Check if these words have different emojis (potential semantic difference)
                emojis = set()
                word_mappings = {}
                
                for word in words:
                    if word in self.word_to_emoji:
                        emoji = self.word_to_emoji[word]
                        emojis.add(emoji)
                        word_mappings[word] = emoji
                
                if len(emojis) > 1:
                    # Potential ambiguity - different words with different emojis normalize to same base
                    ambiguous_groups[base] = {
                        "words": words,
                        "emojis": list(emojis),
                        "mappings": word_mappings,
                        "conflict_level": self._assess_ambiguity_level(words, word_mappings)
                    }
                    
                    # Assess if this creates semantic conflicts
                    conflict_severity = self._assess_semantic_conflict(words)
                    if conflict_severity > 0.5:  # Threshold for significant conflict
                        semantic_conflicts.append({
                            "base": base,
                            "words": words,
                            "mappings": word_mappings,
                            "severity": conflict_severity
                        })
        
        return {
            "total_ambiguous_groups": len(ambiguous_groups),
            "high_conflict_groups": len([g for g in ambiguous_groups.values() if g["conflict_level"] > 0.7]),
            "semantic_conflicts": semantic_conflicts,
            "ambiguous_groups": ambiguous_groups,
            "conflict_statistics": self._calculate_conflict_statistics(ambiguous_groups)
        }
    
    def test_emoji_sequence_comparison(self, sample_size: int = 100) -> Dict:
        """Compare emoji sequences before and after simplification"""
        logger.info(f"Comparing emoji sequences (sample size: {sample_size})...")
        
        # Get a sample of sentences for testing
        test_sentences = self.test_sentences[:sample_size] if len(self.test_sentences) >= sample_size else self.test_sentences
        
        results = {
            "total_comparisons": len(test_sentences),
            "sequence_changes": 0,
            "length_changes": [],
            "complexity_changes": [],
            "detailed_comparisons": []
        }
        
        for test in test_sentences:
            original_text = test["original"]
            
            # Create a "full form" version (attempt to expand contractions, etc.)
            full_form = self._create_full_form(original_text)
            
            # Encode both versions
            original_encoded = encode(original_text)
            full_encoded = encode(full_form)
            
            # Calculate metrics
            original_length = len(original_encoded)
            full_length = len(full_encoded)
            
            original_complexity = self._calculate_sequence_complexity(original_encoded)
            full_complexity = self._calculate_sequence_complexity(full_encoded)
            
            comparison = {
                "original_text": original_text,
                "full_form": full_form,
                "original_encoded": original_encoded,
                "full_encoded": full_encoded,
                "length_change": original_length - full_length,
                "complexity_change": original_complexity - full_complexity,
                "sequences_differ": original_encoded != full_encoded
            }
            
            results["detailed_comparisons"].append(comparison)
            
            if original_encoded != full_encoded:
                results["sequence_changes"] += 1
            
            results["length_changes"].append(comparison["length_change"])
            results["complexity_changes"].append(comparison["complexity_change"])
        
        # Calculate statistics
        results["avg_length_reduction"] = sum(results["length_changes"]) / len(results["length_changes"])
        results["avg_complexity_reduction"] = sum(results["complexity_changes"]) / len(results["complexity_changes"])
        results["sequence_change_rate"] = (results["sequence_changes"] / results["total_comparisons"]) * 100
        
        return results
    
    def test_edge_cases(self) -> Dict:
        """Test specific edge cases that might cause issues"""
        logger.info("Testing edge cases...")
        
        edge_cases = [
            # Homonyms that might get confused
            {"text": "The bat flew while I held a bat.", "description": "Homonym: bat (animal) vs bat (sports equipment)"},
            {"text": "The bank by the river bank was closed.", "description": "Homonym: bank (financial) vs bank (river)"},
            
            # Words that sound the same but have different meanings
            {"text": "I read the red book yesterday.", "description": "Homophone: read (past) vs red (color)"},
            {"text": "The wind will wind the clock.", "description": "Homophone: wind (air) vs wind (twist)"},
            
            # Contractions and informal speech
            {"text": "I can't won't shouldn't do it.", "description": "Multiple contractions"},
            {"text": "They're their friends over there.", "description": "They're/their/there confusion"},
            
            # Numbers and special characters
            {"text": "I have 5 cats and 10 dogs in 2024.", "description": "Mixed text and numbers"},
            {"text": "The cost is $50.99 (fifty dollars).", "description": "Currency and parentheses"},
            
            # Technical terms and abbreviations
            {"text": "The CPU processes data via RAM.", "description": "Technical abbreviations"},
            {"text": "Dr. Smith works at NASA's HQ.", "description": "Titles and organizational abbreviations"},
        ]
        
        results = {
            "total_edge_cases": len(edge_cases),
            "successful_cases": 0,
            "problematic_cases": 0,
            "case_results": []
        }
        
        for case in edge_cases:
            original = case["text"]
            description = case["description"]
            
            try:
                encoded = encode(original)
                decoded = decode(encoded)
                
                # Check for issues
                has_issues = self._detect_edge_case_issues(original, encoded, decoded)
                
                case_result = {
                    "original": original,
                    "encoded": encoded,
                    "decoded": decoded,
                    "description": description,
                    "has_issues": has_issues,
                    "issues_found": self._identify_specific_issues(original, encoded, decoded)
                }
                
                results["case_results"].append(case_result)
                
                if has_issues:
                    results["problematic_cases"] += 1
                else:
                    results["successful_cases"] += 1
                    
            except Exception as e:
                results["problematic_cases"] += 1
                results["case_results"].append({
                    "original": original,
                    "description": description,
                    "error": str(e),
                    "has_issues": True
                })
        
        results["success_rate"] = (results["successful_cases"] / results["total_edge_cases"]) * 100
        
        return results
    
    def generate_comprehensive_report(self, test_results: Dict) -> str:
        """Generate a comprehensive markdown report of all test results"""
        report = []
        report.append("# Semantic Completeness Test Report")
        report.append(f"Generated: {self._get_timestamp()}")
        report.append("")
        
        # Executive Summary
        report.append("## Executive Summary")
        report.append("")
        
        encoding_results = test_results.get("encoding_accuracy", {})
        transformation_results = test_results.get("transformation_preservation", {})
        ambiguity_results = test_results.get("ambiguity_detection", {})
        
        perfect_accuracy = encoding_results.get("perfect_accuracy", 0)
        semantic_accuracy = encoding_results.get("semantic_accuracy", 0)
        transform_accuracy = transformation_results.get("overall_accuracy", 0)
        ambiguous_groups = ambiguity_results.get("total_ambiguous_groups", 0)
        
        report.append(f"- **Perfect Encoding Accuracy**: {perfect_accuracy:.1f}%")
        report.append(f"- **Semantic Accuracy**: {semantic_accuracy:.1f}%") 
        report.append(f"- **Transformation Handling**: {transform_accuracy:.1f}%")
        report.append(f"- **Ambiguous Groups Found**: {ambiguous_groups}")
        
        # Overall assessment
        if perfect_accuracy >= 90 and transform_accuracy >= 85:
            assessment = "🌟 **EXCELLENT** - System maintains high semantic completeness"
        elif perfect_accuracy >= 75 and transform_accuracy >= 70:
            assessment = "✅ **GOOD** - System shows strong semantic preservation with minor issues"
        elif perfect_accuracy >= 60 and transform_accuracy >= 60:
            assessment = "⚖️ **ACCEPTABLE** - System works but needs improvement in key areas"
        else:
            assessment = "⚠️ **NEEDS IMPROVEMENT** - Significant issues found that affect semantic completeness"
        
        report.append(f"\n**Overall Assessment**: {assessment}")
        report.append("")
        
        # Detailed Results Sections
        if "encoding_accuracy" in test_results:
            report.extend(self._format_encoding_results(test_results["encoding_accuracy"]))
        
        if "transformation_preservation" in test_results:
            report.extend(self._format_transformation_results(test_results["transformation_preservation"]))
        
        if "ambiguity_detection" in test_results:
            report.extend(self._format_ambiguity_results(test_results["ambiguity_detection"]))
        
        if "emoji_sequence_comparison" in test_results:
            report.extend(self._format_sequence_results(test_results["emoji_sequence_comparison"]))
        
        if "edge_cases" in test_results:
            report.extend(self._format_edge_case_results(test_results["edge_cases"]))
        
        # Recommendations
        report.append("\n## Recommendations")
        report.extend(self._generate_recommendations(test_results))
        
        return "\n".join(report)
    
    def run_full_test_suite(self, sample_size: int = None) -> Dict:
        """Run all semantic completeness tests"""
        logger.info("Starting full semantic completeness test suite...")
        
        results = {}
        
        # Test 1: Encoding/Decoding Accuracy
        test_sample = self.test_sentences[:sample_size] if sample_size else self.test_sentences
        results["encoding_accuracy"] = self.test_encoding_decoding_accuracy(test_sample)
        
        # Test 2: Transformation Preservation
        results["transformation_preservation"] = self.test_transformation_preservation()
        
        # Test 3: Ambiguity Detection
        results["ambiguity_detection"] = self.test_ambiguity_detection()
        
        # Test 4: Emoji Sequence Comparison
        sequence_sample_size = min(sample_size or 50, 50)
        results["emoji_sequence_comparison"] = self.test_emoji_sequence_comparison(sequence_sample_size)
        
        # Test 5: Edge Cases
        results["edge_cases"] = self.test_edge_cases()
        
        logger.info("Full test suite completed")
        return results
    
    # Helper methods
    def _assess_semantic_equivalence(self, text1: str, text2: str) -> bool:
        """Assess if two texts are semantically equivalent"""
        # Simple heuristic - normalize whitespace and basic transformations
        def normalize_for_comparison(text):
            # Convert to lowercase, normalize whitespace
            text = re.sub(r'\s+', ' ', text.lower().strip())
            # Handle common variations
            text = re.sub(r'\bwere\b', 'be', text)
            text = re.sub(r'\bwas\b', 'be', text)
            text = re.sub(r'\bis\b', 'be', text)
            text = re.sub(r'\bare\b', 'be', text)
            return text
        
        norm1 = normalize_for_comparison(text1)
        norm2 = normalize_for_comparison(text2)
        
        # Check if they're similar enough (allowing for minor differences)
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        # Calculate Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        similarity = intersection / union if union > 0 else 0
        return similarity >= 0.8  # 80% word overlap threshold
    
    def _assess_ambiguity_level(self, words: List[str], mappings: Dict[str, str]) -> float:
        """Assess the level of ambiguity in a word group"""
        # Simple heuristic based on semantic distance between words
        if len(words) <= 1:
            return 0.0
        
        # Check if words are semantically related
        semantic_distance = 0.0
        for i, word1 in enumerate(words):
            for word2 in words[i+1:]:
                # Simple semantic distance based on word characteristics
                if self._are_semantically_related(word1, word2):
                    semantic_distance += 0.2
                else:
                    semantic_distance += 0.8
        
        # Normalize by number of pairs
        num_pairs = len(words) * (len(words) - 1) / 2
        return semantic_distance / num_pairs if num_pairs > 0 else 0.0
    
    def _assess_semantic_conflict(self, words: List[str]) -> float:
        """Assess if words have conflicting semantic meanings"""
        if len(words) <= 1:
            return 0.0
        
        # Check for known semantic conflicts
        conflict_patterns = [
            (r'.*ing$', r'^(?!.*ing$).*'),  # -ing forms vs non-ing forms
            (r'.*ed$', r'^(?!.*ed$).*'),    # -ed forms vs non-ed forms
            (r'.*er$', r'^(?!.*er$).*'),    # agent nouns vs base forms
            (r'^un.*', r'^(?!un).*'),       # negated vs non-negated
        ]
        
        conflict_score = 0.0
        for word1 in words:
            for word2 in words:
                if word1 != word2:
                    for pattern1, pattern2 in conflict_patterns:
                        if re.match(pattern1, word1) and re.match(pattern2, word2):
                            conflict_score += 0.3
        
        # Normalize by word pairs
        max_conflicts = len(words) * (len(words) - 1)
        return min(conflict_score / max_conflicts, 1.0) if max_conflicts > 0 else 0.0
    
    def _are_semantically_related(self, word1: str, word2: str) -> bool:
        """Simple check if two words are semantically related"""
        # Basic patterns for related words
        if word1 in word2 or word2 in word1:
            return True
        
        # Common suffixes that indicate relationships
        related_suffixes = [('', 'ing'), ('', 'ed'), ('', 's'), ('', 'er'), ('', 'est')]
        for suf1, suf2 in related_suffixes:
            if word1 + suf2 == word2 or word2 + suf1 == word1:
                return True
        
        return False
    
    def _calculate_conflict_statistics(self, ambiguous_groups: Dict) -> Dict:
        """Calculate statistics about conflicts"""
        stats = {
            "high_conflict": 0,
            "medium_conflict": 0,
            "low_conflict": 0,
            "total_affected_words": 0
        }
        
        for group in ambiguous_groups.values():
            conflict_level = group["conflict_level"]
            stats["total_affected_words"] += len(group["words"])
            
            if conflict_level >= 0.7:
                stats["high_conflict"] += 1
            elif conflict_level >= 0.4:
                stats["medium_conflict"] += 1
            else:
                stats["low_conflict"] += 1
        
        return stats
    
    def _create_full_form(self, text: str) -> str:
        """Create a 'full form' version of text by expanding contractions"""
        # Simple expansion of common contractions
        expansions = {
            "can't": "cannot",
            "won't": "will not",
            "don't": "do not",
            "doesn't": "does not",
            "isn't": "is not",
            "aren't": "are not",
            "wasn't": "was not",
            "weren't": "were not",
            "haven't": "have not",
            "hasn't": "has not",
            "hadn't": "had not",
            "shouldn't": "should not",
            "wouldn't": "would not",
            "couldn't": "could not",
            "I'm": "I am",
            "you're": "you are",
            "we're": "we are",
            "they're": "they are",
            "I've": "I have",
            "you've": "you have",
            "we've": "we have",
            "they've": "they have",
            "I'll": "I will",
            "you'll": "you will",
            "we'll": "we will",
            "they'll": "they will"
        }
        
        result = text
        for contraction, expansion in expansions.items():
            result = re.sub(r'\b' + re.escape(contraction) + r'\b', expansion, result, flags=re.IGNORECASE)
        
        return result
    
    def _calculate_sequence_complexity(self, sequence: str) -> float:
        """Calculate the complexity of an emoji sequence"""
        if not sequence:
            return 0.0
        
        # Simple complexity measure based on:
        # - Length of sequence
        # - Number of unique emojis
        # - Variation in emoji types
        
        length = len(sequence)
        unique_chars = len(set(sequence))
        
        # Estimate emoji count (rough approximation)
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF]')
        emoji_matches = emoji_pattern.findall(sequence)
        emoji_count = len(emoji_matches)
        
        # Complexity score
        complexity = (length * 0.3 + unique_chars * 0.4 + emoji_count * 0.3) / 10
        return complexity
    
    def _detect_edge_case_issues(self, original: str, encoded: str, decoded: str) -> bool:
        """Detect if an edge case has issues"""
        # Basic checks for problems
        if not encoded or not decoded:
            return True
        
        # Check for obvious encoding failures (too many unchanged words)
        original_words = re.findall(r'\b\w+\b', original.lower())
        decoded_words = re.findall(r'\b\w+\b', decoded.lower())
        
        # If most words are unchanged, encoding may have failed
        if len(original_words) > 0:
            unchanged_ratio = len([w for w in original_words if w in decoded_words]) / len(original_words)
            if unchanged_ratio > 0.8:  # More than 80% unchanged might indicate issues
                return True
        
        return False
    
    def _identify_specific_issues(self, original: str, encoded: str, decoded: str) -> List[str]:
        """Identify specific issues in edge cases"""
        issues = []
        
        if not encoded:
            issues.append("Encoding failed - empty result")
        
        if not decoded:
            issues.append("Decoding failed - empty result")
        
        if encoded == original:
            issues.append("No encoding occurred - text unchanged")
        
        if len(encoded) > len(original) * 3:
            issues.append("Encoded sequence unusually long")
        
        return issues
    
    def _format_encoding_results(self, results: Dict) -> List[str]:
        """Format encoding accuracy results for report"""
        lines = []
        lines.append("## Encoding/Decoding Accuracy")
        lines.append("")
        lines.append(f"**Total Tests**: {results['total_tests']}")
        lines.append(f"**Perfect Matches**: {results['perfect_matches']} ({results['perfect_accuracy']:.1f}%)")
        lines.append(f"**Semantic Matches**: {results['semantic_matches']} ({results['semantic_accuracy']:.1f}% total)")
        lines.append(f"**Failures**: {results['failures']} ({results['failure_rate']:.1f}%)")
        lines.append("")
        
        # Show accuracy by category
        if "detailed_results" in results:
            category_stats = defaultdict(lambda: {"total": 0, "perfect": 0, "semantic": 0})
            for result in results["detailed_results"]:
                cat = result["category"]
                category_stats[cat]["total"] += 1
                if result["perfect_match"]:
                    category_stats[cat]["perfect"] += 1
                elif result["semantic_match"]:
                    category_stats[cat]["semantic"] += 1
            
            lines.append("### Accuracy by Category")
            for category, stats in category_stats.items():
                perfect_pct = (stats["perfect"] / stats["total"]) * 100
                semantic_pct = ((stats["perfect"] + stats["semantic"]) / stats["total"]) * 100
                lines.append(f"- **{category.title()}**: {perfect_pct:.1f}% perfect, {semantic_pct:.1f}% semantic")
        
        # Show worst failures
        if results["failure_examples"]:
            lines.append("")
            lines.append("### Notable Failures")
            for failure in results["failure_examples"][:5]:  # Show top 5 failures
                lines.append(f"- **Original**: {failure['original']}")
                lines.append(f"  **Decoded**: {failure['decoded']}")
                lines.append(f"  **Category**: {failure['category']}")
                lines.append("")
        
        return lines
    
    def _format_transformation_results(self, results: Dict) -> List[str]:
        """Format transformation preservation results"""
        lines = []
        lines.append("## Transformation Preservation")
        lines.append("")
        lines.append(f"**Overall Accuracy**: {results['overall_accuracy']:.1f}%")
        lines.append(f"**Correct Decisions**: {results['correct_decisions']}/{results['total_pairs']}")
        lines.append("")
        
        # Show accuracy by transformation type
        lines.append("### Accuracy by Transformation Type")
        for trans_type, stats in results["accuracy_by_type"].items():
            lines.append(f"- **{trans_type.replace('_', ' ').title()}**: {stats['accuracy']:.1f}% ({stats['correct']}/{stats['total']})")
        
        # Show incorrect examples
        if results["incorrect_examples"]:
            lines.append("")
            lines.append("### Incorrect Transformation Handling")
            for example in results["incorrect_examples"][:10]:
                decision = "normalized" if example["was_normalized"] else "preserved"
                should = "normalize" if example["should_normalize"] else "preserve"
                lines.append(f"- **{example['base']} → {example['transformed']}**: {decision} (should {should})")
        
        return lines
    
    def _format_ambiguity_results(self, results: Dict) -> List[str]:
        """Format ambiguity detection results"""
        lines = []
        lines.append("## Ambiguity Detection")
        lines.append("")
        lines.append(f"**Ambiguous Groups Found**: {results['total_ambiguous_groups']}")
        lines.append(f"**High Conflict Groups**: {results['high_conflict_groups']}")
        lines.append(f"**Semantic Conflicts**: {len(results['semantic_conflicts'])}")
        lines.append("")
        
        # Show conflict statistics
        if "conflict_statistics" in results:
            stats = results["conflict_statistics"]
            lines.append("### Conflict Severity Distribution")
            lines.append(f"- **High Conflict**: {stats['high_conflict']} groups")
            lines.append(f"- **Medium Conflict**: {stats['medium_conflict']} groups")
            lines.append(f"- **Low Conflict**: {stats['low_conflict']} groups")
            lines.append(f"- **Total Affected Words**: {stats['total_affected_words']}")
            lines.append("")
        
        # Show worst ambiguous groups
        if results["ambiguous_groups"]:
            lines.append("### High-Risk Ambiguous Groups")
            high_risk = [(base, info) for base, info in results["ambiguous_groups"].items() 
                        if info["conflict_level"] > 0.6]
            
            for base, info in sorted(high_risk, key=lambda x: x[1]["conflict_level"], reverse=True)[:10]:
                lines.append(f"- **{base}**: {', '.join(info['words'])}")
                lines.append(f"  Emojis: {', '.join(info['emojis'])}")
                lines.append(f"  Conflict Level: {info['conflict_level']:.2f}")
                lines.append("")
        
        return lines
    
    def _format_sequence_results(self, results: Dict) -> List[str]:
        """Format emoji sequence comparison results"""
        lines = []
        lines.append("## Emoji Sequence Comparison")
        lines.append("")
        lines.append(f"**Sequences Changed**: {results['sequence_changes']}/{results['total_comparisons']} ({results['sequence_change_rate']:.1f}%)")
        lines.append(f"**Average Length Reduction**: {results['avg_length_reduction']:.1f} characters")
        lines.append(f"**Average Complexity Reduction**: {results['avg_complexity_reduction']:.2f}")
        lines.append("")
        
        return lines
    
    def _format_edge_case_results(self, results: Dict) -> List[str]:
        """Format edge case test results"""
        lines = []
        lines.append("## Edge Case Testing")
        lines.append("")
        lines.append(f"**Success Rate**: {results['success_rate']:.1f}%")
        lines.append(f"**Successful Cases**: {results['successful_cases']}/{results['total_edge_cases']}")
        lines.append(f"**Problematic Cases**: {results['problematic_cases']}")
        lines.append("")
        
        # Show problematic cases
        problematic = [case for case in results["case_results"] if case.get("has_issues", False)]
        if problematic:
            lines.append("### Problematic Edge Cases")
            for case in problematic[:5]:
                lines.append(f"- **{case.get('description', 'Unknown')}**")
                lines.append(f"  Original: {case.get('original', 'N/A')}")
                if 'error' in case:
                    lines.append(f"  Error: {case['error']}")
                elif 'issues_found' in case:
                    lines.append(f"  Issues: {', '.join(case['issues_found'])}")
                lines.append("")
        
        return lines
    
    def _generate_recommendations(self, test_results: Dict) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        encoding_results = test_results.get("encoding_accuracy", {})
        transformation_results = test_results.get("transformation_preservation", {})
        ambiguity_results = test_results.get("ambiguity_detection", {})
        
        # Encoding accuracy recommendations
        if encoding_results.get("perfect_accuracy", 0) < 80:
            recommendations.append("🔧 **Improve encoding accuracy** by reviewing failed test cases and updating mappings")
        
        if encoding_results.get("failure_rate", 0) > 20:
            recommendations.append("⚠️ **Address high failure rate** by analyzing common failure patterns")
        
        # Transformation recommendations
        if transformation_results.get("overall_accuracy", 0) < 85:
            recommendations.append("📝 **Review transformation rules** - some decisions may need refinement")
        
        incorrect_examples = transformation_results.get("incorrect_examples", [])
        if incorrect_examples:
            problematic_types = set(ex["type"] for ex in incorrect_examples)
            for prob_type in problematic_types:
                recommendations.append(f"🔍 **Review {prob_type.replace('_', ' ')} handling** in normalization rules")
        
        # Ambiguity recommendations
        high_conflict_groups = ambiguity_results.get("high_conflict_groups", 0)
        if high_conflict_groups > 5:
            recommendations.append(f"⚖️ **Address {high_conflict_groups} high-conflict ambiguous groups** to prevent meaning loss")
        
        semantic_conflicts = len(ambiguity_results.get("semantic_conflicts", []))
        if semantic_conflicts > 10:
            recommendations.append("🚨 **Critical: Resolve semantic conflicts** that could cause misunderstanding")
        
        # General recommendations
        if not recommendations:
            recommendations.append("✅ **System performing well** - consider expanding test coverage")
        
        recommendations.append("")
        recommendations.append("### Next Steps")
        recommendations.append("1. Review detailed test results for specific issues")
        recommendations.append("2. Update normalization rules based on findings")
        recommendations.append("3. Add exception handling for identified edge cases")
        recommendations.append("4. Re-run tests after improvements")
        recommendations.append("5. Consider expanding test coverage to more domains")
        
        return recommendations
    
    def _get_timestamp(self) -> str:
        """Get formatted timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    parser = argparse.ArgumentParser(description="Test semantic completeness of EmoLanguage system")
    parser.add_argument("--sample-size", type=int, help="Limit test sample size")
    parser.add_argument("--test-type", choices=["all", "encoding", "transformation", "ambiguity", "sequences", "edge"], 
                       default="all", help="Type of test to run")
    parser.add_argument("--output-dir", default="documents", help="Output directory for results")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress detailed output")
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("🧪 EmoLanguage Semantic Completeness Test System")
        print("=" * 60)
    
    try:
        tester = SemanticCompletenessTest()
        
        if args.test_type == "all":
            results = tester.run_full_test_suite(args.sample_size)
        elif args.test_type == "encoding":
            test_sample = tester.test_sentences[:args.sample_size] if args.sample_size else tester.test_sentences
            results = {"encoding_accuracy": tester.test_encoding_decoding_accuracy(test_sample)}
        elif args.test_type == "transformation":
            results = {"transformation_preservation": tester.test_transformation_preservation()}
        elif args.test_type == "ambiguity":
            results = {"ambiguity_detection": tester.test_ambiguity_detection()}
        elif args.test_type == "sequences":
            sample_size = args.sample_size or 50
            results = {"emoji_sequence_comparison": tester.test_emoji_sequence_comparison(sample_size)}
        elif args.test_type == "edge":
            results = {"edge_cases": tester.test_edge_cases()}
        
        # Generate and save report
        report = tester.generate_comprehensive_report(results)
        
        output_path = Path(args.output_dir) / "semantic_completeness_test_report.md"
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Save raw results
        results_path = Path(args.output_dir) / "semantic_completeness_test_results.json"
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        if not args.quiet:
            print(f"\n📊 Test Results Summary:")
            if "encoding_accuracy" in results:
                acc = results["encoding_accuracy"]["semantic_accuracy"]
                print(f"  Semantic Accuracy: {acc:.1f}%")
            
            if "transformation_preservation" in results:
                trans_acc = results["transformation_preservation"]["overall_accuracy"]
                print(f"  Transformation Accuracy: {trans_acc:.1f}%")
            
            if "ambiguity_detection" in results:
                ambiguous = results["ambiguity_detection"]["total_ambiguous_groups"]
                print(f"  Ambiguous Groups: {ambiguous}")
            
            print(f"\n📝 Report saved to: {output_path}")
            print(f"📋 Raw results saved to: {results_path}")
            print("\n✅ Testing complete!")
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        if not args.quiet:
            print(f"\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
