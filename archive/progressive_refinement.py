# Progressive Refinement Process for Emoji Mappings
# ✅ Uses LLM to review and improve existing mappings
# ✅ Generates example sentences to test readability
# ✅ Collects problematic mappings for manual review
# ✅ Iteratively improves the mapping quality

import os
import json
import time
import logging
import random
from typing import Dict, List, Optional, Set, Tuple, NamedTuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, Counter
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import spacy
from tqdm import tqdm
import datetime
import statistics

# Import existing validation system
from semantic_validator import SemanticValidator, ValidationStatus, MappingValidation

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RefinementStage(Enum):
    """Different stages of refinement process"""
    INITIAL_REVIEW = "initial_review"
    READABILITY_TEST = "readability_test"
    PROBLEM_COLLECTION = "problem_collection"
    IMPROVEMENT_GENERATION = "improvement_generation"
    VALIDATION_CHECK = "validation_check"
    MANUAL_REVIEW_PREP = "manual_review_prep"
    ITERATION_COMPLETE = "iteration_complete"

class ReadabilityScore(Enum):
    """Readability assessment scores"""
    EXCELLENT = "excellent"      # 4.5-5.0 - Immediately clear and intuitive
    GOOD = "good"               # 3.5-4.4 - Clear with minimal thinking
    ACCEPTABLE = "acceptable"   # 2.5-3.4 - Understandable but requires thought
    POOR = "poor"               # 1.5-2.4 - Confusing or unclear
    UNREADABLE = "unreadable"   # 0-1.4 - Cannot understand the connection

@dataclass
class ReadabilityTest:
    """Test case for readability assessment"""
    sentence_english: str
    sentence_emoji: str
    context: str
    difficulty_level: str
    target_words: List[str]
    
@dataclass
class ReadabilityResult:
    """Result of readability testing"""
    test: ReadabilityTest
    score: float
    readability: ReadabilityScore
    issues_identified: List[str]
    suggested_improvements: List[str]
    time_to_understand: Optional[float]
    clarity_rating: float
    context_dependency: float

@dataclass
class MappingImprovement:
    """Suggested improvement for a mapping"""
    word: str
    current_emoji: str
    suggested_emoji: str
    reasoning: str
    expected_improvement: float
    confidence: float
    validation_needed: bool

@dataclass
class RefinementIteration:
    """Complete refinement iteration result"""
    iteration_number: int
    stage: RefinementStage
    timestamp: datetime.datetime
    mappings_reviewed: int
    improvements_suggested: int
    readability_tests: int
    avg_readability_score: float
    problems_identified: int
    manual_review_items: int
    next_actions: List[str]

class ProgressiveRefinementSystem:
    """
    Progressive refinement system that iteratively improves emoji mappings
    through LLM review, readability testing, and quality enhancement.
    """
    
    def __init__(self, llm_base_url: str = "http://127.0.0.1:1234"):
        self.llm_base_url = llm_base_url.rstrip('/')
        self.session = self._create_http_session()
        self.model_name = self._get_model_name()
        self.nlp = spacy.load("en_core_web_sm")
        
        # Initialize validator
        self.validator = SemanticValidator(llm_base_url)
        
        # Refinement configuration
        self.config = {
            "max_iterations": 5,
            "readability_threshold": 3.0,
            "improvement_threshold": 0.5,
            "batch_size": 10,
            "test_sentences_per_word": 3,
            "manual_review_threshold": 2.0,
            "validation_confidence_threshold": 0.7
        }
        
        # State tracking
        self.current_iteration = 0
        self.iteration_history: List[RefinementIteration] = []
        self.problematic_mappings: Dict[str, List[str]] = defaultdict(list)
        self.improvement_suggestions: Dict[str, List[MappingImprovement]] = defaultdict(list)
        self.readability_cache: Dict[str, ReadabilityResult] = {}
        self.manual_review_queue: List[Tuple[str, str, str]] = []
        
        # Example sentence templates for testing
        self.sentence_templates = [
            "The {word} was very important in this context.",
            "I really enjoy {word} when I have free time.",
            "Can you help me understand {word} better?",
            "The concept of {word} is fascinating to explore.",
            "{word} makes a significant difference in our daily lives.",
            "Learning about {word} opened my mind to new possibilities.",
            "The {word} in the story was beautifully described.",
            "Modern {word} has changed how we think about things."
        ]
    
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
    
    def load_current_mappings(self, mapping_file: str = "mappings/word_to_emoji.json") -> Dict[str, str]:
        """Load current emoji mappings"""
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
            logger.info(f"Loaded {len(mappings)} mappings from {mapping_file}")
            return mappings
        except FileNotFoundError:
            logger.error(f"Mapping file {mapping_file} not found")
            return {}
        except Exception as e:
            logger.error(f"Error loading mappings: {e}")
            return {}
    
    def generate_readability_tests(self, word: str, emoji: str, num_tests: int = 3) -> List[ReadabilityTest]:
        """Generate readability test sentences for a word-emoji mapping"""
        tests = []
        
        # Select random sentence templates
        selected_templates = random.sample(
            self.sentence_templates, 
            min(num_tests, len(self.sentence_templates))
        )
        
        for template in selected_templates:
            # Create English sentence
            english_sentence = template.format(word=word)
            
            # Create emoji version (simplified for now - would use full encoder)
            emoji_sentence = template.format(word=emoji)
            
            # Determine context and difficulty
            context = self._determine_sentence_context(english_sentence)
            difficulty = self._estimate_sentence_difficulty(english_sentence, word)
            
            test = ReadabilityTest(
                sentence_english=english_sentence,
                sentence_emoji=emoji_sentence,
                context=context,
                difficulty_level=difficulty,
                target_words=[word]
            )
            tests.append(test)
        
        return tests
    
    def _determine_sentence_context(self, sentence: str) -> str:
        """Determine the context category of a sentence"""
        contexts = {
            "academic": ["concept", "understand", "explore", "learning", "study"],
            "casual": ["enjoy", "fun", "like", "daily", "life"],
            "descriptive": ["beautiful", "important", "significant", "fascinating"],
            "instructional": ["help", "can you", "how to", "explain"],
            "narrative": ["story", "character", "plot", "described"]
        }
        
        sentence_lower = sentence.lower()
        for context, keywords in contexts.items():
            if any(keyword in sentence_lower for keyword in keywords):
                return context
        return "general"
    
    def _estimate_sentence_difficulty(self, sentence: str, target_word: str) -> str:
        """Estimate readability difficulty of sentence"""
        doc = self.nlp(sentence)
        
        # Count complex features
        long_words = sum(1 for token in doc if len(token.text) > 7)
        complex_pos = sum(1 for token in doc if token.pos_ in ["NOUN", "VERB", "ADJ"])
        sentence_length = len(doc)
        
        # Simple heuristic
        complexity_score = (long_words * 2 + complex_pos + sentence_length * 0.1)
        
        if complexity_score < 5:
            return "easy"
        elif complexity_score < 10:
            return "medium"
        else:
            return "hard"
    
    def test_readability(self, test: ReadabilityTest) -> ReadabilityResult:
        """Test readability of an emoji sentence using LLM"""
        
        # Check cache first
        cache_key = f"{test.sentence_emoji}:{test.context}"
        if cache_key in self.readability_cache:
            return self.readability_cache[cache_key]
        
        prompt = self._create_readability_prompt(test)
        
        try:
            response = self._call_llm(prompt, max_tokens=600, temperature=0.1)
            if not response:
                return self._create_error_readability_result(test, "LLM call failed")
            
            result = self._parse_readability_response(test, response)
            self.readability_cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"Readability test failed: {e}")
            return self._create_error_readability_result(test, str(e))
    
    def _create_readability_prompt(self, test: ReadabilityTest) -> str:
        """Create prompt for readability testing"""
        return f"""
You are evaluating the readability of emoji-encoded text for a language system.

ORIGINAL ENGLISH: {test.sentence_english}
EMOJI VERSION: {test.sentence_emoji}
CONTEXT: {test.context}
DIFFICULTY LEVEL: {test.difficulty_level}
TARGET WORDS: {', '.join(test.target_words)}

Please evaluate how well a human reader could understand the emoji version:

EVALUATION CRITERIA (Rate 1-5 scale):

1. IMMEDIATE CLARITY: Can you instantly understand what the emoji represents?
2. CONTEXTUAL UNDERSTANDING: Does the emoji make sense in this sentence context?
3. COGNITIVE LOAD: How much mental effort is needed to decode the meaning?
4. AMBIGUITY LEVEL: Could the emoji be confused for other meanings?
5. FLUENCY: Does the emoji version read smoothly?

RESPONSE FORMAT:

SCORES:
- Immediate Clarity: [1-5] | [explanation]
- Contextual Understanding: [1-5] | [explanation]
- Cognitive Load: [1-5] | [explanation] (5 = very easy, 1 = very hard)
- Ambiguity Level: [1-5] | [explanation] (5 = no ambiguity, 1 = very ambiguous)
- Fluency: [1-5] | [explanation]

OVERALL ASSESSMENT:
- Average Score: [calculated average]
- Readability: [Excellent/Good/Acceptable/Poor/Unreadable]
- Time to Understand: [Immediate/Quick/Moderate/Slow/Very Slow]

ISSUES IDENTIFIED:
- [List specific readability problems, or "None identified"]

IMPROVEMENT SUGGESTIONS:
- [Specific suggestions for better emoji choices, or "None needed"]

SUMMARY:
[2-3 sentence summary of readability assessment]
        """.strip()
    
    def _parse_readability_response(self, test: ReadabilityTest, response: str) -> ReadabilityResult:
        """Parse LLM readability response"""
        
        scores = []
        issues = []
        improvements = []
        overall_score = 0.0
        readability = ReadabilityScore.POOR
        time_rating = "moderate"
        
        lines = response.split('\n')
        current_section = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if "SCORES:" in line:
                current_section = "scores"
            elif "ISSUES IDENTIFIED:" in line:
                current_section = "issues"
            elif "IMPROVEMENT SUGGESTIONS:" in line:
                current_section = "improvements"
            elif "Time to Understand:" in line:
                time_rating = self._extract_time_rating(line)
            elif line.startswith("-") and current_section:
                content = line[1:].strip()
                
                if current_section == "scores":
                    score = self._extract_score_from_line(content)
                    if score is not None:
                        scores.append(score)
                elif current_section == "issues":
                    if content.lower() != "none identified":
                        issues.append(content)
                elif current_section == "improvements":
                    if content.lower() != "none needed":
                        improvements.append(content)
        
        # Calculate overall metrics
        if scores:
            overall_score = sum(scores) / len(scores)
            readability = self._determine_readability_level(overall_score)
        
        # Map time rating to numeric
        time_to_understand = self._time_rating_to_numeric(time_rating)
        
        return ReadabilityResult(
            test=test,
            score=overall_score,
            readability=readability,
            issues_identified=issues,
            suggested_improvements=improvements,
            time_to_understand=time_to_understand,
            clarity_rating=overall_score,
            context_dependency=self._assess_context_dependency(issues)
        )
    
    def _extract_score_from_line(self, line: str) -> Optional[float]:
        """Extract numeric score from response line"""
        import re
        score_match = re.search(r'(\d\.?\d?)', line)
        if score_match:
            try:
                return float(score_match.group(1))
            except ValueError:
                pass
        return None
    
    def _extract_time_rating(self, line: str) -> str:
        """Extract time rating from line"""
        line_lower = line.lower()
        if "immediate" in line_lower:
            return "immediate"
        elif "quick" in line_lower:
            return "quick"
        elif "slow" in line_lower or "very slow" in line_lower:
            return "slow"
        else:
            return "moderate"
    
    def _time_rating_to_numeric(self, rating: str) -> float:
        """Convert time rating to numeric value"""
        ratings = {
            "immediate": 0.5,
            "quick": 1.0,
            "moderate": 2.0,
            "slow": 4.0
        }
        return ratings.get(rating, 2.0)
    
    def _determine_readability_level(self, score: float) -> ReadabilityScore:
        """Determine readability level from score"""
        if score >= 4.5:
            return ReadabilityScore.EXCELLENT
        elif score >= 3.5:
            return ReadabilityScore.GOOD
        elif score >= 2.5:
            return ReadabilityScore.ACCEPTABLE
        elif score >= 1.5:
            return ReadabilityScore.POOR
        else:
            return ReadabilityScore.UNREADABLE
    
    def _assess_context_dependency(self, issues: List[str]) -> float:
        """Assess how context-dependent the understanding is"""
        context_keywords = ["context", "ambiguous", "unclear", "confusing"]
        context_issues = sum(1 for issue in issues if any(kw in issue.lower() for kw in context_keywords))
        return min(context_issues / max(len(issues), 1), 1.0)
    
    def _create_error_readability_result(self, test: ReadabilityTest, error_msg: str) -> ReadabilityResult:
        """Create error readability result"""
        return ReadabilityResult(
            test=test,
            score=0.0,
            readability=ReadabilityScore.UNREADABLE,
            issues_identified=[f"Error: {error_msg}"],
            suggested_improvements=["Retry when LLM is available"],
            time_to_understand=None,
            clarity_rating=0.0,
            context_dependency=1.0
        )
    
    def generate_mapping_improvements(self, word: str, emoji: str, 
                                   validation: MappingValidation, 
                                   readability_results: List[ReadabilityResult]) -> List[MappingImprovement]:
        """Generate improvement suggestions for a mapping"""
        
        prompt = self._create_improvement_prompt(word, emoji, validation, readability_results)
        
        try:
            response = self._call_llm(prompt, max_tokens=800, temperature=0.2)
            if not response:
                return []
            
            improvements = self._parse_improvement_response(word, emoji, response)
            return improvements
            
        except Exception as e:
            logger.error(f"Improvement generation failed for {word}: {e}")
            return []
    
    def _create_improvement_prompt(self, word: str, emoji: str, 
                                 validation: MappingValidation,
                                 readability_results: List[ReadabilityResult]) -> str:
        """Create prompt for improvement generation"""
        
        # Summarize readability issues
        common_issues = []
        avg_readability = 0.0
        if readability_results:
            all_issues = []
            scores = []
            for result in readability_results:
                all_issues.extend(result.issues_identified)
                scores.append(result.score)
            
            if scores:
                avg_readability = sum(scores) / len(scores)
            
            # Count common issues
            issue_counts = Counter(all_issues)
            common_issues = [issue for issue, count in issue_counts.most_common(3)]
        
        validation_issues = validation.issues if validation else []
        validation_score = validation.overall_score if validation else 0.0
        
        return f"""
You are an expert in emoji language design, tasked with improving word-emoji mappings.

CURRENT MAPPING:
Word: "{word}"
Current Emoji: {emoji}

VALIDATION RESULTS:
- Validation Score: {validation_score:.2f}/5.0
- Status: {validation.status.value if validation else 'unknown'}
- Issues: {'; '.join(validation_issues) if validation_issues else 'None'}

READABILITY RESULTS:
- Average Readability Score: {avg_readability:.2f}/5.0
- Common Issues: {'; '.join(common_issues) if common_issues else 'None'}

TASK: Suggest improved emoji mappings that address the identified issues.

REQUIREMENTS:
- Maintain semantic accuracy to the word
- Improve readability and clarity
- Reduce ambiguity and cognitive load
- Consider cultural universality
- Limit to 1-2 emojis maximum

RESPONSE FORMAT:

IMPROVEMENT SUGGESTIONS:

1. SUGGESTED EMOJI: [emoji]
   - Reasoning: [why this is better]
   - Expected Improvement: [estimated score improvement 0.0-2.0]
   - Confidence: [confidence level 0.0-1.0]
   - Addresses Issues: [specific issues this fixes]

2. SUGGESTED EMOJI: [emoji]
   - Reasoning: [why this is better]
   - Expected Improvement: [estimated score improvement 0.0-2.0]
   - Confidence: [confidence level 0.0-1.0]
   - Addresses Issues: [specific issues this fixes]

3. SUGGESTED EMOJI: [emoji]
   - Reasoning: [why this is better]
   - Expected Improvement: [estimated score improvement 0.0-2.0]
   - Confidence: [confidence level 0.0-1.0]
   - Addresses Issues: [specific issues this fixes]

ANALYSIS:
- Root Cause: [main reason current mapping has issues]
- Key Improvement Focus: [what needs to be improved most]

RECOMMENDATION:
[Which suggestion is best and why]
        """.strip()
    
    def _parse_improvement_response(self, word: str, current_emoji: str, response: str) -> List[MappingImprovement]:
        """Parse improvement suggestions from LLM response"""
        
        improvements = []
        lines = response.split('\n')
        
        current_suggestion = None
        for line in lines:
            line = line.strip()
            
            if line.startswith(("1.", "2.", "3.")) and "SUGGESTED EMOJI:" in line:
                # New suggestion
                if current_suggestion:
                    improvements.append(current_suggestion)
                
                # Extract emoji from line
                import re
                emoji_match = re.search(r'SUGGESTED EMOJI:\s*([^\s]+)', line)
                if emoji_match:
                    suggested_emoji = emoji_match.group(1)
                    current_suggestion = MappingImprovement(
                        word=word,
                        current_emoji=current_emoji,
                        suggested_emoji=suggested_emoji,
                        reasoning="",
                        expected_improvement=0.0,
                        confidence=0.0,
                        validation_needed=True
                    )
            
            elif current_suggestion:
                # Parse details
                if "Reasoning:" in line:
                    current_suggestion.reasoning = line.split("Reasoning:", 1)[1].strip()
                elif "Expected Improvement:" in line:
                    improvement_text = line.split("Expected Improvement:", 1)[1].strip()
                    try:
                        current_suggestion.expected_improvement = float(re.search(r'(\d\.?\d?)', improvement_text).group(1))
                    except:
                        current_suggestion.expected_improvement = 0.5
                elif "Confidence:" in line:
                    confidence_text = line.split("Confidence:", 1)[1].strip()
                    try:
                        current_suggestion.confidence = float(re.search(r'(\d\.?\d?)', confidence_text).group(1))
                    except:
                        current_suggestion.confidence = 0.5
        
        # Add final suggestion
        if current_suggestion:
            improvements.append(current_suggestion)
        
        return improvements
    
    def identify_problematic_mappings(self, mappings: Dict[str, str], 
                                   validation_results: Dict[str, MappingValidation],
                                   readability_results: Dict[str, List[ReadabilityResult]]) -> Dict[str, List[str]]:
        """Identify mappings that need attention"""
        
        problems = defaultdict(list)
        
        for word, emoji in mappings.items():
            issues = []
            
            # Check validation issues
            if word in validation_results:
                validation = validation_results[word]
                if validation.status in [ValidationStatus.WEAK, ValidationStatus.REJECTED]:
                    issues.append(f"Poor validation score: {validation.overall_score:.2f}")
                if validation.issues:
                    issues.extend([f"Validation: {issue}" for issue in validation.issues])
            
            # Check readability issues
            if word in readability_results:
                results = readability_results[word]
                avg_readability = sum(r.score for r in results) / len(results)
                if avg_readability < self.config["readability_threshold"]:
                    issues.append(f"Poor readability: {avg_readability:.2f}")
                
                # Collect common readability issues
                all_issues = []
                for result in results:
                    all_issues.extend(result.issues_identified)
                issue_counts = Counter(all_issues)
                for issue, count in issue_counts.most_common(2):
                    if count >= 2:  # Issue appears in multiple tests
                        issues.append(f"Readability: {issue}")
            
            if issues:
                problems[word] = issues
                
                # Add to manual review queue if very problematic
                severity_score = len(issues)
                if word in validation_results:
                    severity_score += (5.0 - validation_results[word].overall_score)
                if word in readability_results:
                    avg_read = sum(r.score for r in readability_results[word]) / len(readability_results[word])
                    severity_score += (5.0 - avg_read)
                
                if severity_score >= self.config["manual_review_threshold"] * 3:
                    self.manual_review_queue.append((word, emoji, f"Severity: {severity_score:.1f}"))
        
        return problems
    
    def run_refinement_iteration(self, mappings: Dict[str, str], 
                               sample_size: Optional[int] = None) -> RefinementIteration:
        """Run a complete refinement iteration"""
        
        self.current_iteration += 1
        start_time = datetime.datetime.now()
        
        logger.info(f"🔄 Starting refinement iteration {self.current_iteration}")
        
        # Sample mappings if requested
        if sample_size and len(mappings) > sample_size:
            sample_words = random.sample(list(mappings.keys()), sample_size)
            sample_mappings = {word: mappings[word] for word in sample_words}
        else:
            sample_mappings = mappings
        
        logger.info(f"Processing {len(sample_mappings)} mappings")
        
        # Stage 1: Initial Review (Validation)
        logger.info("Stage 1: Initial validation review...")
        validation_results = {}
        for word, emoji in tqdm(sample_mappings.items(), desc="Validating"):
            validation_results[word] = self.validator.validate_single_mapping(word, emoji)
            time.sleep(0.1)  # Rate limiting
        
        # Stage 2: Readability Testing
        logger.info("Stage 2: Readability testing...")
        readability_results = {}
        total_tests = 0
        
        for word, emoji in tqdm(sample_mappings.items(), desc="Testing readability"):
            tests = self.generate_readability_tests(word, emoji, self.config["test_sentences_per_word"])
            results = []
            
            for test in tests:
                result = self.test_readability(test)
                results.append(result)
                time.sleep(0.1)
            
            readability_results[word] = results
            total_tests += len(results)
        
        # Stage 3: Problem Collection
        logger.info("Stage 3: Collecting problematic mappings...")
        problems = self.identify_problematic_mappings(sample_mappings, validation_results, readability_results)
        self.problematic_mappings.update(problems)
        
        # Stage 4: Improvement Generation
        logger.info("Stage 4: Generating improvements...")
        improvements_count = 0
        
        for word, issues in tqdm(problems.items(), desc="Generating improvements"):
            if word in validation_results and word in readability_results:
                improvements = self.generate_mapping_improvements(
                    word, sample_mappings[word], 
                    validation_results[word], 
                    readability_results[word]
                )
                if improvements:
                    self.improvement_suggestions[word].extend(improvements)
                    improvements_count += len(improvements)
                time.sleep(0.1)
        
        # Calculate metrics
        avg_validation_score = sum(v.overall_score for v in validation_results.values()) / len(validation_results)
        all_readability_scores = []
        for results in readability_results.values():
            all_readability_scores.extend([r.score for r in results])
        avg_readability_score = sum(all_readability_scores) / len(all_readability_scores) if all_readability_scores else 0.0
        
        # Create iteration result
        iteration = RefinementIteration(
            iteration_number=self.current_iteration,
            stage=RefinementStage.ITERATION_COMPLETE,
            timestamp=start_time,
            mappings_reviewed=len(sample_mappings),
            improvements_suggested=improvements_count,
            readability_tests=total_tests,
            avg_readability_score=avg_readability_score,
            problems_identified=len(problems),
            manual_review_items=len([item for item in self.manual_review_queue 
                                   if any(word in item[0] for word in problems.keys())]),
            next_actions=self._generate_next_actions(problems, improvements_count, avg_readability_score)
        )
        
        self.iteration_history.append(iteration)
        
        logger.info(f"✅ Iteration {self.current_iteration} complete:")
        logger.info(f"  - Mappings reviewed: {iteration.mappings_reviewed}")
        logger.info(f"  - Problems identified: {iteration.problems_identified}")
        logger.info(f"  - Improvements suggested: {iteration.improvements_suggested}")
        logger.info(f"  - Average readability: {iteration.avg_readability_score:.2f}")
        logger.info(f"  - Manual review items: {iteration.manual_review_items}")
        
        return iteration
    
    def _generate_next_actions(self, problems: Dict[str, List[str]], 
                             improvements_count: int, 
                             avg_readability: float) -> List[str]:
        """Generate recommended next actions"""
        actions = []
        
        if len(problems) > len(problems) * 0.3:  # More than 30% have problems
            actions.append("High problem rate - consider systematic mapping review")
        
        if avg_readability < 2.5:
            actions.append("Low readability scores - focus on clearer emoji choices")
        
        if improvements_count > 0:
            actions.append(f"Apply {improvements_count} generated improvements")
        
        if len(self.manual_review_queue) > 10:
            actions.append("Process manual review queue - many complex cases identified")
        
        if not actions:
            actions.append("Quality looks good - consider testing with more mappings")
        
        return actions
    
    def _call_llm(self, prompt: str, max_tokens: int = 800, temperature: float = 0.1) -> Optional[str]:
        """Call LLM API"""
        try:
            response = self.session.post(
                f"{self.llm_base_url}/v1/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.8,
                },
                timeout=45
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'choices' not in result or not result['choices']:
                return None
            
            return result['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return None
    
    def run_progressive_refinement(self, mappings: Dict[str, str], 
                                 max_iterations: Optional[int] = None) -> Dict:
        """Run complete progressive refinement process"""
        
        max_iter = max_iterations or self.config["max_iterations"]
        logger.info(f"🚀 Starting progressive refinement process (max {max_iter} iterations)")
        
        results = {
            "iterations": [],
            "final_problems": {},
            "final_improvements": {},
            "manual_review_queue": [],
            "quality_progression": [],
            "recommendations": []
        }
        
        # Run iterations
        for i in range(max_iter):
            # Use progressively larger samples
            sample_size = min(50 + (i * 25), len(mappings))
            
            iteration = self.run_refinement_iteration(mappings, sample_size)
            results["iterations"].append(asdict(iteration))
            results["quality_progression"].append({
                "iteration": iteration.iteration_number,
                "avg_readability": iteration.avg_readability_score,
                "problems_rate": iteration.problems_identified / iteration.mappings_reviewed,
                "improvements_rate": iteration.improvements_suggested / max(iteration.problems_identified, 1)
            })
            
            # Check convergence
            if self._check_convergence():
                logger.info(f"Convergence detected after {i+1} iterations")
                break
        
        # Compile final results
        results["final_problems"] = dict(self.problematic_mappings)
        results["final_improvements"] = {
            word: [asdict(imp) for imp in improvements] 
            for word, improvements in self.improvement_suggestions.items()
        }
        results["manual_review_queue"] = self.manual_review_queue
        results["recommendations"] = self._generate_final_recommendations()
        
        logger.info(f"🏁 Progressive refinement complete!")
        logger.info(f"  - Total iterations: {len(results['iterations'])}")
        logger.info(f"  - Final problems identified: {len(results['final_problems'])}")
        logger.info(f"  - Total improvements suggested: {sum(len(imps) for imps in self.improvement_suggestions.values())}")
        logger.info(f"  - Manual review items: {len(results['manual_review_queue'])}")
        
        return results
    
    def _check_convergence(self) -> bool:
        """Check if refinement process has converged"""
        if len(self.iteration_history) < 2:
            return False
        
        # Check if improvement rate is slowing down
        last_two = self.iteration_history[-2:]
        
        improvement_rate_1 = last_two[0].improvements_suggested / max(last_two[0].problems_identified, 1)
        improvement_rate_2 = last_two[1].improvements_suggested / max(last_two[1].problems_identified, 1)
        
        # Check if readability scores are plateauing
        readability_improvement = abs(last_two[1].avg_readability_score - last_two[0].avg_readability_score)
        
        return (readability_improvement < 0.1 and 
                abs(improvement_rate_2 - improvement_rate_1) < 0.2)
    
    def _generate_final_recommendations(self) -> List[str]:
        """Generate final recommendations based on refinement results"""
        recommendations = []
        
        if self.iteration_history:
            latest = self.iteration_history[-1]
            
            if latest.avg_readability_score < 3.0:
                recommendations.append(
                    f"Average readability score is {latest.avg_readability_score:.2f} - "
                    "consider systematic review of emoji choices"
                )
            
            if latest.problems_identified / latest.mappings_reviewed > 0.4:
                recommendations.append(
                    "High problem rate detected - consider revising mapping strategy"
                )
            
            if len(self.manual_review_queue) > 20:
                recommendations.append(
                    "Large manual review queue - prioritize human review of complex mappings"
                )
            
            # Analyze improvement patterns
            top_improvements = []
            for word, improvements in self.improvement_suggestions.items():
                if improvements:
                    best_imp = max(improvements, key=lambda x: x.expected_improvement * x.confidence)
                    if best_imp.expected_improvement > 0.8 and best_imp.confidence > 0.7:
                        top_improvements.append((word, best_imp))
            
            if top_improvements:
                recommendations.append(
                    f"Apply {len(top_improvements)} high-confidence improvements immediately"
                )
        
        if not recommendations:
            recommendations.append("Mapping quality appears good - continue monitoring")
        
        return recommendations
    
    def save_refinement_results(self, results: Dict, output_dir: str = "refinement_results"):
        """Save refinement results to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save main results
        with open(os.path.join(output_dir, "refinement_results.json"), 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save manual review queue
        with open(os.path.join(output_dir, "manual_review_queue.json"), 'w', encoding='utf-8') as f:
            json.dump(self.manual_review_queue, f, indent=2)
        
        # Generate summary report
        report = self._generate_summary_report(results)
        with open(os.path.join(output_dir, "refinement_summary.md"), 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Refinement results saved to {output_dir}/")
    
    def _generate_summary_report(self, results: Dict) -> str:
        """Generate human-readable summary report"""
        lines = [
            "# Progressive Refinement Summary Report",
            "=" * 50,
            "",
            f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Iterations:** {len(results['iterations'])}",
            ""
        ]
        
        # Iteration summary
        if results["iterations"]:
            lines.extend([
                "## Iteration Summary",
                "",
                "| Iteration | Mappings | Problems | Improvements | Avg Readability |",
                "|-----------|----------|----------|--------------|-----------------|"
            ])
            
            for iter_data in results["iterations"]:
                lines.append(
                    f"| {iter_data['iteration_number']} | "
                    f"{iter_data['mappings_reviewed']} | "
                    f"{iter_data['problems_identified']} | "
                    f"{iter_data['improvements_suggested']} | "
                    f"{iter_data['avg_readability_score']:.2f} |"
                )
            
            lines.append("")
        
        # Quality progression
        if results["quality_progression"]:
            lines.extend([
                "## Quality Progression",
                "",
                "Readability scores improved over iterations:",
                ""
            ])
            
            for prog in results["quality_progression"]:
                lines.append(f"- Iteration {prog['iteration']}: {prog['avg_readability']:.2f}")
            
            lines.append("")
        
        # Top problems
        if results["final_problems"]:
            lines.extend([
                "## Top Problematic Mappings",
                ""
            ])
            
            # Sort by number of issues
            sorted_problems = sorted(
                results["final_problems"].items(), 
                key=lambda x: len(x[1]), 
                reverse=True
            )[:10]
            
            for word, issues in sorted_problems:
                lines.extend([
                    f"### {word}",
                    "**Issues:**"
                ])
                for issue in issues:
                    lines.append(f"- {issue}")
                lines.append("")
        
        # Recommendations
        if results["recommendations"]:
            lines.extend([
                "## Recommendations",
                ""
            ])
            for i, rec in enumerate(results["recommendations"], 1):
                lines.append(f"{i}. {rec}")
            lines.append("")
        
        # Manual review queue
        if results["manual_review_queue"]:
            lines.extend([
                f"## Manual Review Queue ({len(results['manual_review_queue'])} items)",
                "",
                "Items requiring human review:",
                ""
            ])
            
            for word, emoji, reason in results["manual_review_queue"][:10]:  # Top 10
                lines.append(f"- **{word}** → {emoji} ({reason})")
            
            if len(results["manual_review_queue"]) > 10:
                lines.append(f"- ... and {len(results['manual_review_queue']) - 10} more items")
        
        return "\n".join(lines)

# Example usage and testing
if __name__ == "__main__":
    # Initialize refinement system
    refinement_system = ProgressiveRefinementSystem()
    
    # Load current mappings
    mappings = refinement_system.load_current_mappings()
    
    if mappings:
        print(f"Loaded {len(mappings)} mappings")
        
        # Run progressive refinement on a small sample for testing
        sample_mappings = dict(list(mappings.items())[:20])  # Test with 20 mappings
        
        print("Starting progressive refinement process...")
        results = refinement_system.run_progressive_refinement(sample_mappings, max_iterations=2)
        
        # Save results
        refinement_system.save_refinement_results(results)
        print("Refinement complete! Check refinement_results/ for detailed output.")
        
    else:
        print("No mappings found - please ensure mappings/word_to_emoji.json exists")
