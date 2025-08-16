# Semantic Validation Layer for Word-Emoji Mappings
# ✅ Uses LLM to verify each mapping makes intuitive sense
# ✅ Flags confusing or arbitrary mappings
# ✅ Suggests improvements for weak mappings
# ✅ Ensures consistency across similar words

import os
import json
import time
import logging
from typing import Dict, List, Optional, Set, Tuple, NamedTuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationStatus(Enum):
    """Validation status for emoji mappings"""
    EXCELLENT = "excellent"      # Score 4.5-5.0
    GOOD = "good"               # Score 3.5-4.4
    ACCEPTABLE = "acceptable"   # Score 2.5-3.4
    WEAK = "weak"               # Score 1.5-2.4
    REJECTED = "rejected"       # Score 0-1.4

class ValidationCriterion(Enum):
    """Different validation criteria"""
    SEMANTIC_ACCURACY = "semantic_accuracy"
    VISUAL_CLARITY = "visual_clarity"
    CULTURAL_UNIVERSALITY = "cultural_universality"
    DISAMBIGUATION = "disambiguation"
    COGNITIVE_LOAD = "cognitive_load"
    CONSISTENCY = "consistency"

@dataclass
class ValidationScore:
    """Individual validation score for a criterion"""
    criterion: ValidationCriterion
    score: float  # 1-5 scale
    explanation: str
    suggestions: List[str]

@dataclass
class MappingValidation:
    """Complete validation result for a word-emoji mapping"""
    word: str
    emoji: str
    overall_score: float
    status: ValidationStatus
    scores: List[ValidationScore]
    issues: List[str]
    improvements: List[str]
    alternative_suggestions: List[str]
    consistency_notes: List[str]
    validation_reasoning: str

@dataclass
class ConsistencyGroup:
    """Group of related words for consistency checking"""
    semantic_field: str
    words: List[str]
    patterns: List[str]
    expected_consistency: str

class SemanticValidator:
    """
    Comprehensive semantic validation system for word-emoji mappings.
    Evaluates mappings for intuitive sense, flags confusing assignments,
    and ensures consistency across similar words.
    """
    
    def __init__(self, llm_base_url: str = "http://127.0.0.1:1234"):
        self.llm_base_url = llm_base_url.rstrip('/')
        self.session = self._create_http_session()
        self.model_name = self._get_model_name()
        
        # Validation thresholds
        self.thresholds = {
            ValidationStatus.EXCELLENT: 4.5,
            ValidationStatus.GOOD: 3.5,
            ValidationStatus.ACCEPTABLE: 2.5,
            ValidationStatus.WEAK: 1.5
        }
        
        # Consistency groups for semantic fields
        self.consistency_groups = self._initialize_consistency_groups()
        
        # Cache for validation results
        self.validation_cache = {}
        self.consistency_cache = {}
        
    def _create_http_session(self) -> requests.Session:
        """Create HTTP session with retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
        
    def _get_model_name(self) -> str:
        """Auto-detect available model"""
        try:
            response = self.session.get(
                f"{self.llm_base_url}/v1/models",
                timeout=10
            )
            response.raise_for_status()
            models = response.json().get('data', [])
            if models:
                model_name = models[0].get('id', 'local-model')
                logger.info(f"Detected model: {model_name}")
                return model_name
            return 'local-model'
        except Exception as e:
            logger.warning(f"Could not detect model, using default: {e}")
            return 'local-model'
            
    def _initialize_consistency_groups(self) -> Dict[str, ConsistencyGroup]:
        """Initialize semantic field groups for consistency checking"""
        return {
            "animals": ConsistencyGroup(
                semantic_field="animals",
                words=["cat", "dog", "bird", "fish", "horse", "cow", "sheep", "pig"],
                patterns=["Use specific animal emoji when available", "Consider domesticated vs wild animals"],
                expected_consistency="Animal emoji should directly represent the species"
            ),
            "emotions": ConsistencyGroup(
                semantic_field="emotions", 
                words=["happy", "sad", "angry", "excited", "calm", "anxious", "joyful"],
                patterns=["Use facial expressions", "Consider intensity of emotion"],
                expected_consistency="Emotional states should use expressive face emoji"
            ),
            "colors": ConsistencyGroup(
                semantic_field="colors",
                words=["red", "blue", "green", "yellow", "purple", "orange", "black", "white"],
                patterns=["Use objects strongly associated with colors", "Consider color psychology"],
                expected_consistency="Colors should use representative objects or hearts in that color"
            ),
            "actions": ConsistencyGroup(
                semantic_field="actions",
                words=["run", "walk", "jump", "swim", "fly", "dance", "sing"],
                patterns=["Show action being performed", "Use person + action combinations"],
                expected_consistency="Action verbs should show clear motion or activity"
            ),
            "technology": ConsistencyGroup(
                semantic_field="technology",
                words=["computer", "phone", "internet", "software", "algorithm", "database"],
                patterns=["Use tech-related emoji", "Combine for complex concepts"],
                expected_consistency="Tech terms should use digital/electronic symbols"
            )
        }
        
    def validate_single_mapping(self, word: str, emoji: str, reasoning: str = "") -> MappingValidation:
        """
        Validate a single word-emoji mapping against all criteria
        """
        # Check cache first
        cache_key = f"{word}:{emoji}"
        if cache_key in self.validation_cache:
            return self.validation_cache[cache_key]
            
        logger.info(f"Validating mapping: '{word}' → {emoji}")
        
        # Generate validation prompt
        validation_prompt = self._create_validation_prompt(word, emoji, reasoning)
        
        # Get LLM evaluation
        llm_response = self._call_llm(validation_prompt)
        if not llm_response:
            return self._create_error_validation(word, emoji, "LLM call failed")
            
        # Parse LLM response into structured validation
        validation = self._parse_validation_response(word, emoji, llm_response)
        
        # Cache result
        self.validation_cache[cache_key] = validation
        
        return validation
        
    def validate_mapping_batch(self, mappings: Dict[str, str]) -> Dict[str, MappingValidation]:
        """
        Validate multiple mappings and check for consistency issues
        """
        logger.info(f"Validating batch of {len(mappings)} mappings")
        
        # Individual validations
        validations = {}
        for word, emoji in mappings.items():
            validations[word] = self.validate_single_mapping(word, emoji)
            time.sleep(0.1)  # Rate limiting
            
        # Consistency analysis
        consistency_issues = self._analyze_consistency(validations)
        
        # Update validations with consistency findings
        for word, issues in consistency_issues.items():
            if word in validations:
                validations[word].consistency_notes.extend(issues)
                
        return validations
        
    def _create_validation_prompt(self, word: str, emoji: str, reasoning: str) -> str:
        """Create comprehensive validation prompt"""
        
        base_prompt = f"""
You are an expert semantic linguist evaluating word-emoji mappings for an emoji language system.

MAPPING TO EVALUATE:
Word: "{word}"
Emoji: {emoji}
Original Reasoning: {reasoning if reasoning else "No reasoning provided"}

EVALUATION CRITERIA (Rate each 1-5 scale, 5 = excellent):

1. SEMANTIC ACCURACY: Does the emoji truly represent the word's core meaning?
   - Consider denotative (literal) and connotative (associated) meanings
   - Evaluate how well the emoji captures the essence of the word
   
2. VISUAL CLARITY: Is the connection immediately apparent to users?
   - How obvious is the visual relationship?
   - Would users intuitively understand this mapping?
   
3. CULTURAL UNIVERSALITY: Will this work across different cultural contexts?
   - Are there cultural biases or specific regional interpretations?
   - Is the emoji meaning consistent globally?
   
4. DISAMBIGUATION: Can this be confused with other possible word mappings?
   - Is the emoji specific enough for this word?
   - Could it reasonably represent other words?
   
5. COGNITIVE LOAD: How much mental effort to understand the connection?
   - Is it immediate recognition or requires thinking?
   - How memorable is this association?

REQUIRED RESPONSE FORMAT:

SCORES:
- Semantic Accuracy: [1-5] | [detailed explanation]
- Visual Clarity: [1-5] | [detailed explanation]  
- Cultural Universality: [1-5] | [detailed explanation]
- Disambiguation: [1-5] | [detailed explanation]
- Cognitive Load: [1-5] | [detailed explanation]

OVERALL ASSESSMENT:
- Average Score: [calculated average]
- Status: [Excellent/Good/Acceptable/Weak/Rejected]

ISSUES IDENTIFIED:
- [List specific problems, or "None identified" if clean]

IMPROVEMENT SUGGESTIONS:
- [Specific actionable recommendations, or "None needed" if satisfactory]

ALTERNATIVE MAPPINGS:
- Alternative 1: [emoji] - [reasoning]
- Alternative 2: [emoji] - [reasoning]
- Alternative 3: [emoji] - [reasoning]

FINAL RECOMMENDATION:
[Approve/Revise/Reject] - [Summary reasoning in 1-2 sentences]
"""
        return base_prompt.strip()
        
    def _call_llm(self, prompt: str) -> Optional[str]:
        """Call LLM API with validation prompt"""
        try:
            response = self.session.post(
                f"{self.llm_base_url}/v1/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.1,  # Low temperature for consistent validation
                    "top_p": 0.8,
                },
                timeout=45
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'choices' not in result or not result['choices']:
                logger.error(f"Invalid API response: {result}")
                return None
                
            return result['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return None
            
    def _parse_validation_response(self, word: str, emoji: str, response: str) -> MappingValidation:
        """Parse LLM validation response into structured format"""
        
        scores = []
        issues = []
        improvements = []
        alternatives = []
        overall_score = 0.0
        status = ValidationStatus.WEAK
        
        lines = response.split('\n')
        current_section = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Section headers
            if "SCORES:" in line:
                current_section = "scores"
            elif "ISSUES IDENTIFIED:" in line:
                current_section = "issues"
            elif "IMPROVEMENT SUGGESTIONS:" in line:
                current_section = "improvements"
            elif "ALTERNATIVE MAPPINGS:" in line:
                current_section = "alternatives"
            elif "FINAL RECOMMENDATION:" in line:
                current_section = "recommendation"
            elif line.startswith("-") and current_section:
                # Process content based on current section
                content = line[1:].strip()
                
                if current_section == "scores":
                    score_info = self._parse_score_line(content)
                    if score_info:
                        scores.append(score_info)
                        
                elif current_section == "issues":
                    if content and content.lower() != "none identified":
                        issues.append(content)
                        
                elif current_section == "improvements":
                    if content and content.lower() != "none needed":
                        improvements.append(content)
                        
                elif current_section == "alternatives":
                    if ":" in content:
                        alternatives.append(content.split(":", 1)[1].strip())
        
        # Calculate overall score
        if scores:
            overall_score = sum(s.score for s in scores) / len(scores)
            status = self._determine_status(overall_score)
        
        return MappingValidation(
            word=word,
            emoji=emoji,
            overall_score=overall_score,
            status=status,
            scores=scores,
            issues=issues,
            improvements=improvements,
            alternative_suggestions=alternatives,
            consistency_notes=[],
            validation_reasoning=response
        )
        
    def _parse_score_line(self, content: str) -> Optional[ValidationScore]:
        """Parse individual score line"""
        try:
            if "|" in content:
                parts = content.split("|", 1)
                criterion_part = parts[0].strip()
                explanation = parts[1].strip()
                
                # Extract score (look for pattern like "Score: 4" or just "4")
                import re
                score_match = re.search(r'(\d\.?\d?)', criterion_part)
                if score_match:
                    score = float(score_match.group(1))
                    
                    # Determine criterion type
                    criterion_text = criterion_part.lower()
                    if "semantic" in criterion_text:
                        criterion = ValidationCriterion.SEMANTIC_ACCURACY
                    elif "visual" in criterion_text:
                        criterion = ValidationCriterion.VISUAL_CLARITY
                    elif "cultural" in criterion_text:
                        criterion = ValidationCriterion.CULTURAL_UNIVERSALITY
                    elif "disambiguation" in criterion_text:
                        criterion = ValidationCriterion.DISAMBIGUATION
                    elif "cognitive" in criterion_text:
                        criterion = ValidationCriterion.COGNITIVE_LOAD
                    else:
                        return None
                        
                    return ValidationScore(
                        criterion=criterion,
                        score=score,
                        explanation=explanation,
                        suggestions=[]
                    )
        except Exception as e:
            logger.warning(f"Failed to parse score line '{content}': {e}")
            
        return None
        
    def _determine_status(self, score: float) -> ValidationStatus:
        """Determine validation status from overall score"""
        if score >= self.thresholds[ValidationStatus.EXCELLENT]:
            return ValidationStatus.EXCELLENT
        elif score >= self.thresholds[ValidationStatus.GOOD]:
            return ValidationStatus.GOOD
        elif score >= self.thresholds[ValidationStatus.ACCEPTABLE]:
            return ValidationStatus.ACCEPTABLE
        elif score >= self.thresholds[ValidationStatus.WEAK]:
            return ValidationStatus.WEAK
        else:
            return ValidationStatus.REJECTED
            
    def _create_error_validation(self, word: str, emoji: str, error_msg: str) -> MappingValidation:
        """Create error validation result"""
        return MappingValidation(
            word=word,
            emoji=emoji,
            overall_score=0.0,
            status=ValidationStatus.REJECTED,
            scores=[],
            issues=[f"Validation error: {error_msg}"],
            improvements=["Re-run validation when LLM is available"],
            alternative_suggestions=[],
            consistency_notes=[],
            validation_reasoning=f"Error occurred during validation: {error_msg}"
        )
        
    def _analyze_consistency(self, validations: Dict[str, MappingValidation]) -> Dict[str, List[str]]:
        """Analyze consistency across related words"""
        consistency_issues = defaultdict(list)
        
        # Group words by semantic field
        word_groups = defaultdict(list)
        for word in validations.keys():
            for field, group in self.consistency_groups.items():
                if word in group.words:
                    word_groups[field].append(word)
                    
        # Check each semantic field for consistency
        for field, words in word_groups.items():
            if len(words) < 2:
                continue
                
            group = self.consistency_groups[field]
            field_validations = {w: validations[w] for w in words}
            
            # Check for consistent patterns
            issues = self._check_field_consistency(field, field_validations, group)
            for word, word_issues in issues.items():
                consistency_issues[word].extend(word_issues)
                
        return consistency_issues
        
    def _check_field_consistency(self, field: str, validations: Dict[str, MappingValidation], 
                                group: ConsistencyGroup) -> Dict[str, List[str]]:
        """Check consistency within a semantic field"""
        issues = defaultdict(list)
        
        # Get emoji patterns used
        emoji_patterns = defaultdict(list)
        for word, validation in validations.items():
            emoji = validation.emoji
            if len(emoji) == 1:
                emoji_patterns["single"].append((word, emoji))
            else:
                emoji_patterns["combination"].append((word, emoji))
                
        # Check if similar words are using consistent approaches
        if len(emoji_patterns["single"]) > 0 and len(emoji_patterns["combination"]) > 0:
            # Mixed approaches - may indicate inconsistency
            single_words = [w for w, _ in emoji_patterns["single"]]
            combo_words = [w for w, _ in emoji_patterns["combination"]]
            
            for word in single_words:
                issues[word].append(
                    f"Inconsistent approach in {field}: uses single emoji while {combo_words} use combinations"
                )
                
        # Check for quality consistency
        scores = [(word, val.overall_score) for word, val in validations.items()]
        avg_score = sum(score for _, score in scores) / len(scores)
        
        for word, score in scores:
            if abs(score - avg_score) > 1.0:  # Significant deviation
                issues[word].append(
                    f"Quality inconsistency in {field}: score {score:.1f} vs field average {avg_score:.1f}"
                )
                
        return issues
        
    def analyze_mapping_quality(self, mappings: Dict[str, str]) -> Dict:
        """
        Comprehensive quality analysis of all mappings
        """
        logger.info("Performing comprehensive quality analysis...")
        
        validations = self.validate_mapping_batch(mappings)
        
        # Aggregate statistics
        stats = {
            "total_mappings": len(validations),
            "status_distribution": defaultdict(int),
            "avg_scores_by_criterion": defaultdict(list),
            "common_issues": defaultdict(int),
            "quality_summary": {},
            "recommendations": []
        }
        
        # Process each validation
        for validation in validations.values():
            stats["status_distribution"][validation.status.value] += 1
            
            # Aggregate scores by criterion
            for score in validation.scores:
                stats["avg_scores_by_criterion"][score.criterion.value].append(score.score)
                
            # Track common issues
            for issue in validation.issues:
                stats["common_issues"][issue] += 1
                
        # Calculate averages
        for criterion, scores in stats["avg_scores_by_criterion"].items():
            if scores:
                stats["avg_scores_by_criterion"][criterion] = sum(scores) / len(scores)
                
        # Generate quality summary
        total = stats["total_mappings"]
        excellent = stats["status_distribution"]["excellent"]
        good = stats["status_distribution"]["good"]
        acceptable = stats["status_distribution"]["acceptable"] 
        weak = stats["status_distribution"]["weak"]
        rejected = stats["status_distribution"]["rejected"]
        
        stats["quality_summary"] = {
            "high_quality_rate": (excellent + good) / total * 100,
            "acceptable_rate": acceptable / total * 100,
            "needs_improvement_rate": (weak + rejected) / total * 100,
            "overall_avg_score": sum(v.overall_score for v in validations.values()) / total
        }
        
        # Generate recommendations
        if weak + rejected > total * 0.2:  # More than 20% poor quality
            stats["recommendations"].append("High number of weak mappings - consider revising mapping strategy")
            
        if stats["avg_scores_by_criterion"].get("disambiguation", 5) < 3.0:
            stats["recommendations"].append("Low disambiguation scores - focus on more specific emoji choices")
            
        if stats["avg_scores_by_criterion"].get("cultural_universality", 5) < 3.0:
            stats["recommendations"].append("Cultural universality concerns - review emoji with regional meanings")
            
        return stats
        
    def generate_improvement_report(self, validations: Dict[str, MappingValidation], 
                                  output_file: str = None) -> str:
        """
        Generate comprehensive improvement report
        """
        report_lines = [
            "# Semantic Validation Report",
            "=" * 50,
            "",
            f"**Total Mappings Validated:** {len(validations)}",
            ""
        ]
        
        # Status distribution
        status_counts = defaultdict(int)
        for validation in validations.values():
            status_counts[validation.status.value] += 1
            
        report_lines.extend([
            "## Status Distribution",
            "",
            f"- Excellent: {status_counts['excellent']} ({status_counts['excellent']/len(validations)*100:.1f}%)",
            f"- Good: {status_counts['good']} ({status_counts['good']/len(validations)*100:.1f}%)",
            f"- Acceptable: {status_counts['acceptable']} ({status_counts['acceptable']/len(validations)*100:.1f}%)",
            f"- Weak: {status_counts['weak']} ({status_counts['weak']/len(validations)*100:.1f}%)",
            f"- Rejected: {status_counts['rejected']} ({status_counts['rejected']/len(validations)*100:.1f}%)",
            ""
        ])
        
        # Problem mappings that need attention
        problem_mappings = [
            (word, val) for word, val in validations.items() 
            if val.status in [ValidationStatus.WEAK, ValidationStatus.REJECTED]
        ]
        
        if problem_mappings:
            report_lines.extend([
                "## Mappings Requiring Attention",
                ""
            ])
            
            for word, validation in sorted(problem_mappings, key=lambda x: x[1].overall_score):
                report_lines.extend([
                    f"### {word} → {validation.emoji}",
                    f"**Score:** {validation.overall_score:.2f} ({validation.status.value})",
                    "**Issues:**"
                ])
                for issue in validation.issues:
                    report_lines.append(f"- {issue}")
                    
                report_lines.extend(["**Suggested Improvements:**"])
                for improvement in validation.improvements:
                    report_lines.append(f"- {improvement}")
                    
                if validation.alternative_suggestions:
                    report_lines.extend(["**Alternative Mappings:**"])
                    for alt in validation.alternative_suggestions:
                        report_lines.append(f"- {alt}")
                        
                report_lines.append("")
                
        # Consistency issues
        consistency_mappings = [
            (word, val) for word, val in validations.items() 
            if val.consistency_notes
        ]
        
        if consistency_mappings:
            report_lines.extend([
                "## Consistency Issues",
                ""
            ])
            
            for word, validation in consistency_mappings:
                report_lines.extend([
                    f"### {word} → {validation.emoji}",
                    "**Consistency Notes:**"
                ])
                for note in validation.consistency_notes:
                    report_lines.append(f"- {note}")
                report_lines.append("")
                
        report = "\n".join(report_lines)
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Improvement report saved to {output_file}")
            
        return report
        
    def save_validation_results(self, validations: Dict[str, MappingValidation], 
                               output_dir: str = "validation_results"):
        """Save validation results in multiple formats"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save as JSON for programmatic access
        json_data = {
            word: asdict(validation) for word, validation in validations.items()
        }
        
        with open(os.path.join(output_dir, "validation_results.json"), 'w') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
            
        # Generate and save improvement report
        report = self.generate_improvement_report(
            validations, 
            os.path.join(output_dir, "improvement_report.md")
        )
        
        # Save summary statistics
        stats = self.analyze_mapping_quality({word: val.emoji for word, val in validations.items()})
        with open(os.path.join(output_dir, "quality_statistics.json"), 'w') as f:
            json.dump(stats, f, indent=2)
            
        logger.info(f"Validation results saved to {output_dir}/")

# Example usage and testing
if __name__ == "__main__":
    # Initialize validator
    validator = SemanticValidator()
    
    # Example mappings for testing
    test_mappings = {
        "happy": "😊",
        "computer": "💻", 
        "cat": "🐱",
        "run": "🏃",
        "love": "❤️",
        "algorithm": "🔄⚙️",
        "red": "❤️",  # Potential conflict with love
        "dog": "🐶"
    }
    
    print("Testing semantic validation system...")
    
    # Validate single mapping
    print("\n=== Single Mapping Validation ===")
    validation = validator.validate_single_mapping("happy", "😊", "Direct facial expression of happiness")
    print(f"Word: {validation.word}")
    print(f"Emoji: {validation.emoji}")
    print(f"Score: {validation.overall_score:.2f}")
    print(f"Status: {validation.status.value}")
    print(f"Issues: {len(validation.issues)}")
    
    # Validate batch
    print("\n=== Batch Validation ===")
    validations = validator.validate_mapping_batch(test_mappings)
    print(f"Validated {len(validations)} mappings")
    
    # Quality analysis  
    print("\n=== Quality Analysis ===")
    quality_stats = validator.analyze_mapping_quality(test_mappings)
    print(f"High quality rate: {quality_stats['quality_summary']['high_quality_rate']:.1f}%")
    print(f"Overall average score: {quality_stats['quality_summary']['overall_avg_score']:.2f}")
    
    # Save results
    print("\n=== Saving Results ===")
    validator.save_validation_results(validations)
    print("Results saved to validation_results/")
