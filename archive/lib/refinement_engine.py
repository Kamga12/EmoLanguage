#!/usr/bin/env python3
"""
Iterative Mapping Refinement System

This module implements an iterative refinement process to continuously
improve emoji mapping quality through feedback loops and quality assessment.
"""

import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from dataclasses import dataclass

from lib.quality_validator import MappingQualityValidator, QualityScore, validate_mapping_batch
from lib.semantic_categorizer import SemanticCategorizer, create_category_specific_prompt
from lib.file_manager import NewMapping

logger = logging.getLogger(__name__)

@dataclass
class RefinementResult:
    """Result of a refinement iteration"""
    iteration: int
    improved_mappings: List[NewMapping]
    quality_improvement: float
    issues_resolved: int
    remaining_issues: int

class MappingRefinementEngine:
    """Engine for iterative mapping quality improvement"""
    
    def __init__(self, llm_client, file_manager):
        self.llm_client = llm_client
        self.file_manager = file_manager
        self.validator = MappingQualityValidator()
        self.categorizer = SemanticCategorizer()
        
        # Refinement parameters
        self.quality_threshold = 70.0  # Minimum acceptable quality score
        self.max_iterations = 3        # Maximum refinement iterations per word
        self.batch_size = 20           # Words to refine per batch
        
    def identify_low_quality_mappings(self, mappings: Dict[str, str], 
                                    threshold: Optional[float] = None) -> List[Tuple[str, str, QualityScore]]:
        """Identify mappings that need quality improvement"""
        threshold = threshold or self.quality_threshold
        
        logger.info(f"🔍 Identifying mappings below quality threshold ({threshold})")
        
        low_quality = []
        sample_size = min(200, len(mappings))  # Validate a reasonable sample
        
        # Sample mappings for validation
        import random
        sample_items = random.sample(list(mappings.items()), sample_size)
        
        for word, emoji in sample_items:
            score = self.validator.validate_mapping(word, emoji, mappings)
            if score.overall_score < threshold:
                low_quality.append((word, emoji, score))
        
        logger.info(f"Found {len(low_quality)} mappings needing improvement out of {sample_size} sampled")
        return sorted(low_quality, key=lambda x: x[2].overall_score)
    
    def refine_mappings_batch(self, low_quality_mappings: List[Tuple[str, str, QualityScore]], 
                            existing_emojis: set) -> List[NewMapping]:
        """Refine a batch of low-quality mappings"""
        
        if not low_quality_mappings:
            return []
        
        logger.info(f"🔧 Refining {len(low_quality_mappings)} low-quality mappings")
        
        # Prepare words and analysis for categorized prompting
        words_with_analysis = []
        for word, emoji, score in low_quality_mappings:
            analysis = self.categorizer.categorize_word(word)
            words_with_analysis.append((word, analysis))
        
        # Create category-specific prompt
        existing_emojis_text = ", ".join(list(existing_emojis)[:50])  # Sample for prompt
        prompt = self._create_refinement_prompt(words_with_analysis, low_quality_mappings, existing_emojis_text)
        
        logger.info("📤 REFINEMENT PROMPT BEING SENT TO LLM:")
        logger.info("=" * 50)
        logger.info(prompt[:1000] + "..." if len(prompt) > 1000 else prompt)
        logger.info("=" * 50)
        
        # Get refined mappings from LLM
        word_mappings = self.llm_client.call_llm_for_word_mappings(prompt, temperature=0.7, max_tokens=10000)
        
        if not word_mappings:
            logger.error("Failed to get refinement response from LLM")
            return []
        
        # Convert to NewMapping objects
        refined_mappings = []
        for word, emoji in word_mappings.items():
            if emoji and emoji not in existing_emojis:
                refined_mappings.append(NewMapping(
                    word=word,
                    suggested_emojis=emoji,
                    category='refined'
                ))
        
        logger.info(f"✅ Successfully refined {len(refined_mappings)} mappings")
        return refined_mappings
    
    def _create_refinement_prompt(self, words_with_analysis: List[Tuple[str, Any]], 
                                low_quality_mappings: List[Tuple[str, str, Any]], 
                                existing_emojis: str) -> str:
        """Create a specialized prompt for mapping refinement"""
        
        # Create mapping of word to current emoji and issues
        word_to_current = {}
        word_to_issues = {}
        for word, emoji, score in low_quality_mappings:
            word_to_current[word] = emoji
            word_to_issues[word] = score.issues
        
        prompt_parts = [
            "# Role",
            "You are an expert emoji mapping specialist focused on improving low-quality word-to-emoji mappings.",
            "",
            "# Task",
            "Improve the provided mappings by addressing specific quality issues while maintaining semantic accuracy.",
            "",
            "# Current Mappings and Issues"
        ]
        
        for word, analysis in words_with_analysis:
            current_emoji = word_to_current.get(word, "")
            issues = word_to_issues.get(word, [])
            
            prompt_parts.append(f"\n- **{word}** (currently: {current_emoji})")
            prompt_parts.append(f"  Category: {analysis.category.value}")
            prompt_parts.append(f"  Strategy: {analysis.suggested_strategy}")
            if issues:
                issue_names = [issue.value.replace('_', ' ') for issue in issues]
                prompt_parts.append(f"  Issues to fix: {', '.join(issue_names)}")
        
        prompt_parts.extend([
            f"\n# Existing Emojis (avoid these):",
            existing_emojis,
            "",
            "# Refinement Guidelines:",
            "",
            "## Quality Priorities",
            "1. **Semantic Accuracy**: Emoji must clearly represent the word's meaning",
            "2. **Visual Clarity**: Easy to interpret at a glance",
            "3. **Appropriate Complexity**: Match emoji complexity to word complexity",
            "4. **Cultural Neutrality**: Avoid flags, skin tones, regional symbols",
            "",
            "## Specific Improvements",
            "- **Over-complex mappings**: Simplify while maintaining meaning",
            "- **Under-specific mappings**: Add descriptive emoji for clarity",
            "- **Unclear sequences**: Use more intuitive emoji combinations",
            "- **Repetitive patterns**: Vary emoji usage creatively",
            "",
            "## Success Criteria",
            "- Single emoji for simple, directly-representable concepts",
            "- 2-4 emoji for moderate complexity words",
            "- 3-6 emoji for complex or abstract concepts",
            "- Logical flow in multi-emoji sequences",
            "- Universal recognition across cultures",
            "",
            "# Output Format",
            "Return only a JSON array of {\"word\":\"improved_emoji_combo\"} objects.",
            "Provide exactly one improved mapping for each input word."
        ])
        
        return "\n".join(prompt_parts)
    
    def run_iterative_refinement(self, mappings: Dict[str, str], 
                               max_words: int = 100) -> RefinementResult:
        """Run iterative refinement on the mapping set"""
        
        logger.info(f"🚀 Starting iterative refinement process")
        
        # Get existing emojis to avoid collisions
        existing_emojis = set(mappings.values())
        
        # Identify low-quality mappings
        low_quality = self.identify_low_quality_mappings(mappings)[:max_words]
        
        if not low_quality:
            logger.info("✅ No low-quality mappings found - refinement not needed")
            return RefinementResult(0, [], 0.0, 0, 0)
        
        initial_avg_score = sum(score.overall_score for _, _, score in low_quality) / len(low_quality)
        
        # Process in batches
        all_improved = []
        total_issues_before = sum(len(score.issues) for _, _, score in low_quality)
        
        for i in range(0, len(low_quality), self.batch_size):
            batch = low_quality[i:i + self.batch_size]
            logger.info(f"Processing refinement batch {i//self.batch_size + 1}")
            
            improved_batch = self.refine_mappings_batch(batch, existing_emojis)
            all_improved.extend(improved_batch)
            
            # Update existing emojis to avoid future collisions
            for mapping in improved_batch:
                existing_emojis.add(mapping.suggested_emojis)
        
        # Validate improvements
        improved_words = {m.word for m in all_improved}
        issues_resolved = 0
        final_avg_score = initial_avg_score
        
        if all_improved:
            # Re-validate improved mappings
            improved_mappings_dict = {m.word: m.suggested_emojis for m in all_improved}
            improved_scores = []
            
            for mapping in all_improved:
                score = self.validator.validate_mapping(mapping.word, mapping.suggested_emojis, mappings)
                improved_scores.append(score.overall_score)
                issues_resolved += len([i for i in score.issues if i not in 
                                     [item[2].issues for item in low_quality if item[0] == mapping.word][0]])
            
            final_avg_score = sum(improved_scores) / len(improved_scores) if improved_scores else initial_avg_score
        
        improvement = final_avg_score - initial_avg_score
        remaining_issues = total_issues_before - issues_resolved
        
        logger.info(f"📊 Refinement Results:")
        logger.info(f"  Processed words: {len(improved_words)}")
        logger.info(f"  Average quality improvement: {improvement:.1f} points")
        logger.info(f"  Issues resolved: {issues_resolved}")
        logger.info(f"  Remaining issues: {remaining_issues}")
        
        return RefinementResult(
            iteration=1,
            improved_mappings=all_improved,
            quality_improvement=improvement,
            issues_resolved=issues_resolved,
            remaining_issues=remaining_issues
        )
    
    def generate_quality_report(self, mappings: Dict[str, str]) -> Dict:
        """Generate a comprehensive quality report for the mapping set"""
        
        logger.info("📊 Generating comprehensive quality report...")
        
        # Sample validation
        stats = validate_mapping_batch(mappings, sample_size=200)
        
        # Category analysis
        category_stats = {}
        sample_items = list(mappings.items())[:100]  # Analyze first 100 for categories
        
        for word, emoji in sample_items:
            analysis = self.categorizer.categorize_word(word)
            category = analysis.category.value
            
            if category not in category_stats:
                category_stats[category] = {'count': 0, 'avg_length': 0, 'examples': []}
            
            category_stats[category]['count'] += 1
            category_stats[category]['avg_length'] += len(emoji)
            if len(category_stats[category]['examples']) < 3:
                category_stats[category]['examples'].append((word, emoji))
        
        # Calculate averages
        for category in category_stats:
            if category_stats[category]['count'] > 0:
                category_stats[category]['avg_length'] /= category_stats[category]['count']
        
        report = {
            'overall_stats': stats,
            'category_analysis': category_stats,
            'recommendations': self._generate_recommendations(stats, category_stats)
        }
        
        return report
    
    def _generate_recommendations(self, stats: Dict, category_stats: Dict) -> List[str]:
        """Generate actionable recommendations based on quality analysis"""
        recommendations = []
        
        if stats['average_score'] < 70:
            recommendations.append("Overall mapping quality is below target - consider comprehensive refinement")
        
        if stats['poor_count'] > stats['total_validated'] * 0.2:
            recommendations.append("High proportion of poor-quality mappings detected - prioritize refinement")
        
        # Category-specific recommendations
        for category, data in category_stats.items():
            if data['avg_length'] > 6:
                recommendations.append(f"Consider simplifying {category} mappings - average length is {data['avg_length']:.1f}")
        
        if not recommendations:
            recommendations.append("Mapping quality appears good - consider periodic refinement for continuous improvement")
        
        return recommendations
