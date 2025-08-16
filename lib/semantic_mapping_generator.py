#!/usr/bin/env python3
"""
Refactored Semantic Mapping Generator

This refactored version separates concerns into focused classes and utility functions.
The main class now orchestrates the process rather than handling all details.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .llm_client import LLMClient
from .file_manager import FileManager, NewMapping
from .collision_manager import CollisionManager
from .config import (
    BATCH_GENERATION_PROMPT_TEMPLATE,
    COLLISION_RESOLUTION_PROMPT_TEMPLATE,
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_MAPPING_BATCH_SIZE,
    DEFAULT_COLLISION_BATCH_SIZE,
    RETRY_EMOJI_MARKER
)
from .utils import (
    format_words_for_prompt,
    format_existing_emojis_for_prompt,
    format_existing_emojis_for_collision_prompt,
    truncate_prompt_for_logging,
    convert_word_mappings_to_new_mappings,
    validate_word_mappings,
    create_generation_report,
    analyze_mappings
)
from .word_normalizer import WordNormalizer

logger = logging.getLogger(__name__)

class SemanticMappingGenerator:
    """
    Refactored semantic mapping generator with separated concerns.
    
    This class orchestrates the emoji mapping generation process by coordinating
    between specialized components for LLM interaction, file management, and
    collision resolution.
    """
    
    def __init__(self, 
                 base_url: str = DEFAULT_BASE_URL, 
                 model: str = DEFAULT_MODEL):
        """Initialize the semantic mapping generator with its components"""
        self.llm_client = LLMClient(base_url=base_url, model=model)
        self.file_manager = FileManager()
        self.collision_manager = CollisionManager()
        self.normalizer = WordNormalizer()
        
        logger.info(f"Initialized SemanticMappingGenerator with model: {model}")
    
    def generate_mappings_multipass(self, words: List[str], num_passes: int = 3) -> List[NewMapping]:
        """
        Multi-pass generation with quality validation and consensus building.
        
        Args:
            words: List of words to generate mappings for
            num_passes: Number of LLM passes for consensus building
            
        Returns:
            List of high-quality NewMapping objects
        """
        if not words:
            return []
            
        logger.info(f"🔄 Starting multi-pass generation for {len(words)} words ({num_passes} passes)")
        
        # Step 1: Context-aware word analysis and clustering
        word_clusters = self._cluster_words_by_context(words)
        logger.info(f"📊 Organized words into {len(word_clusters)} semantic clusters")
        
        all_mappings = []
        
        # Step 2: Process each cluster with multi-pass generation
        for cluster_idx, cluster_words in enumerate(word_clusters):
            logger.info(f"🎯 Processing cluster {cluster_idx + 1}/{len(word_clusters)}: {len(cluster_words)} words")
            
            # Generate multiple candidates for this cluster
            cluster_candidates = self._generate_multiple_candidates(cluster_words, num_passes)
            
            # Select best mappings through consensus and quality validation
            best_mappings = self._select_best_mappings(cluster_candidates, cluster_words)
            
            all_mappings.extend(best_mappings)
        
        logger.info(f"✅ Multi-pass generation complete: {len([m for m in all_mappings if m.suggested_emojis])} successful mappings")
        return all_mappings
    
    def _cluster_words_by_context(self, words: List[str]) -> List[List[str]]:
        """
        Cluster words by semantic context for coherent processing.
        Uses simple heuristics to group related words together.
        """
        clusters = []
        remaining_words = words.copy()
        
        while remaining_words:
            # Start a new cluster with the first remaining word
            seed_word = remaining_words.pop(0)
            current_cluster = [seed_word]
            
            # Find related words for this cluster
            words_to_remove = []
            for word in remaining_words:
                if self._are_words_contextually_related(seed_word, word):
                    current_cluster.append(word)
                    words_to_remove.append(word)
            
            # Remove clustered words from remaining
            for word in words_to_remove:
                remaining_words.remove(word)
            
            clusters.append(current_cluster)
            
            # Limit cluster size for manageable processing
            if len(current_cluster) > 8:
                # Split large clusters
                mid_point = len(current_cluster) // 2
                clusters[-1] = current_cluster[:mid_point]
                clusters.append(current_cluster[mid_point:])
        
        return clusters
    
    def _are_words_contextually_related(self, word1: str, word2: str) -> bool:
        """
        Determine if two words are contextually related using simple heuristics.
        """
        # Length similarity (words of similar complexity)
        if abs(len(word1) - len(word2)) <= 2 and min(len(word1), len(word2)) >= 6:
            return True
        
        # Common prefixes/suffixes (morphological relationships)
        if len(word1) >= 4 and len(word2) >= 4:
            if word1[:3] == word2[:3] or word1[-3:] == word2[-3:]:
                return True
        
        # Domain-specific patterns
        technical_suffixes = ['tion', 'ment', 'ness', 'able', 'ible', 'ology', 'ism']
        word1_technical = any(word1.endswith(suffix) for suffix in technical_suffixes)
        word2_technical = any(word2.endswith(suffix) for suffix in technical_suffixes)
        
        if word1_technical and word2_technical:
            return True
        
        return False
    
    def _generate_multiple_candidates(self, words: List[str], num_passes: int) -> Dict[str, List[str]]:
        """
        Generate multiple emoji candidates for each word across multiple LLM passes.
        """
        candidates = {word: [] for word in words}
        
        for pass_num in range(num_passes):
            logger.info(f"  🔄 Pass {pass_num + 1}/{num_passes} for {len(words)} words")
            
            # Create context-aware prompt for this pass
            prompt = self._create_context_aware_prompt(words, pass_num, num_passes)
            
            # Adjust temperature for diversity across passes
            temperature = 0.6 + (pass_num * 0.15)  # Increase creativity in later passes
            
            # Use new method that returns match scores
            word_mappings_with_scores = self.llm_client.call_llm_for_word_mappings_with_scores(
                prompt, temperature=temperature, max_tokens=50000
            )
            
            if word_mappings_with_scores:
                for mapping in word_mappings_with_scores:
                    word = mapping.get('word')
                    emoji = mapping.get('emoji_combo')
                    match_score = mapping.get('match_score', 0.0)
                    
                    if word and emoji and word in candidates:
                        # Store emoji with its match score for later use
                        candidates[word].append({'emoji': emoji, 'score': match_score})
                        
        logger.info(f"  📊 Generated candidates: {sum(len(c) for c in candidates.values())} total options")
        return candidates
    
    def _create_context_aware_prompt(self, words: List[str], pass_num: int, total_passes: int) -> str:
        """
        Create a context-aware prompt that considers word relationships and pass number.
        Includes word variants and usage examples to give the LLM better context.
        Updated to request match scores in response.
        """
        # Get existing mappings for context
        existing_mappings = self.file_manager.load_existing_mappings()
        
        # Build context from related existing mappings using word variants
        context_examples = []
        max_context_examples = 6  # Allow more context examples since we're being smarter about finding them
        
        for word in words:
            # Generate variants for this word to help find related mappings
            word_variants = self._get_word_variants(word)
            all_word_forms = [word] + word_variants
            
            # Find similar words that already have mappings using multiple strategies
            word_related_examples = []
            
            # Strategy 1: Direct match - check if any variant already has a mapping
            for word_form in all_word_forms:
                if word_form in existing_mappings:
                    emoji = existing_mappings[word_form]
                    example = f'"{word_form}": "{emoji}"'
                    if example not in word_related_examples:
                        word_related_examples.append(example)
            
            # Strategy 2: Morphological similarity - check existing mappings for words related to our variants
            for existing_word, existing_emoji in existing_mappings.items():
                # Check if existing word is similar to any of our word forms
                for word_form in all_word_forms:
                    if self._are_words_contextually_related(word_form, existing_word):
                        example = f'"{existing_word}": "{existing_emoji}"'
                        if example not in word_related_examples:
                            word_related_examples.append(example)
                        break  # Found a match, move to next existing word
                
                # Also check if any existing word's variants relate to our base word
                existing_variants = self._generate_morphological_variants(existing_word)
                for existing_variant in existing_variants:
                    if existing_variant in all_word_forms:
                        example = f'"{existing_word}": "{existing_emoji}"'
                        if example not in word_related_examples:
                            word_related_examples.append(example)
                        break
            
            # Add the best examples for this word to our context
            context_examples.extend(word_related_examples[:2])  # Max 2 examples per word
            if len(context_examples) >= max_context_examples:
                break
        
        prompt = "Generate emoji mappings for the following words and return as a JSON array.\n\n"
        
        if context_examples:
            prompt += "**Context from related mappings:**\n"
            for example in context_examples[:3]:  # Show top 3 examples
                prompt += f"- {example}\n"
            prompt += "\n"
        
        # Add pass-specific instructions
        if pass_num == 0:
            prompt += "**Instructions:** Focus on the most direct and intuitive emoji representations.\n"
        elif pass_num == 1:
            prompt += "**Instructions:** Consider alternative creative representations that capture the essence.\n"
        else:
            prompt += "**Instructions:** Think creatively about unique emoji combinations that haven't been tried.\n"
        
        prompt += "\n**Words to map:**\n"
        for word in words:
            prompt += f"- {word}\n"
        
        # Add word usage section to provide context about word variants and forms
        prompt += "\n**Usage of Words:**\n"
        for word in words:
            word_variants = self._get_word_variants(word)
            if word_variants:
                prompt += f"- {word}: {', '.join(word_variants)}\n"
            else:
                prompt += f"- {word}: (base form)\n"
        
        # Updated output format to include match scores
        prompt += '\n**Output format:** Return a JSON array with objects containing word, emoji_combo, and match_score: `{"word":"...", "emoji_combo":"...", "match_score": 0.95}`\n'
        prompt += '\n**Match score:** Float from 0.0 to 1.0 indicating confidence in emoji mapping quality:\n'
        prompt += '- 1.0: Perfect semantic match, universally recognizable\n'
        prompt += '- 0.8-0.9: Very good match, clear connection\n'
        prompt += '- 0.6-0.7: Good match, reasonable representation\n'
        prompt += '- 0.4-0.5: Acceptable match, some ambiguity\n'
        prompt += '- 0.0-0.3: Poor match, forced or unclear\n'
        prompt += "\n**Example:** [{\"word\":\"cat\", \"emoji_combo\":\"🐱\", \"match_score\": 0.95}, {\"word\":\"happy\", \"emoji_combo\":\"😊\", \"match_score\": 0.90}]\n"
        prompt += "\nGenerate the JSON array now:"
        
        return prompt
    
    def _get_word_variants(self, word: str) -> List[str]:
        """
        Generate word variants and usage forms to help the LLM understand context.
        Uses the word normalizer to find potential related forms and adds common variations.
        """
        variants = []
        
        # Get all existing mappings to search for related words
        existing_mappings = self.file_manager.load_existing_mappings()
        all_existing_words = set(existing_mappings.keys())
        
        # Use the word normalizer to find words that normalize to the same base
        word_groups = self.normalizer.analyze_word_groups(list(all_existing_words))
        
        # Find the group that contains our target word
        normalized_word = self.normalizer.normalize_word(word)
        if normalized_word in word_groups:
            related_words = word_groups[normalized_word]
            # Add related words that aren't the base word itself
            for related_word in related_words:
                if related_word != word:
                    variants.append(related_word)
        
        # Generate common morphological variants even if not in existing mappings
        base_variants = self._generate_morphological_variants(word)
        for variant in base_variants:
            if variant not in variants and variant != word:
                variants.append(variant)
        
        # Limit to reasonable number and sort by relevance
        variants = variants[:8]  # Limit to 8 variants max
        
        return variants
    
    def _generate_morphological_variants(self, word: str) -> List[str]:
        """
        Generate common morphological variants for a word to show usage context.
        """
        variants = []
        word = word.lower().strip()
        
        if len(word) < 3:
            return variants
            
        # Common verb forms
        if not word.endswith(('ing', 'ed', 'er', 'est', 's')):
            # Add present participle
            if word.endswith('e'):
                variants.append(word[:-1] + 'ing')  # make -> making
            elif len(word) >= 3 and word[-1] in 'bcdfghjklmnpqrstvwxyz' and word[-2] in 'aeiou' and word[-3] in 'bcdfghjklmnpqrstvwxyz':
                variants.append(word + word[-1] + 'ing')  # run -> running
            else:
                variants.append(word + 'ing')  # walk -> walking
                
            # Add past tense
            if word.endswith('e'):
                variants.append(word + 'd')  # make -> made (this is imperfect, but gives context)
            elif len(word) >= 3 and word[-1] in 'bcdfghjklmnpqrstvwxyz' and word[-2] in 'aeiou' and word[-3] in 'bcdfghjklmnpqrstvwxyz':
                variants.append(word + word[-1] + 'ed')  # stop -> stopped
            else:
                variants.append(word + 'ed')  # walk -> walked
                
            # Add third person singular
            if word.endswith(('s', 'sh', 'ch', 'x', 'z')):
                variants.append(word + 'es')  # wash -> washes
            elif word.endswith('y') and len(word) > 1 and word[-2] not in 'aeiou':
                variants.append(word[:-1] + 'ies')  # try -> tries
            else:
                variants.append(word + 's')  # walk -> walks
        
        # Common noun plurals (if not already a verb form)
        if not word.endswith(('ing', 'ed', 'er', 'est')) and len(word) >= 3:
            if word.endswith(('s', 'sh', 'ch', 'x', 'z')):
                variants.append(word + 'es')  # box -> boxes
            elif word.endswith('y') and len(word) > 1 and word[-2] not in 'aeiou':
                variants.append(word[:-1] + 'ies')  # city -> cities  
            elif word.endswith('f'):
                variants.append(word[:-1] + 'ves')  # leaf -> leaves
            elif word.endswith('fe'):
                variants.append(word[:-2] + 'ves')  # knife -> knives
            else:
                variants.append(word + 's')  # cat -> cats
        
        # Common adjective/adverb forms
        if not word.endswith(('er', 'est', 'ly', 'ing', 'ed')):
            # Comparative and superlative
            if len(word) <= 6:  # Short adjectives
                if word.endswith('e'):
                    variants.extend([word + 'r', word + 'st'])  # nice -> nicer, nicest
                elif len(word) >= 3 and word[-1] in 'bcdfghjklmnpqrstvwxyz' and word[-2] in 'aeiou' and word[-3] in 'bcdfghjklmnpqrstvwxyz':
                    variants.extend([word + word[-1] + 'er', word + word[-1] + 'est'])  # big -> bigger, biggest
                else:
                    variants.extend([word + 'er', word + 'est'])  # fast -> faster, fastest
            
            # Adverb form
            if word.endswith('y'):
                variants.append(word[:-1] + 'ily')  # easy -> easily
            elif word.endswith('le'):
                variants.append(word[:-2] + 'ly')  # simple -> simply
            elif word.endswith('ic'):
                variants.append(word + 'ally')  # basic -> basically
            else:
                variants.append(word + 'ly')  # quick -> quickly
        
        # Common derivational forms
        if not any(word.endswith(suffix) for suffix in ['tion', 'sion', 'ness', 'ment', 'ing', 'ed', 'er', 'est', 'ly']):
            # Add -ing form for nouns that can be verbs
            variants.append(word + 'ing')
            
            # Add -er for agent nouns
            if word.endswith('e'):
                variants.append(word + 'r')  # drive -> driver
            else:
                variants.append(word + 'er')  # teach -> teacher
        
        # Remove duplicates and invalid forms
        unique_variants = []
        seen = set()
        for variant in variants:
            if variant not in seen and len(variant) >= 3 and variant != word:
                unique_variants.append(variant)
                seen.add(variant)
        
        return unique_variants[:6]  # Return top 6 variants
    
    def _select_best_mappings(self, candidates: Dict[str, List[Dict[str, float]]], words: List[str]) -> List[NewMapping]:
        """
        Select the best mapping for each word using LLM-provided scores and consensus.
        """
        best_mappings = []
        
        for word in words:
            word_candidates = candidates.get(word, [])
            
            if not word_candidates:
                # No candidates generated
                best_mappings.append(NewMapping(word=word, suggested_emojis='', category='multipass_failed'))
                continue
            
            # Step 1: Aggregate scores for duplicate emojis across passes
            emoji_scores = {}
            for candidate in word_candidates:
                emoji = candidate['emoji']
                score = candidate['score']
                
                if emoji not in emoji_scores:
                    emoji_scores[emoji] = {'scores': [], 'count': 0}
                
                emoji_scores[emoji]['scores'].append(score)
                emoji_scores[emoji]['count'] += 1
            
            # Step 2: Calculate final score for each unique emoji
            scored_candidates = []
            for emoji, data in emoji_scores.items():
                # Combine LLM scores with consensus (frequency)
                avg_llm_score = sum(data['scores']) / len(data['scores'])
                consensus_score = data['count'] / len(word_candidates)  # How often this emoji appeared
                
                # Weighted combination: 70% LLM score, 30% consensus
                final_score = (avg_llm_score * 0.7) + (consensus_score * 0.3)
                
                scored_candidates.append((emoji, final_score, avg_llm_score, consensus_score))
                logger.debug(f"Emoji '{emoji}' for '{word}': LLM={avg_llm_score:.2f}, consensus={consensus_score:.2f}, final={final_score:.2f}")
            
            # Step 3: Select best candidate
            if scored_candidates:
                # Sort by final score (higher is better)
                scored_candidates.sort(key=lambda x: x[1], reverse=True)
                best_emoji, final_score, llm_score, consensus_score = scored_candidates[0]
                
                logger.info(f"✅ Selected for '{word}': {best_emoji} (LLM={llm_score:.2f}, consensus={consensus_score:.2f}, final={final_score:.2f})")
                best_mappings.append(NewMapping(
                    word=word, 
                    suggested_emojis=best_emoji, 
                    category=f'multipass_llm_{final_score:.1f}'
                ))
            else:
                best_mappings.append(NewMapping(word=word, suggested_emojis='', category='multipass_failed'))
        
        return best_mappings
    
    def _score_emoji_quality(self, word: str, emoji: str, all_candidates: Dict[str, List[str]]) -> float:
        """
        Score an emoji mapping based on multiple quality factors.
        """
        score = 0.0
        
        # Factor 1: Consensus (how often this emoji was generated)
        word_candidates = all_candidates.get(word, [])
        consensus_count = word_candidates.count(emoji)
        consensus_score = consensus_count / len(word_candidates) if word_candidates else 0
        score += consensus_score * 0.4  # 40% weight
        
        # Factor 2: Complexity appropriateness
        word_complexity = len(word) + (1 if any(c in word for c in 'tion,ment,ness,able'.split(',')) else 0)
        emoji_complexity = len(emoji)
        
        # Prefer simpler emojis for simple words, complex emojis for complex words
        if word_complexity <= 5:  # Simple word
            complexity_score = 1.0 if emoji_complexity <= 2 else 0.5
        else:  # Complex word
            complexity_score = 1.0 if emoji_complexity >= 2 else 0.7
        
        score += complexity_score * 0.3  # 30% weight
        
        # Factor 3: Uniqueness (avoid overused emojis)
        existing_emojis = self.file_manager.get_existing_emojis()
        uniqueness_score = 0.0 if emoji in existing_emojis else 1.0
        score += uniqueness_score * 0.2  # 20% weight
        
        # Factor 4: Semantic appropriateness (basic checks)
        semantic_score = 1.0
        
        # Avoid obviously inappropriate combinations
        if len(emoji) > 6:  # Very long combinations might be overcomplex
            semantic_score -= 0.3
        
        if '🚫' in emoji or '❌' in emoji:  # Negative symbols for non-negative words
            if not any(neg in word.lower() for neg in ['no', 'not', 'anti', 'un']):
                semantic_score -= 0.5
        
        score += semantic_score * 0.1  # 10% weight
        
        return max(0.0, min(1.0, score))  # Clamp to [0, 1]
    
    def generate_mappings_batch(self, words: List[str], num_passes: int = 1) -> List[NewMapping]:
        """Generate multiple word-to-emoji mappings in batch mode with optional multi-pass support
        
        Args:
            words: List of words to generate mappings for
            num_passes: Number of passes to run (1 for single pass, >1 for multi-pass batch mode)
            
        Returns:
            List of NewMapping objects with best scoring emojis selected
        """
        if not words:
            return []
        
        if num_passes == 1:
            # Single pass batch mode (original behavior)
            return self._generate_mappings_batch_single_pass(words)
        else:
            # Multi-pass batch mode (new behavior)
            logger.info(f"🔄 Starting multi-pass BATCH generation for {len(words)} words ({num_passes} passes)")
            return self._generate_mappings_batch_multi_pass(words, num_passes)
    
    def _generate_mappings_batch_single_pass(self, words: List[str]) -> List[NewMapping]:
        """Original single-pass batch generation"""
        # Get existing emojis to avoid duplicates
        existing_emojis = self.file_manager.get_existing_emojis()
        all_used_emojis = self.collision_manager.get_all_used_emojis(existing_emojis)
        
        # Prepare prompt data
        words_text = format_words_for_prompt(words)
        
        # Create the batch generation prompt using new template format
        prompt = BATCH_GENERATION_PROMPT_TEMPLATE.format(words_text=words_text)
        
        # Log the prompt (with truncated emoji list)
        truncated_prompt = truncate_prompt_for_logging(prompt)
        logger.info("📤 BATCH PROMPT BEING SENT TO LLM:")
        logger.info("=" * 50)
        logger.info(truncated_prompt)
        logger.info("=" * 50)
        
        # Make LLM call using the new method that returns match scores
        word_mappings_with_scores = self.llm_client.call_llm_for_word_mappings_with_scores(prompt, temperature=0.8, max_tokens=100000)
        
        if word_mappings_with_scores is None:
            logger.error("Failed to get response from LLM")
            return [NewMapping(word=word, suggested_emojis='', category='error') for word in words]
        
        # Convert response to mappings using the new score-aware approach
        mappings = []
        for mapping_data in word_mappings_with_scores:
            word = mapping_data.get('word')
            emoji = mapping_data.get('emoji_combo')
            match_score = mapping_data.get('match_score', 0.0)
            
            if word and emoji:
                # Include the LLM-provided score in the category for tracking
                category = f'batch_llm_{match_score:.1f}'
                mappings.append(NewMapping(word=word, suggested_emojis=emoji, category=category))
                logger.debug(f"Batch mapping: '{word}' -> '{emoji}' (LLM score: {match_score:.2f})")
            elif word:
                # Word present but no emoji
                mappings.append(NewMapping(word=word, suggested_emojis='', category='batch_error'))
        
        # Ensure all input words are represented
        mapped_words = {m.word for m in mappings}
        for word in words:
            if word not in mapped_words:
                mappings.append(NewMapping(word=word, suggested_emojis='', category='batch_missing'))
        
        # Track newly generated emojis in session
        for mapping in mappings:
            if mapping.suggested_emojis:
                self.collision_manager.track_emoji_usage(mapping.suggested_emojis)
        
        return mappings
    
    def _generate_mappings_batch_multi_pass(self, words: List[str], num_passes: int) -> List[NewMapping]:
        """Multi-pass batch generation - runs batch generation multiple times and selects best scoring results"""
        # Get existing emojis to avoid duplicates
        existing_emojis = self.file_manager.get_existing_emojis()
        all_used_emojis = self.collision_manager.get_all_used_emojis(existing_emojis)
        
        # Prepare prompt data
        words_text = format_words_for_prompt(words)
        prompt = BATCH_GENERATION_PROMPT_TEMPLATE.format(words_text=words_text)
        
        # Log the prompt (with truncated emoji list) once
        truncated_prompt = truncate_prompt_for_logging(prompt)
        logger.info("📤 MULTI-PASS BATCH PROMPT:")
        logger.info("=" * 50)
        logger.info(truncated_prompt)
        logger.info("=" * 50)
        
        # Collect candidates from multiple passes
        all_candidates = {word: [] for word in words}
        
        for pass_num in range(num_passes):
            logger.info(f"  🔄 Batch pass {pass_num + 1}/{num_passes} for {len(words)} words")
            
            # Adjust temperature for diversity across passes
            temperature = 0.7 + (pass_num * 0.1)  # Slightly increase creativity in later passes
            
            # Make LLM call
            word_mappings_with_scores = self.llm_client.call_llm_for_word_mappings_with_scores(
                prompt, temperature=temperature, max_tokens=100000
            )
            
            if word_mappings_with_scores:
                for mapping_data in word_mappings_with_scores:
                    word = mapping_data.get('word')
                    emoji = mapping_data.get('emoji_combo')
                    match_score = mapping_data.get('match_score', 0.0)
                    
                    if word and emoji and word in all_candidates:
                        all_candidates[word].append({
                            'emoji': emoji, 
                            'score': match_score,
                            'pass': pass_num + 1
                        })
                        logger.debug(f"Pass {pass_num + 1}: '{word}' -> '{emoji}' (score: {match_score:.2f})")
        
        # Select best mapping for each word based on scores and frequency
        best_mappings = []
        for word in words:
            candidates = all_candidates.get(word, [])
            
            if not candidates:
                # No candidates from any pass
                best_mappings.append(NewMapping(word=word, suggested_emojis='', category='batch_multi_failed'))
                continue
            
            # Aggregate scores for duplicate emojis across passes
            emoji_scores = {}
            for candidate in candidates:
                emoji = candidate['emoji']
                score = candidate['score']
                
                if emoji not in emoji_scores:
                    emoji_scores[emoji] = {'scores': [], 'count': 0, 'passes': []}
                
                emoji_scores[emoji]['scores'].append(score)
                emoji_scores[emoji]['count'] += 1
                emoji_scores[emoji]['passes'].append(candidate['pass'])
            
            # Calculate final score for each unique emoji
            scored_candidates = []
            for emoji, data in emoji_scores.items():
                # Combine LLM scores with consensus (frequency)
                avg_llm_score = sum(data['scores']) / len(data['scores'])
                consensus_score = data['count'] / len(candidates)  # How often this emoji appeared
                
                # Weighted combination: 80% LLM score, 20% consensus (less emphasis on consensus for batch mode)
                final_score = (avg_llm_score * 0.8) + (consensus_score * 0.2)
                
                scored_candidates.append((emoji, final_score, avg_llm_score, consensus_score, data['passes']))
                logger.debug(f"Multi-pass batch '{word}': '{emoji}' LLM={avg_llm_score:.2f}, consensus={consensus_score:.2f}, final={final_score:.2f}, passes={data['passes']}")
            
            # Select best candidate
            if scored_candidates:
                # Sort by final score (higher is better)
                scored_candidates.sort(key=lambda x: x[1], reverse=True)
                best_emoji, final_score, llm_score, consensus_score, passes = scored_candidates[0]
                
                logger.info(f"✅ Multi-pass batch selected for '{word}': {best_emoji} (LLM={llm_score:.2f}, consensus={consensus_score:.2f}, final={final_score:.2f}, passes={passes})")
                best_mappings.append(NewMapping(
                    word=word, 
                    suggested_emojis=best_emoji, 
                    category=f'batch_multi_llm_{final_score:.1f}'
                ))
            else:
                best_mappings.append(NewMapping(word=word, suggested_emojis='', category='batch_multi_failed'))
        
        # Track newly generated emojis in session
        for mapping in best_mappings:
            if mapping.suggested_emojis:
                self.collision_manager.track_emoji_usage(mapping.suggested_emojis)
        
        logger.info(f"  📊 Multi-pass batch complete: {len([m for m in best_mappings if m.suggested_emojis])}/{len(words)} successful mappings")
        return best_mappings
    
    def resolve_emoji_collisions_with_llm(self, 
                                        collisions: List[Tuple[str, str, str]], 
                                        collision_size: int = DEFAULT_COLLISION_BATCH_SIZE,
                                        num_passes: int = 1) -> List[NewMapping]:
        """Use LLM to intelligently resolve emoji collisions
        
        Args:
            collisions: List of collision tuples to resolve
            collision_size: Batch size for collision resolution
            num_passes: Number of passes for collision resolution (1 for single pass, >1 for multi-pass)
        """
        if not collisions:
            return []
        
        # Get existing emojis to avoid new conflicts
        existing_emojis = self.file_manager.get_existing_emojis()
        all_used_emojis = self.collision_manager.get_all_used_emojis(existing_emojis)
        existing_sample_text = format_existing_emojis_for_collision_prompt(all_used_emojis, max_emojis=50)
        
        all_resolved_mappings = []
        collisions_to_process = list(collisions)  # Copy so we can modify it
        
        while collisions_to_process:
            # Take a batch of collisions
            batch_size = min(collision_size, len(collisions_to_process))
            collision_batch = collisions_to_process[:batch_size]
            collisions_to_process = collisions_to_process[batch_size:]
            
            logger.info(f"🔧 Resolving collision batch: {len(collision_batch)} conflicts (remaining: {len(collisions_to_process)})")
            
            # Resolve this batch with multi-pass support
            batch_resolved_mappings, new_collisions = self._resolve_collision_batch(
                collision_batch, existing_sample_text, num_passes=num_passes
            )
            all_resolved_mappings.extend(batch_resolved_mappings)
            
            # If LLM created new collisions, add them back to the processing queue
            if new_collisions:
                logger.info(f"⚠️  Adding {len(new_collisions)} new collision pairs back to queue")
                collisions_to_process.extend(new_collisions)
        
        logger.info(f"✅ Successfully resolved {len(collisions)} total collisions into {len(all_resolved_mappings)} mappings")
        return all_resolved_mappings
    
    def _resolve_collision_batch(self, 
                               collision_batch: List[Tuple[str, str, str]], 
                               existing_sample_text: str,
                               num_passes: int = 1) -> Tuple[List[NewMapping], List[Tuple[str, str, str]]]:
        """Resolve a single batch of collisions with optional multi-pass support
        
        Args:
            collision_batch: List of collision tuples to resolve
            existing_sample_text: Sample of existing emojis to avoid
            num_passes: Number of passes for collision resolution (1 for single pass, >1 for multi-pass)
        """
        
        # Format collisions for prompt
        collisions_text = self.collision_manager.format_collisions_for_prompt(collision_batch)
        
        # Get all words involved in collisions for usage context
        collision_words = list(self.collision_manager.get_collision_words(collision_batch))
        
        # Generate word usage context for better collision resolution decisions
        word_usage_context = self._generate_word_usage_context(collision_words)
        
        # Create collision resolution prompt with usage context
        prompt = COLLISION_RESOLUTION_PROMPT_TEMPLATE.format(
            collisions_text=collisions_text,
            existing_emojis=existing_sample_text,
            word_usage_context=word_usage_context
        )
        
        # Collision resolution prompt prepared
        
        if num_passes == 1:
            # Single pass collision resolution (original behavior)
            logger.info(f"🔧 Resolving {len(collision_batch)} emoji collisions with LLM...")
            return self._resolve_collision_batch_single_pass(prompt, collision_batch)
        else:
            # Multi-pass collision resolution (new behavior)
            logger.info(f"🔧 Resolving {len(collision_batch)} emoji collisions with multi-pass LLM ({num_passes} passes)...")
            return self._resolve_collision_batch_multi_pass(prompt, collision_batch, num_passes)
    
    def _resolve_collision_batch_single_pass(self, prompt: str, collision_batch: List[Tuple[str, str, str]]) -> Tuple[List[NewMapping], List[Tuple[str, str, str]]]:
        """Original single-pass collision resolution"""
        # Make LLM call using the new method that returns match scores
        word_mappings_with_scores = self.llm_client.call_llm_for_word_mappings_with_scores(prompt, temperature=0.8, max_tokens=100000)
        
        if word_mappings_with_scores is None:
            logger.error("Failed to get collision resolution from LLM")
            return [], []
        
        # Convert to the format expected by the processing function
        word_mappings = {}
        for mapping_data in word_mappings_with_scores:
            word = mapping_data.get('word')
            emoji = mapping_data.get('emoji_combo')
            match_score = mapping_data.get('match_score', 0.0)
            
            if word and emoji:
                word_mappings[word] = emoji
                logger.debug(f"Collision resolution mapping: '{word}' -> '{emoji}' (LLM score: {match_score:.2f})")
        
        # Log the collision resolution results
        collision_words = self.collision_manager.get_collision_words(collision_batch)
        logger.info(f"✅ COLLISION RESOLUTION SUCCESSFUL:")
        logger.info(f"   📝 Expected words: {sorted(collision_words)}")
        logger.info(f"   📥 Received mappings: {word_mappings}")
        logger.info(f"   📊 Mapped {len(word_mappings)}/{len(collision_words)} collision words")
        
        # Process the collision resolution response using the unified format
        resolved_mappings = self._process_collision_resolution_response_unified(
            word_mappings, collision_batch
        )
        
        return self._finalize_collision_resolution(resolved_mappings, collision_batch)
    
    def _resolve_collision_batch_multi_pass(self, prompt: str, collision_batch: List[Tuple[str, str, str]], num_passes: int) -> Tuple[List[NewMapping], List[Tuple[str, str, str]]]:
        """Multi-pass collision resolution using collective scoring of complete response sets"""
        collision_words = self.collision_manager.get_collision_words(collision_batch)
        
        # Collect complete response sets from multiple passes
        response_sets = []
        
        for pass_num in range(num_passes):
            logger.info(f"  🔄 Collision resolution pass {pass_num + 1}/{num_passes} for {len(collision_words)} words")
            
            # Adjust temperature for diversity across passes
            temperature = 0.75 + (pass_num * 0.1)  # Slightly increase creativity in later passes
            
            # Make LLM call
            word_mappings_with_scores = self.llm_client.call_llm_for_word_mappings_with_scores(
                prompt, temperature=temperature, max_tokens=100000
            )
            
            if word_mappings_with_scores:
                # Create a complete response set for this pass
                response_set = {
                    'pass': pass_num + 1,
                    'mappings': {},
                    'scores': {},
                    'temperature': temperature
                }
                
                for mapping_data in word_mappings_with_scores:
                    word = mapping_data.get('word')
                    emoji = mapping_data.get('emoji_combo')
                    match_score = mapping_data.get('match_score', 0.0)
                    
                    if word and emoji and word in collision_words:
                        response_set['mappings'][word] = emoji
                        response_set['scores'][word] = match_score
                        logger.debug(f"Collision pass {pass_num + 1}: '{word}' -> '{emoji}' (score: {match_score:.2f})")
                
                # Only add complete response sets that have mappings for all collision words
                if len(response_set['mappings']) == len(collision_words):
                    response_sets.append(response_set)
                    logger.info(f"  ✅ Pass {pass_num + 1}: Complete response set with {len(response_set['mappings'])} mappings")
                else:
                    logger.warning(f"  ⚠️  Pass {pass_num + 1}: Incomplete response set ({len(response_set['mappings'])}/{len(collision_words)} words), skipping")
        
        if not response_sets:
            logger.error("❌ No complete response sets collected across all passes")
            return [], []
        
        # Score each complete response set using collective scoring
        scored_sets = []
        for response_set in response_sets:
            collective_score = self._score_collision_response_set(response_set, collision_words)
            scored_sets.append((response_set, collective_score))
            
            logger.info(f"  📊 Pass {response_set['pass']} collective score: {collective_score:.3f}")
        
        # Select the best complete response set
        scored_sets.sort(key=lambda x: x[1], reverse=True)  # Sort by collective score (higher is better)
        best_response_set, best_score = scored_sets[0]
        
        logger.info(f"✅ Selected response set from pass {best_response_set['pass']} with collective score {best_score:.3f}")
        
        # Use the best response set as our final mappings
        best_word_mappings = best_response_set['mappings']
        
        # Log the collision resolution results
        logger.info(f"✅ MULTI-PASS COLLISION RESOLUTION COMPLETE:")
        logger.info(f"   📝 Expected words: {sorted(collision_words)}")
        logger.info(f"   📥 Received mappings: {best_word_mappings}")
        logger.info(f"   📊 Mapped {len(best_word_mappings)}/{len(collision_words)} collision words")
        logger.info(f"   🏆 Winning pass: {best_response_set['pass']} (collective score: {best_score:.3f})")
        
        # Process the collision resolution response using the unified format
        resolved_mappings = self._process_collision_resolution_response_unified(
            best_word_mappings, collision_batch
        )
        
        return self._finalize_collision_resolution(resolved_mappings, collision_batch)
    
    def _score_collision_response_set(self, response_set: Dict, collision_words: List[str]) -> float:
        """Score a complete collision response set using collective metrics
        
        Args:
            response_set: Dict containing 'mappings', 'scores', 'pass', 'temperature'
            collision_words: List of words that need collision resolution
            
        Returns:
            Collective score for the entire response set (higher is better)
        """
        mappings = response_set['mappings']
        individual_scores = response_set['scores']
        
        if not mappings or len(mappings) != len(collision_words):
            return 0.0
        
        # Factor 1: Average LLM confidence scores (70% weight)
        avg_llm_score = sum(individual_scores.values()) / len(individual_scores)
        
        # Factor 2: Uniqueness within the set (20% weight)
        emojis = list(mappings.values())
        unique_emojis = set(emojis)
        uniqueness_score = len(unique_emojis) / len(emojis)  # 1.0 if all unique, lower if duplicates
        
        # Factor 3: Completeness bonus (10% weight)
        completeness_score = 1.0 if len(mappings) == len(collision_words) else 0.0
        
        # Calculate weighted collective score
        collective_score = (
            avg_llm_score * 0.7 +
            uniqueness_score * 0.2 +
            completeness_score * 0.1
        )
        
        logger.debug(f"Response set scoring - LLM avg: {avg_llm_score:.3f}, uniqueness: {uniqueness_score:.3f}, completeness: {completeness_score:.3f}, collective: {collective_score:.3f}")
        
        return collective_score
    
    def _finalize_collision_resolution(self, resolved_mappings: List[NewMapping], collision_batch: List[Tuple[str, str, str]]) -> Tuple[List[NewMapping], List[Tuple[str, str, str]]]:
        """Common finalization logic for both single-pass and multi-pass collision resolution"""
        # Track newly generated emojis in session
        for mapping in resolved_mappings:
            if mapping.suggested_emojis:
                self.collision_manager.track_emoji_usage(mapping.suggested_emojis)
        
        # Validate that all collision words got mappings and check for new collisions
        collision_words = self.collision_manager.get_collision_words(collision_batch)
        resolved_words = set(m.word for m in resolved_mappings)
        missing_words = list(collision_words - resolved_words)
        
        # Check for new collisions created by LLM
        clean_mappings, new_collision_tuples = self.collision_manager.validate_collision_resolution(resolved_mappings)
        
        # Handle missing words by creating retry collision tuples
        if missing_words:
            logger.warning(f"⚠️  LLM collision resolution is missing {len(missing_words)} words: {missing_words}")
            missing_collision_tuples = self.collision_manager.create_collision_tuples_from_missing_words(missing_words)
            new_collision_tuples.extend(missing_collision_tuples)
        
        if new_collision_tuples:
            logger.warning(f"⚠️  Found {len(new_collision_tuples)} collision pairs (including missing words), will retry in next batch")
        
        # Log final collision resolution summary
        logger.info(f"🔧 COLLISION BATCH COMPLETE:")
        logger.info(f"   ✅ Resolved mappings: {len(clean_mappings)}")
        logger.info(f"   🔄 New collision pairs: {len(new_collision_tuples)}")
        if clean_mappings:
            logger.info(f"   📝 Successfully resolved: {[m.word + ' → ' + m.suggested_emojis for m in clean_mappings]}")
        
        return clean_mappings, new_collision_tuples
    
    def _process_collision_resolution_response_unified(self, 
                                                     word_mappings: Dict[str, str], 
                                                     collision_batch: List[Tuple[str, str, str]]) -> List[NewMapping]:
        """Process word-to-emoji mappings from collision resolution into NewMapping objects (unified format)"""
        resolved_mappings = []
        collision_words = self.collision_manager.get_collision_words(collision_batch)
        
        # Process each word-emoji mapping
        for word, emoji in word_mappings.items():
            # Only include words that were part of the collision
            if word in collision_words and emoji:
                # Determine category based on whether this word got the original disputed emoji
                category = self._determine_collision_category(word, emoji, collision_batch)
                
                resolved_mappings.append(NewMapping(
                    word=word,
                    suggested_emojis=emoji,
                    category=category
                ))
        
        return resolved_mappings
    
    
    def _determine_collision_category(self, 
                                    word: str, 
                                    emoji: str, 
                                    collision_batch: List[Tuple[str, str, str]]) -> str:
        """Determine the appropriate category for a resolved collision mapping"""
        for word1, word2, disputed_emoji in collision_batch:
            if word in [word1, word2]:
                if disputed_emoji == RETRY_EMOJI_MARKER:
                    return 'collision_retry'
                elif emoji != disputed_emoji:
                    return 'collision_alternative'
                else:
                    return 'collision_winner'
        return 'collision_winner'  # Default
    
    def handle_emoji_collisions(self, 
                              batch_mappings: List[NewMapping], 
                              collision_size: int = DEFAULT_COLLISION_BATCH_SIZE,
                              num_passes: int = 1) -> Tuple[List[NewMapping], List[str]]:
        """Check for emoji collisions and use LLM to resolve them intelligently
        
        Args:
            batch_mappings: Mappings to check for collisions
            collision_size: Batch size for collision resolution
            num_passes: Number of passes for collision resolution (1 for single pass, >1 for multi-pass)
        """
        existing_emojis = self.file_manager.get_existing_emojis()
        emoji_to_word = self.file_manager.get_emoji_to_word_mapping()
        
        accepted_mappings, collisions_to_resolve = self.collision_manager.detect_collisions_in_batch(
            batch_mappings, existing_emojis, emoji_to_word
        )
        
        # If there are collisions, resolve them with LLM (with multi-pass support)
        if collisions_to_resolve:
            if num_passes > 1:
                logger.info(f"🔧 Found {len(collisions_to_resolve)} collisions, resolving with multi-pass LLM ({num_passes} passes)...")
            else:
                logger.info(f"🔧 Found {len(collisions_to_resolve)} collisions, resolving with LLM...")
                
            resolved_mappings = self._resolve_collisions_with_multipass_support(
                collisions_to_resolve, collision_size, num_passes
            )
            
            # Separate successful mappings from error mappings that need re-queuing
            successful_mappings = [m for m in resolved_mappings if m.suggested_emojis]
            error_mappings = [m for m in resolved_mappings if not m.suggested_emojis]
            
            accepted_mappings.extend(successful_mappings)
            words_to_requeue = [m.word for m in error_mappings]
        else:
            words_to_requeue = []
        
        logger.info(f"Collision handling complete: {len(accepted_mappings)} accepted, {len(collisions_to_resolve)} resolved, {len(words_to_requeue)} to re-queue")
        return accepted_mappings, words_to_requeue
    
    def _resolve_collisions_with_multipass_support(self, 
                                                 collisions: List[Tuple[str, str, str]], 
                                                 collision_size: int, 
                                                 num_passes: int) -> List[NewMapping]:
        """Resolve emoji collisions with multi-pass support"""
        if not collisions:
            return []
        
        # Get existing emojis to avoid new conflicts
        existing_emojis = self.file_manager.get_existing_emojis()
        all_used_emojis = self.collision_manager.get_all_used_emojis(existing_emojis)
        existing_sample_text = format_existing_emojis_for_collision_prompt(all_used_emojis, max_emojis=50)
        
        all_resolved_mappings = []
        collisions_to_process = list(collisions)  # Copy so we can modify it
        
        while collisions_to_process:
            # Take a batch of collisions
            batch_size = min(collision_size, len(collisions_to_process))
            collision_batch = collisions_to_process[:batch_size]
            collisions_to_process = collisions_to_process[batch_size:]
            
            logger.info(f"🔧 Resolving collision batch: {len(collision_batch)} conflicts (remaining: {len(collisions_to_process)})")
            
            # Resolve this batch with multi-pass support
            batch_resolved_mappings, new_collisions = self._resolve_collision_batch(
                collision_batch, existing_sample_text, num_passes=num_passes
            )
            all_resolved_mappings.extend(batch_resolved_mappings)
            
            # If LLM created new collisions, add them back to the processing queue
            if new_collisions:
                logger.info(f"⚠️  Adding {len(new_collisions)} new collision pairs back to queue")
                collisions_to_process.extend(new_collisions)
        
        logger.info(f"✅ Successfully resolved {len(collisions)} total collisions into {len(all_resolved_mappings)} mappings")
        return all_resolved_mappings
    
    def _generate_word_usage_context(self, words: List[str]) -> str:
        """
        Generate word usage context for collision resolution prompts.
        This provides the LLM with word variants and usage examples to make better decisions.
        
        Args:
            words: List of words to generate usage context for
            
        Returns:
            Formatted string containing usage context for each word
        """
        if not words:
            return "(No words provided)"
        
        usage_lines = []
        
        for word in words:
            # Get word variants using the existing method
            word_variants = self._get_word_variants(word)
            
            if word_variants:
                # Format as: word: variant1, variant2, variant3
                variants_text = ', '.join(word_variants[:6])  # Limit to 6 variants to keep prompt manageable
                usage_lines.append(f"- {word}: {variants_text}")
            else:
                # Show base form if no variants found
                usage_lines.append(f"- {word}: (base form)")
        
        if not usage_lines:
            return "(No usage context available)"
        
        return '\n'.join(usage_lines)
    
    def _normalize_dictionary_words(self, dictionary_words: List[str]) -> List[str]:
        """Normalize dictionary words and remove duplicates.
        
        Args:
            dictionary_words: Raw list of words from dictionary
            
        Returns:
            List of normalized, deduplicated words
        """
        if not dictionary_words:
            return []
            
        logger.info(f"Normalizing {len(dictionary_words)} dictionary words...")
        normalized_words = []
        normalization_stats = {'changed': 0, 'unchanged': 0, 'duplicates_removed': 0}
        seen_normalized = set()
        
        for word in dictionary_words:
            normalized_word = self.normalizer.normalize_word(word)
            
            if normalized_word != word:
                normalization_stats['changed'] += 1
                logger.debug(f"Normalized: {word} -> {normalized_word}")
            else:
                normalization_stats['unchanged'] += 1
            
            # Avoid duplicate normalized words
            if normalized_word not in seen_normalized:
                normalized_words.append(normalized_word)
                seen_normalized.add(normalized_word)
            else:
                normalization_stats['duplicates_removed'] += 1
                logger.debug(f"Duplicate normalized word removed: {word} -> {normalized_word} (already exists)")
        
        logger.info(f"Normalization complete: {normalization_stats['changed']} changed, "
                   f"{normalization_stats['unchanged']} unchanged, "
                   f"{normalization_stats['duplicates_removed']} duplicates removed")
        logger.info(f"Processing {len(normalized_words)} normalized words (reduced from {len(dictionary_words)})")
        
        return normalized_words
    
    def _add_words_to_queue(self, words_to_add: List[str], target_queue: List[str]) -> None:
        """Add words to processing queue, avoiding duplicates.
        
        Args:
            words_to_add: Words to add to the queue
            target_queue: The queue to add words to (modified in place)
        """
        for word in words_to_add:
            if word not in target_queue:
                target_queue.append(word)
    
    def generate_dictionary_mappings(self,
                                   mapping_size: int = DEFAULT_MAPPING_BATCH_SIZE, 
                                   collision_size: int = DEFAULT_COLLISION_BATCH_SIZE, 
                                   dictionary_path: str = "documents/dictionary.txt",
                                   collision_passes: int = 1) -> List[NewMapping]:
        """Generate mappings for all words in dictionary using batch processing with collision handling
        
        Args:
            mapping_size: Batch size for word generation
            collision_size: Batch size for collision resolution
            dictionary_path: Path to dictionary file
            collision_passes: Number of LLM passes for collision resolution
        """
        logger.info(f"Reading words from {dictionary_path}...")
        
        # Load and normalize dictionary words
        raw_words = self.file_manager.load_dictionary(dictionary_path)
        dictionary_words = self._normalize_dictionary_words(raw_words)

        # Handle existing duplicate emoji conflicts first
        words_with_duplicate_emojis, duplicate_collision_tuples = self.file_manager.find_and_remove_duplicate_emojis()        # Filter out words that already have mappings, but add back the duplicate-emoji words
        words_to_process = self.file_manager.filter_unmapped_words(dictionary_words)
        for word in words_with_duplicate_emojis:
            if word not in words_to_process:
                words_to_process.append(word)
        
        if not words_to_process and not duplicate_collision_tuples:
            logger.info("All dictionary words already have mappings!")
            return []
        
        all_mappings = []
        
        # First, resolve any duplicate emoji collisions found in existing mappings
        if duplicate_collision_tuples:
            all_mappings.extend(self._resolve_duplicate_collisions(
                duplicate_collision_tuples, collision_size, words_to_process
            ))
        
        # Process remaining words until all are complete (handles collision re-queuing)
        all_mappings.extend(self._process_words_with_collision_handling(
            words_to_process, mapping_size, collision_size
        ))
        
        logger.info(f"Completed generation of {len(all_mappings)} mappings")
        return all_mappings
    
    def generate_dictionary_mappings_multipass(self, 
                                             mapping_size: int = DEFAULT_MAPPING_BATCH_SIZE, 
                                             collision_size: int = DEFAULT_COLLISION_BATCH_SIZE, 
                                             dictionary_path: str = "documents/dictionary.txt",
                                             num_passes: int = 3,
                                             collision_passes: int = None) -> List[NewMapping]:
        """
        Generate dictionary mappings using multi-pass generation for higher quality.
        
        Args:
            mapping_size: Batch size for generation
            collision_size: Batch size for collision resolution  
            dictionary_path: Path to dictionary file
            num_passes: Number of LLM passes for consensus building
            collision_passes: Number of LLM passes for collision resolution (defaults to num_passes)
        """
        # Set default collision passes if not specified
        if collision_passes is None:
            collision_passes = num_passes
        
        logger.info(f"🧠 Starting MULTI-PASS dictionary mapping generation from {dictionary_path}")
        logger.info(f"📊 Using {num_passes} passes for consensus building")
        logger.info(f"🔧 Using {collision_passes} passes for collision resolution")
        
        # Load and normalize dictionary words using shared method
        raw_words = self.file_manager.load_dictionary(dictionary_path)
        
        if not raw_words:
            logger.warning(f"No words found in dictionary: {dictionary_path}")
            return []
        
        logger.info(f"Loaded {len(raw_words)} words from {dictionary_path}")
        
        # Use shared normalization method
        normalized_words = self._normalize_dictionary_words(raw_words)
        
        # Filter unmapped words
        words_to_process = self.file_manager.filter_unmapped_words(normalized_words)
        
        if not words_to_process:
            logger.info("All dictionary words already have mappings!")
            return []
        
        logger.info(f"🎯 Processing {len(words_to_process)} unmapped words with multi-pass generation")
        
        # Process words using the same collision-handling pattern as regular generation
        all_mappings = []
        
        while words_to_process:
            logger.info(f"Processing {len(words_to_process)} remaining words with multi-pass generation...")
            
            # Process in batches
            total_batches = (len(words_to_process) + mapping_size - 1) // mapping_size
            
            for batch_num in range(total_batches):
                start_idx = batch_num * mapping_size
                end_idx = min(start_idx + mapping_size, len(words_to_process))
                batch_words = words_to_process[start_idx:end_idx]
                
                logger.info(f"📝 Processing multipass batch {batch_num + 1}/{total_batches} ({len(batch_words)} words)")
                
                # Process this batch using multipass generation
                batch_mappings, processed_words, collision_words = self._process_single_multipass_batch(
                    batch_words, num_passes, collision_size, collision_passes
                )
                
                all_mappings.extend(batch_mappings)
                
                # Update words_to_process: remove processed words, add collision words to front
                words_to_process = [w for w in words_to_process if w not in processed_words]
                if collision_words:
                    logger.info(f"🔄 Re-queuing {len(collision_words)} words due to collisions: {collision_words}")
                    words_to_process = collision_words + words_to_process
                
                logger.info(f"Multipass batch {batch_num + 1} complete ({len(all_mappings)} total mappings, {len(words_to_process)} remaining)")
                
                # Break out of batch loop if we have collision words to reprocess
                if collision_words:
                    break
        
        logger.info(f"✅ Multi-pass dictionary generation complete: {len(all_mappings)} mappings")
        return all_mappings
    
    def _process_single_multipass_batch(self, 
                                      batch_words: List[str], 
                                      num_passes: int,
                                      collision_size: int,
                                      collision_passes: int = None) -> Tuple[List[NewMapping], set, List[str]]:
        """Process a single batch of words using multipass generation and return mappings, processed words, and collision words
        
        Args:
            batch_words: Words to process in this batch
            num_passes: Number of passes for word generation
            collision_size: Batch size for collision resolution
            collision_passes: Number of passes for collision resolution (defaults to num_passes)
        """
        # Generate mappings for this batch using multipass generation
        batch_mappings = self.generate_mappings_multipass(batch_words, num_passes)
        
        # Separate successful and failed mappings
        successful_mappings = [m for m in batch_mappings if m.suggested_emojis]
        failed_mappings = [m for m in batch_mappings if not m.suggested_emojis]
        
        if failed_mappings:
            logger.warning(f"⚠️  {len(failed_mappings)} words failed multipass generation: {[m.word for m in failed_mappings]}")
        
        # Set default collision passes if not specified
        if collision_passes is None:
            collision_passes = num_passes
        
        # Check for emoji collisions and handle them (using collision passes)
        accepted_mappings, collision_words = self.handle_emoji_collisions(
            successful_mappings, collision_size=collision_size, num_passes=collision_passes
        )
        
        # Add failed mapping words to collision_words for re-queuing
        failed_words = [m.word for m in failed_mappings]
        collision_words.extend(failed_words)
        
        # Save accepted mappings to disk and check for save-time collisions
        save_collision_words = []
        if accepted_mappings:
            save_collision_words = self._save_mappings_to_file(accepted_mappings)
            logger.info(f"💾 Auto-saved {len(accepted_mappings)} mappings from multipass batch")
            
            # BUGFIX: Immediately resolve save-time collisions if any are found
            if save_collision_words:
                logger.warning(f"⚠️ Found {len(save_collision_words)} save-time collisions, resolving immediately...")
                # The save collision words actually represent real emoji conflicts that were detected during save
                # We need to create proper collision tuples, not treat them as missing words
                # Get the collision information from the save process
                save_collision_tuples = self._create_save_collision_tuples(save_collision_words, accepted_mappings)
                
                if save_collision_tuples:
                    logger.info(f"🔧 Created {len(save_collision_tuples)} collision tuples for save-time conflicts")
                    # Use dedicated collision resolution (NOT multipass generation) for these conflicts
                    resolved_save_mappings = self.resolve_emoji_collisions_with_llm(
                        save_collision_tuples, collision_size=collision_size, num_passes=collision_passes
                    )
                    
                    # Save these resolved mappings
                    successful_save_mappings = [m for m in resolved_save_mappings if m.suggested_emojis]
                    if successful_save_mappings:
                        # Try to save again - this might create more collisions, but those will be handled in the next batch
                        recursive_save_collisions = self._save_mappings_to_file(successful_save_mappings)
                        logger.info(f"✅ Recursively resolved and saved {len(successful_save_mappings)} save-time collisions")
                        if recursive_save_collisions:
                            logger.warning(f"⚠️ Still have {len(recursive_save_collisions)} unresolved save-time collisions after recursive resolution")
                            # CRITICAL FIX: Don't re-queue persistent save collision words for normal generation
                            # This prevents infinite loops where the same collision keeps happening
                            logger.error(f"🚨 PERSISTENT SAVE COLLISIONS: {recursive_save_collisions} - these words will be skipped to prevent infinite loops")
                            logger.error("These words may need manual review or different emoji assignments")
                            save_collision_words = []  # Clear to prevent infinite re-queuing
                        else:
                            # All save-time collisions resolved successfully
                            save_collision_words = []
                            
                        # Add the successful save-time resolution mappings to our accepted mappings
                        accepted_mappings.extend(successful_save_mappings)
                else:
                    logger.warning("⚠️ Unable to create proper collision tuples for save-time collisions, skipping to prevent loops")
                    # Clear collision words to prevent infinite re-queuing
                    save_collision_words = []
        
        # Combine collision words from processing and saving
        all_collision_words = collision_words + save_collision_words
        
        # Track which words were processed in this batch
        processed_words = {m.word for m in batch_mappings}
        
        return accepted_mappings, processed_words, all_collision_words
    
    def _resolve_duplicate_collisions(self,
                                    duplicate_collision_tuples: List[Tuple[str, str, str]], 
                                    collision_size: int, 
                                    words_to_process: List[str]) -> List[NewMapping]:
        """Resolve duplicate emoji collisions found in existing mappings"""
        logger.info(f"🔧 Resolving {len(duplicate_collision_tuples)} duplicate emoji collisions first...")
        resolved_duplicate_mappings = self.resolve_emoji_collisions_with_llm(
            duplicate_collision_tuples, collision_size=collision_size
        )
        
        # Save the resolved duplicate mappings
        if resolved_duplicate_mappings:
            successful_duplicate_mappings = [m for m in resolved_duplicate_mappings if m.suggested_emojis]
            if successful_duplicate_mappings:
                save_collision_words = self._save_mappings_to_file(successful_duplicate_mappings)
                logger.info(f"✅ Resolved {len(successful_duplicate_mappings)} duplicate emoji collisions")
                
                # Handle any new collisions found during save
                if save_collision_words:
                    logger.warning(f"⚠️ {len(save_collision_words)} words from duplicate resolution created new collisions during save")
                    self._add_words_to_queue(save_collision_words, words_to_process)
            
            # Handle any words that still failed resolution
            failed_duplicate_words = [m.word for m in resolved_duplicate_mappings if not m.suggested_emojis]
            if failed_duplicate_words:
                logger.warning(f"⚠️ {len(failed_duplicate_words)} words from duplicate resolution still need processing: {failed_duplicate_words}")
                # Add them to the main processing queue
                self._add_words_to_queue(failed_duplicate_words, words_to_process)
            
            return successful_duplicate_mappings
        
        return []
    
    def _process_words_with_collision_handling(self, 
                                             words_to_process: List[str], 
                                             mapping_size: int, 
                                             collision_size: int) -> List[NewMapping]:
        """Process words in batches with collision handling and re-queuing"""
        all_mappings = []
        
        while words_to_process:
            logger.info(f"Processing {len(words_to_process)} remaining words...")
            
            # Process in batches
            total_batches = (len(words_to_process) + mapping_size - 1) // mapping_size
            
            for batch_num in range(total_batches):
                start_idx = batch_num * mapping_size
                end_idx = min(start_idx + mapping_size, len(words_to_process))
                batch_words = words_to_process[start_idx:end_idx]
                
                logger.info(f"Processing batch {batch_num + 1}/{total_batches} ({len(batch_words)} words)")
                
                # Process this batch
                batch_mappings, processed_words, collision_words = self._process_single_batch(
                    batch_words, collision_size
                )
                
                all_mappings.extend(batch_mappings)
                
                # Update words_to_process: remove processed words, add collision words to front
                words_to_process = [w for w in words_to_process if w not in processed_words]
                if collision_words:
                    logger.info(f"Re-queuing {len(collision_words)} words due to collisions: {collision_words}")
                    words_to_process = collision_words + words_to_process
                
                logger.info(f"Batch {batch_num + 1} complete ({len(all_mappings)} total mappings, {len(words_to_process)} remaining)")
                
                # Break out of batch loop if we have collision words to reprocess
                if collision_words:
                    break
        
        return all_mappings
    
    def _process_single_batch(self, 
                            batch_words: List[str], 
                            collision_size: int,
                            num_passes: int = 1) -> Tuple[List[NewMapping], set, List[str]]:
        """Process a single batch of words and return mappings, processed words, and collision words
        
        Args:
            batch_words: Words to process in this batch
            collision_size: Batch size for collision resolution
            num_passes: Number of passes for both batch generation and collision resolution
        """
        # Generate mappings for this batch (with multi-pass support)
        batch_mappings = self.generate_mappings_batch(batch_words, num_passes=num_passes)
        
        # Separate successful mappings from failed ones
        successful_mappings = [m for m in batch_mappings if m.suggested_emojis]
        failed_mappings = [m for m in batch_mappings if not m.suggested_emojis]
        
        if failed_mappings:
            logger.warning(f"⚠️  {len(failed_mappings)} words failed to get emojis from batch generation: {[m.word for m in failed_mappings]}")
        
        # Check for emoji collisions and handle them (with multi-pass support)
        accepted_mappings, collision_words = self.handle_emoji_collisions(
            successful_mappings, collision_size=collision_size, num_passes=num_passes
        )
        
        # Add failed mapping words to collision_words for re-queuing
        failed_words = [m.word for m in failed_mappings]
        collision_words.extend(failed_words)
        
        # Save accepted mappings to disk and check for save-time collisions
        save_collision_words = []
        if accepted_mappings:
            save_collision_words = self._save_mappings_to_file(accepted_mappings)
            logger.info(f"💾 Auto-saved {len(accepted_mappings)} mappings from current batch")
            
            # BUGFIX: Immediately resolve save-time collisions if any are found
            if save_collision_words:
                logger.warning(f"⚠️ Found {len(save_collision_words)} save-time collisions, resolving immediately...")
                # The save collision words actually represent real emoji conflicts that were detected during save
                # We need to create proper collision tuples, not treat them as missing words
                # Get the collision information from the save process
                save_collision_tuples = self._create_save_collision_tuples(save_collision_words, accepted_mappings)
                
                if save_collision_tuples:
                    logger.info(f"🔧 Created {len(save_collision_tuples)} collision tuples for save-time conflicts")
                    # Use dedicated collision resolution (NOT multipass generation) for these conflicts
                    resolved_save_mappings = self.resolve_emoji_collisions_with_llm(
                        save_collision_tuples, collision_size=collision_size, num_passes=collision_passes
                    )
                    
                    # Save these resolved mappings
                    successful_save_mappings = [m for m in resolved_save_mappings if m.suggested_emojis]
                    if successful_save_mappings:
                        # Try to save again - this might create more collisions, but those will be handled in the next batch
                        recursive_save_collisions = self._save_mappings_to_file(successful_save_mappings)
                        logger.info(f"✅ Recursively resolved and saved {len(successful_save_mappings)} save-time collisions")
                        if recursive_save_collisions:
                            logger.warning(f"⚠️ Still have {len(recursive_save_collisions)} unresolved save-time collisions after recursive resolution")
                            # CRITICAL FIX: Don't re-queue persistent save collision words for normal generation
                            # This prevents infinite loops where the same collision keeps happening
                            logger.error(f"🚨 PERSISTENT SAVE COLLISIONS: {recursive_save_collisions} - these words will be skipped to prevent infinite loops")
                            logger.error("These words may need manual review or different emoji assignments")
                            save_collision_words = []  # Clear to prevent infinite re-queuing
                        else:
                            # All save-time collisions resolved successfully
                            save_collision_words = []
                            
                        # Add the successful save-time resolution mappings to our accepted mappings
                        accepted_mappings.extend(successful_save_mappings)
                else:
                    logger.warning("⚠️ Unable to create proper collision tuples for save-time collisions, skipping to prevent loops")
                    # Clear collision words to prevent infinite re-queuing
                    save_collision_words = []
        
        # Combine collision words from processing and saving
        all_collision_words = collision_words + save_collision_words
        
        # Track which words were processed in this batch
        processed_words = {m.word for m in batch_mappings}
        
        return accepted_mappings, processed_words, all_collision_words
    
    def _create_save_collision_tuples(self, save_collision_words: List[str], accepted_mappings: List[NewMapping]) -> List[Tuple[str, str, str]]:
        """
        Create proper collision tuples for save-time collisions.
        
        Save-time collisions occur when a new mapping conflicts with an existing mapping.
        We use the stored collision info from the save process to create proper tuples.
        
        Args:
            save_collision_words: Words that had collisions during save (both new and existing words)
            accepted_mappings: The mappings that were trying to be saved
            
        Returns:
            List of collision tuples representing the actual emoji conflicts
        """
        collision_tuples = []
        
        # Check if we have stored collision info from the save process
        if hasattr(self, '_last_save_collision_info') and self._last_save_collision_info:
            logger.info(f"Using stored collision info from save process: {len(self._last_save_collision_info)} collisions")
            
            for collision_info in self._last_save_collision_info:
                new_word = collision_info['new_word']
                existing_word = collision_info['existing_word']
                emoji = collision_info['emoji']
                
                # Skip if it's the same word (should not happen but extra protection)
                if new_word != existing_word:
                    logger.debug(f"Save collision: '{new_word}' wants '{emoji}' but '{existing_word}' already uses it")
                    collision_tuples.append((new_word, existing_word, emoji))
                else:
                    logger.debug(f"Skipping same-word collision tuple: '{new_word}' vs '{existing_word}' for '{emoji}' (duplicate)")
            
            # Clear the collision info after use
            self._last_save_collision_info = None
            
        else:
            # Fallback to old method if no stored collision info
            logger.warning("No stored collision info, falling back to reconstruction method")
            
            # Load current mappings to find the conflicts
            existing_mappings = self.file_manager.load_existing_mappings()
            
            # Create a map from word to emoji for the accepted mappings that were trying to be saved
            new_word_to_emoji = {mapping.word: mapping.suggested_emojis for mapping in accepted_mappings if mapping.suggested_emojis}
            
            # Group collision words by the emoji they're fighting over
            emoji_conflicts = {}
            
            for collision_word in save_collision_words:
                # Check if this is a new word that was trying to be saved
                if collision_word in new_word_to_emoji:
                    conflicted_emoji = new_word_to_emoji[collision_word]
                    if conflicted_emoji not in emoji_conflicts:
                        emoji_conflicts[conflicted_emoji] = {'new_words': [], 'existing_words': []}
                    emoji_conflicts[conflicted_emoji]['new_words'].append(collision_word)
                    logger.debug(f"New word '{collision_word}' was trying to use '{conflicted_emoji}'")
                
                # Check if this is an existing word that already uses an emoji
                elif collision_word in existing_mappings:
                    existing_emoji = existing_mappings[collision_word]
                    if existing_emoji not in emoji_conflicts:
                        emoji_conflicts[existing_emoji] = {'new_words': [], 'existing_words': []}
                    emoji_conflicts[existing_emoji]['existing_words'].append(collision_word)
                    logger.debug(f"Existing word '{collision_word}' already uses '{existing_emoji}'")
                else:
                    logger.warning(f"Collision word '{collision_word}' not found in new mappings or existing mappings")
            
            # Create collision tuples from the emoji conflicts
            for emoji, conflict_info in emoji_conflicts.items():
                new_words = conflict_info['new_words']
                existing_words = conflict_info['existing_words']
                
                # Each new word that wants this emoji conflicts with each existing word that has it
                for new_word in new_words:
                    for existing_word in existing_words:
                        # Skip if it's the same word (should not happen but extra protection)
                        if new_word != existing_word:
                            logger.debug(f"Save collision identified: '{new_word}' wants '{emoji}' but '{existing_word}' already uses it")
                            collision_tuples.append((new_word, existing_word, emoji))
                        else:
                            logger.debug(f"Skipping same-word fallback collision tuple: '{new_word}' vs '{existing_word}' for '{emoji}' (duplicate)")
        
        logger.info(f"Created {len(collision_tuples)} collision tuples from {len(save_collision_words)} save collision words")
        return collision_tuples
    
    def _save_mappings_to_file(self, mappings: List[NewMapping]) -> List[str]:
        """
        Save mappings to the main mapping file with collision validation
        
        Returns:
            List of words that had emoji collisions and need to be re-resolved
        """
        # Load existing mappings
        existing_mappings = self.file_manager.load_existing_mappings()
        
        # Create reverse mapping to detect collisions
        existing_emoji_to_word = {emoji: word for word, emoji in existing_mappings.items()}
        
        # First, remove any existing mappings for words that are being updated in this batch
        # This prevents false collision detection when words are getting new mappings
        words_being_updated = {mapping.word for mapping in mappings if mapping.suggested_emojis}
        for word in words_being_updated:
            if word in existing_mappings:
                old_emoji = existing_mappings[word]
                # Remove the old mapping
                existing_mappings.pop(word, None)
                # Remove from reverse mapping if this was the only word using that emoji
                if old_emoji in existing_emoji_to_word and existing_emoji_to_word[old_emoji] == word:
                    existing_emoji_to_word.pop(old_emoji, None)
        
        # Validate new mappings and detect collisions
        validated_mappings = []
        collision_words = []
        collision_info = []  # Store collision details for better tuple creation
        
        for mapping in mappings:
            if not mapping.suggested_emojis:
                continue
                
            # Check if this emoji is already used by a different word (not in current batch)
            if mapping.suggested_emojis in existing_emoji_to_word:
                existing_word = existing_emoji_to_word[mapping.suggested_emojis]
                # Only treat as collision if it's a DIFFERENT word using the same emoji
                if existing_word != mapping.word and existing_word not in words_being_updated:
                    logger.warning(f"🚨 SAVE COLLISION DETECTED: '{mapping.word}' wants '{mapping.suggested_emojis}' but it's already used by '{existing_word}'")
                    collision_words.append(mapping.word)
                    collision_words.append(existing_word)
                    # Store collision info for tuple creation
                    collision_info.append({
                        'new_word': mapping.word,
                        'existing_word': existing_word, 
                        'emoji': mapping.suggested_emojis
                    })
                    # Don't remove the existing mapping here - we need it for collision resolution
                    continue
                elif existing_word == mapping.word:
                    # Same word trying to use the same emoji it already has - this is fine, just skip
                    logger.debug(f"Skipping duplicate mapping: '{mapping.word}' -> '{mapping.suggested_emojis}' (already exists)")
                    continue
            
            # No collision, add the mapping
            logger.info(f"Adding mapping: {mapping.word} -> {mapping.suggested_emojis}")
            existing_mappings[mapping.word] = mapping.suggested_emojis
            existing_emoji_to_word[mapping.suggested_emojis] = mapping.word
            validated_mappings.append(mapping)
        
        # Save updated mappings
        self.file_manager.save_mappings(existing_mappings)
        
        if collision_words:
            unique_collision_words = list(set(collision_words))
            logger.warning(f"⚠️  Found {len(unique_collision_words)} words with save-time collisions, will re-queue for resolution: {unique_collision_words}")
            # Store collision info for the tuple creation method
            self._last_save_collision_info = collision_info
            return unique_collision_words
        
        return []
    
    def save_mappings(self, mappings: List[NewMapping], filename: Optional[str] = None) -> Path:
        """Save generated mappings to logs and update main mapping file"""
        # Save to logs directory for analysis
        log_path = self.file_manager.save_generation_log(mappings, filename)
        
        # Also save to main mapping file and check for final collisions
        final_collision_words = self._save_mappings_to_file(mappings)
        if final_collision_words:
            logger.error(f"🚨 FINAL SAVE COLLISIONS: {len(final_collision_words)} words still have collisions after processing: {final_collision_words}")
            logger.error("These words may need manual review or re-processing")
        
        return log_path
    
    
    def create_generation_report(self, mappings: List[NewMapping]) -> str:
        """Create a generation report using the utility function"""
        return create_generation_report(mappings)
    
    def analyze_mappings(self, mappings: List[NewMapping]) -> Dict:
        """Analyze mappings using the utility function"""
        return analyze_mappings(mappings)
