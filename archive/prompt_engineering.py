# Intelligent Prompt Engineering for Word-to-Emoji Mapping
# ✅ Develops sophisticated prompts that guide LLM to consider word meaning, context, and usage
# ✅ Suggests primary emoji with visual/conceptual representation 
# ✅ Provides fallback emoji combinations when single emoji insufficient
# ✅ Explains reasoning behind each mapping for validation
# ✅ Avoids arbitrary or confusing associations

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import re

class WordType(Enum):
    """Categories of words for specialized prompt handling"""
    CONCRETE_NOUN = "concrete_noun"          # cat, car, book
    ABSTRACT_NOUN = "abstract_noun"          # love, freedom, concept
    ACTION_VERB = "action_verb"              # run, jump, eat
    STATE_VERB = "state_verb"                # be, seem, exist
    DESCRIPTIVE_ADJECTIVE = "descriptive_adj" # red, big, soft
    EMOTIONAL_ADJECTIVE = "emotional_adj"     # happy, sad, angry
    ADVERB = "adverb"                        # quickly, carefully
    PREPOSITION = "preposition"              # in, on, under
    PRONOUN = "pronoun"                      # he, she, it
    CONJUNCTION = "conjunction"              # and, but, or
    INTERJECTION = "interjection"            # wow, ouch, hello
    TECHNICAL_TERM = "technical_term"        # algorithm, database
    COLLOQUIAL = "colloquial"               # gonna, wanna, ain't

@dataclass 
class EmojiMappingContext:
    """Context information for intelligent emoji mapping"""
    word: str
    word_type: WordType
    definition: str
    usage_examples: List[str]
    semantic_field: str  # e.g., "animals", "emotions", "technology"
    frequency_score: float  # how common the word is (0-1)
    ambiguity_level: str  # "low", "medium", "high"
    cultural_sensitivity: bool  # whether word has cultural implications

class PromptEngineeringSystem:
    """
    Sophisticated prompt engineering system for intelligent word-to-emoji mapping.
    Generates context-aware prompts that guide LLMs to create semantically meaningful mappings.
    """
    
    def __init__(self):
        self.base_system_prompt = self._create_base_system_prompt()
        self.word_type_strategies = self._initialize_word_type_strategies()
        self.reasoning_templates = self._create_reasoning_templates()
        
    def _create_base_system_prompt(self) -> str:
        """Create the foundational system prompt for emoji mapping"""
        return """You are an expert semantic linguist and emoji mapping specialist. Your task is to create intuitive, semantically meaningful mappings between English words and emoji representations.

CORE PRINCIPLES:
1. SEMANTIC ALIGNMENT: Choose emojis that truly represent the word's core meaning, not superficial associations
2. VISUAL CONCEPTUALIZATION: Consider how the word's concept would be visually represented
3. CONTEXTUAL APPROPRIATENESS: Account for common usage patterns and contexts
4. COGNITIVE LOAD: Prefer simple, immediately recognizable mappings over complex ones
5. CULTURAL UNIVERSALITY: Choose emojis that work across different cultural contexts when possible
6. SYSTEMATIC CONSISTENCY: Apply consistent logic across similar word types

MAPPING HIERARCHY:
1st Priority: Direct semantic match (cat → 🐱)
2nd Priority: Conceptual representation (idea → 💡) 
3rd Priority: Functional association (key → 🗝️)
4th Priority: Metaphorical connection (growth → 🌱)

COMBINATION STRATEGY:
- Use single emoji when it clearly represents the concept
- Use 2-emoji combinations when single emoji is insufficient or ambiguous
- Avoid 3+ emoji combinations unless absolutely necessary
- Ensure combinations are intuitive and not arbitrary

QUALITY VALIDATION:
For each mapping, you must provide clear reasoning explaining:
- Why this emoji/combination was chosen
- How it relates to the word semantically
- What alternatives were considered and rejected
- Potential ambiguity or confusion risks"""

    def _initialize_word_type_strategies(self) -> Dict[WordType, str]:
        """Define specialized prompt strategies for different word types"""
        return {
            WordType.CONCRETE_NOUN: """
CONCRETE NOUN STRATEGY:
- Look for direct emoji representations of the physical object
- Consider the object's most distinctive visual features
- If no direct match, use emojis representing the object's primary function
- For animals/plants: Use specific species emoji when available
- For objects: Consider shape, use, or category associations
Example reasoning: "chair" → 🪑 (direct visual representation of seating furniture)
""",
            
            WordType.ABSTRACT_NOUN: """  
ABSTRACT NOUN STRATEGY:
- Identify concrete symbols or metaphors that represent the concept
- Consider cultural symbols and universal representations
- Look for emoji that evoke the emotional or conceptual essence
- Use combination when single emoji cannot capture complexity
- Avoid overly literal or reductive mappings
Example reasoning: "freedom" → 🕊️ (dove universally symbolizes freedom and peace)
""",
            
            WordType.ACTION_VERB: """
ACTION VERB STRATEGY:
- Prioritize emojis showing the action being performed
- Consider the typical actor/subject performing the action
- Look for motion-indicating emojis or gesture representations
- Use person+action combinations when clearer than action alone
- Consider the action's end result or associated objects
Example reasoning: "running" → 🏃 (person in running pose shows the action clearly)
""",
            
            WordType.STATE_VERB: """
STATE VERB STRATEGY:
- Focus on the condition or state being described rather than action
- Use symbols that represent the resulting state or condition
- Consider metaphorical representations of states
- Use combinations to show state transitions when relevant
- Avoid action-based emojis for state verbs
Example reasoning: "existing" → ✨ (sparkle suggests presence and being)
""",
            
            WordType.DESCRIPTIVE_ADJECTIVE: """
DESCRIPTIVE ADJECTIVE STRATEGY:
- Choose emojis that embody the quality being described
- Consider objects or concepts that exemplify this quality
- Use color-related emojis for color adjectives
- For size/shape: use objects known for that characteristic
- Combine multiple emojis if quality has multiple dimensions
Example reasoning: "bright" → ☀️ (sun embodies brightness visually and conceptually)
""",
            
            WordType.EMOTIONAL_ADJECTIVE: """
EMOTIONAL ADJECTIVE STRATEGY:
- Use facial expressions that directly show the emotion
- Consider body language emojis that convey the feeling
- Look for symbols that culturally represent the emotion
- Use heart variations for love-related emotions
- Avoid ambiguous expressions that could convey multiple emotions
Example reasoning: "joyful" → 😊 (smiling face directly expresses joy and happiness)
""",
            
            WordType.TECHNICAL_TERM: """
TECHNICAL TERM STRATEGY:
- Look for emojis representing the technical domain
- Use computer/technology emojis for digital concepts
- Consider the tool or object associated with the technical field
- Use combinations to specify technical sub-domains
- Avoid overly generic tech symbols when specific ones exist
Example reasoning: "algorithm" → 🔄⚙️ (process flow + mechanism suggests systematic procedure)
""",
            
            WordType.ADVERB: """
ADVERB STRATEGY:
- Focus on the manner, speed, or intensity being modified
- Use movement or direction indicators for manner adverbs
- Consider combining action symbols with intensity indicators
- For time adverbs: use clock or time-related symbols
- Use arrow or directional emojis for spatial/directional adverbs
Example reasoning: "quickly" → ⚡ (lightning bolt suggests speed and rapid action)
""",
            
            WordType.PREPOSITION: """
PREPOSITION STRATEGY:
- Use spatial relationship indicators and arrows
- Consider the physical relationship being described
- Use directional emojis for movement prepositions
- Combine position indicators with reference objects when helpful
- Focus on the geometric or spatial concept
Example reasoning: "above" → ⬆️ (upward arrow indicates higher position relationship)
"""
        }

    def _create_reasoning_templates(self) -> Dict[str, str]:
        """Templates for structured reasoning explanations"""
        return {
            "semantic_connection": "🔗 SEMANTIC: This emoji connects to '{word}' because {explanation}",
            "visual_representation": "👁️ VISUAL: The emoji visually represents {word} by {explanation}",
            "conceptual_metaphor": "🧠 CONCEPTUAL: This represents the abstract concept of {word} through {explanation}", 
            "functional_association": "⚙️ FUNCTIONAL: This emoji represents {word} through its primary function: {explanation}",
            "cultural_symbol": "🌍 CULTURAL: This emoji is a widely recognized symbol for {word} because {explanation}",
            "combination_rationale": "🔗 COMBINATION: Multiple emojis needed because {explanation}",
            "alternative_considered": "🤔 ALTERNATIVE: Considered {alternative} but chose {chosen} because {reason}",
            "ambiguity_warning": "⚠️ AMBIGUITY: Potential confusion with {other_meaning}, mitigated by {solution}",
            "fallback_explanation": "🔄 FALLBACK: Primary option unavailable, this {explanation}"
        }

    def generate_word_analysis_prompt(self, word: str, context: Optional[EmojiMappingContext] = None) -> str:
        """Generate comprehensive analysis prompt for a word"""
        
        analysis_prompt = f"""
WORD ANALYSIS REQUEST: "{word}"

Please analyze this word across multiple dimensions before suggesting emoji mappings:

1. SEMANTIC ANALYSIS:
   - Core meaning and definition
   - Semantic field (category/domain)
   - Level of concreteness (concrete ↔ abstract)
   - Frequency of use (common ↔ rare)

2. CONTEXTUAL ANALYSIS:
   - Typical usage contexts
   - Common collocations and phrases
   - Formality level (informal ↔ formal)
   - Cultural or regional variations

3. CONCEPTUAL MAPPING:
   - Visual imagery associated with the word
   - Metaphorical representations
   - Symbolic associations
   - Emotional connotations

4. DISAMBIGUATION:
   - Multiple meanings or homonyms
   - Potential confusion with similar words
   - Contextual clues needed for clarity

Provide this analysis first, then proceed with emoji mapping suggestions."""

        if context:
            analysis_prompt += f"""

ADDITIONAL CONTEXT PROVIDED:
- Definition: {context.definition}
- Semantic field: {context.semantic_field}
- Usage examples: {', '.join(context.usage_examples[:3])}
- Ambiguity level: {context.ambiguity_level}
"""
        
        return analysis_prompt

    def generate_mapping_prompt(self, word: str, word_type: WordType, 
                              context: Optional[EmojiMappingContext] = None) -> str:
        """Generate specialized mapping prompt based on word type and context"""
        
        # Get base system prompt
        system_context = self.base_system_prompt
        
        # Add word-type specific strategy
        if word_type in self.word_type_strategies:
            system_context += "\n\n" + self.word_type_strategies[word_type]
        
        # Build the specific mapping request
        mapping_prompt = f"""
EMOJI MAPPING REQUEST: "{word}" ({word_type.value})

INSTRUCTIONS:
1. Apply the relevant word type strategy above
2. Consider the word's meaning, context, and common usage
3. Suggest your PRIMARY emoji choice with full reasoning
4. Provide 2-3 ALTERNATIVE options with brief explanations
5. If single emoji insufficient, provide COMBINATION suggestions
6. Explain your reasoning using the structured format below

REQUIRED RESPONSE FORMAT:

PRIMARY MAPPING:
Word: {word}
Emoji: [your primary choice]
Type: [single/combination]
Reasoning: [Use reasoning templates - semantic connection, visual representation, etc.]

ALTERNATIVES:
1. Emoji: [alternative 1] | Reasoning: [brief explanation]
2. Emoji: [alternative 2] | Reasoning: [brief explanation] 
3. Emoji: [alternative 3] | Reasoning: [brief explanation]

FALLBACK COMBINATIONS (if needed):
- [emoji combo 1]: [reasoning]
- [emoji combo 2]: [reasoning]

VALIDATION CHECKS:
- Ambiguity risk: [low/medium/high] - [explanation]
- Cultural sensitivity: [appropriate/needs caution] - [explanation]
- Intuitive rating: [1-5] - [explanation]
- Alternative meanings: [list any other possible interpretations]

FINAL RECOMMENDATION: [State your strongest recommendation and why]
"""

        # Add context-specific guidance if available
        if context:
            context_guidance = f"""
CONTEXTUAL GUIDANCE:
- Focus on the "{context.semantic_field}" domain
- Consider frequency: {"common" if context.frequency_score > 0.7 else "less common"} word
- Ambiguity level: {context.ambiguity_level}
- Cultural considerations: {"important" if context.cultural_sensitivity else "minimal"}
"""
            mapping_prompt = context_guidance + "\n" + mapping_prompt

        return system_context + "\n" + mapping_prompt

    def generate_batch_mapping_prompt(self, words: List[str], 
                                    shared_context: str = "") -> str:
        """Generate prompt for batch processing multiple related words"""
        
        word_list = ", ".join(words)
        
        batch_prompt = f"""
BATCH EMOJI MAPPING REQUEST
Words: {word_list}
Shared Context: {shared_context}

BATCH PROCESSING INSTRUCTIONS:
1. Identify relationships and patterns between words
2. Ensure consistent mapping logic across similar words  
3. Avoid emoji reuse - each word needs unique emoji/combination
4. Consider the full set when making individual choices
5. Maintain semantic coherence across the batch

For each word, provide:
- Word: [word]
- Emoji: [mapping]
- Reasoning: [brief explanation]
- Batch notes: [how it relates to other words in the set]

CONSISTENCY CHECKS:
- Are similar words mapped with consistent logic?
- Do any mappings conflict or create confusion?
- Is the overall batch semantically coherent?

RESPONSE FORMAT:
[Process each word with the format above, then provide batch analysis]

BATCH ANALYSIS:
- Consistency rating: [1-5]
- Potential conflicts: [list any issues]
- Overall coherence: [assessment]
"""
        
        return self.base_system_prompt + "\n\n" + batch_prompt

    def generate_validation_prompt(self, word: str, mappingsping: str, 
                                 reasoning: str) -> str:
        """Generate prompt for validating existing mappings"""
        
        validation_prompt = f"""
MAPPING VALIDATION REQUEST

Word: "{word}"
Proposed Emoji: {mappingsping}  
Original Reasoning: {reasoning}

VALIDATION CRITERIA:
1. SEMANTIC ACCURACY: Does the emoji truly represent the word's meaning?
2. VISUAL CLARITY: Is the connection immediately apparent to users?
3. CULTURAL UNIVERSALITY: Will this work across different cultural contexts?
4. DISAMBIGUATION: Can this be confused with other word mappings?
5. COGNITIVE LOAD: How much mental effort to understand the connection?

VALIDATION TASKS:
1. Rate each criterion (1-5 scale, 5 = excellent)
2. Identify potential issues or improvements
3. Suggest alternative mappings if current one is problematic
4. Provide overall recommendation (approve/revise/reject)

RESPONSE FORMAT:
VALIDATION SCORES:
- Semantic Accuracy: [1-5] - [explanation]
- Visual Clarity: [1-5] - [explanation]  
- Cultural Universality: [1-5] - [explanation]
- Disambiguation: [1-5] - [explanation]
- Cognitive Load: [1-5] - [explanation]

ISSUES IDENTIFIED:
- [List any problems or concerns]

IMPROVEMENT SUGGESTIONS:
- [List specific recommendations]

ALTERNATIVE MAPPINGS:
- [Suggest 1-2 alternatives if needed]

FINAL RECOMMENDATION: [Approve/Revise/Reject] - [Summary reasoning]
OVERALL QUALITY SCORE: [Average of criteria scores]
"""
        
        return validation_prompt

    def generate_conflict_resolution_prompt(self, conflicts: List[Tuple[str, str, str]]) -> str:
        """Generate prompt for resolving emoji mapping conflicts"""
        
        conflict_descriptions = []
        for i, (word1, word2, shared_emoji) in enumerate(conflicts, 1):
            conflict_descriptions.append(f"{i}. '{word1}' and '{word2}' both mapped to: {shared_emoji}")
        
        conflicts_text = "\n".join(conflict_descriptions)
        
        resolution_prompt = f"""
EMOJI MAPPING CONFLICT RESOLUTION

The following emoji mappings have conflicts (same emoji used for multiple words):

{conflicts_text}

RESOLUTION STRATEGY:
1. Identify which word has the strongest semantic claim to each emoji
2. Find alternative mappings for words that lose their original emoji
3. Ensure new mappings maintain semantic quality
4. Prevent new conflicts from arising

For each conflict, provide:

CONFLICT [number]: {shared_emoji}
Primary claimant: [word with strongest semantic connection] - [reasoning]
Alternative for other word: [new emoji] - [reasoning] 
Confidence: [high/medium/low] - [explanation]

RESOLUTION SUMMARY:
- Total conflicts resolved: [number]
- New mappings created: [number]  
- Quality maintained: [assessment]
- Potential new issues: [any warnings]
"""
        
        return self.base_system_prompt + "\n\n" + resolution_prompt

    def generate_domain_specific_prompt(self, domain: str, words: List[str]) -> str:
        """Generate prompts specialized for specific semantic domains"""
        
        domain_strategies = {
            "emotions": "Focus on facial expressions, heart variations, and universally understood emotional symbols",
            "animals": "Use specific species emoji when available, consider animal behavior and characteristics",
            "technology": "Leverage computer, phone, and digital symbols; use combinations for complex tech concepts",
            "food": "Use specific food emoji, consider preparation methods and cultural food associations",
            "transportation": "Use vehicle emoji, consider mode of transport and associated concepts",
            "nature": "Use weather, plant, and natural phenomenon emoji; consider seasonal associations",
            "body_parts": "Use anatomical emoji when available, consider body system relationships",
            "colors": "Use objects strongly associated with colors, consider color psychology",
            "time": "Use clock, calendar, and temporal symbols; consider duration vs. specific time",
            "space": "Use celestial bodies, direction indicators, and spatial relationship symbols"
        }
        
        strategy = domain_strategies.get(domain, "Use standard semantic mapping principles")
        word_list = ", ".join(words)
        
        domain_prompt = f"""
DOMAIN-SPECIFIC EMOJI MAPPING

Domain: {domain.upper()}
Words: {word_list}
Specialized Strategy: {strategy}

DOMAIN CONSIDERATIONS:
1. What emoji are specifically available in this domain?
2. Are there domain-specific conventions or expectations?
3. How do words in this domain typically relate to each other?
4. What are the most distinctive features of concepts in this domain?

MAPPING APPROACH:
- Apply domain expertise to choose the most appropriate emoji
- Consider relationships between concepts within the domain
- Use domain-specific symbols and conventions
- Maintain consistency with domain expectations

For each word, consider:
- Domain-specific meaning and usage
- Relationship to other words in the domain
- Most distinctive characteristics within this domain
- Available emoji that best represents the concept

Proceed with mapping each word using domain-specialized reasoning.
"""
        
        return self.base_system_prompt + "\n\n" + domain_prompt

    def export_prompts_to_json(self) -> Dict:
        """Export all prompt templates and strategies to JSON for easy access"""
        
        return {
            "base_system_prompt": self.base_system_prompt,
            "word_type_strategies": {wt.value: strategy for wt, strategy in self.word_type_strategies.items()},
            "reasoning_templates": self.reasoning_templates,
            "prompt_types": {
                "word_analysis": "Comprehensive analysis before mapping",
                "specialized_mapping": "Word-type specific mapping with reasoning", 
                "batch_processing": "Multiple related words with consistency",
                "validation": "Quality assessment of existing mappings",
                "conflict_resolution": "Resolve emoji reuse conflicts",
                "domain_specific": "Specialized for semantic domains"
            }
        }

# Example usage and testing
if __name__ == "__main__":
    # Initialize the prompt engineering system
    prompt_system = PromptEngineeringSystem()
    
    # Example 1: Generate analysis prompt
    print("=== WORD ANALYSIS PROMPT ===")
    analysis_prompt = prompt_system.generate_word_analysis_prompt("serendipity")
    print(analysis_prompt[:500] + "...")
    
    print("\n=== SPECIALIZED MAPPING PROMPT ===")
    # Example 2: Generate specialized mapping prompt
    mapping_prompt = prompt_system.generate_mapping_prompt("happiness", WordType.EMOTIONAL_ADJECTIVE)
    print(mapping_prompt[:500] + "...")
    
    print("\n=== BATCH PROCESSING PROMPT ===") 
    # Example 3: Generate batch processing prompt
    batch_prompt = prompt_system.generate_batch_mapping_prompt(
        ["cat", "dog", "bird", "fish"], "domestic animals"
    )
    print(batch_prompt[:500] + "...")
    
    print("\n=== VALIDATION PROMPT ===")
    # Example 4: Generate validation prompt
    validation_prompt = prompt_system.generate_validation_prompt(
        "computer", "💻", "Direct visual representation of computing device"
    )
    print(validation_prompt[:500] + "...")
    
    # Export prompts to JSON
    prompts_export = prompt_system.export_prompts_to_json()
    with open("prompt_templates.json", "w") as f:
        json.dump(prompts_export, f, indent=2)
    
    print(f"\n=== EXPORTED PROMPTS ===")
    print(f"Exported {len(prompts_export)} prompt categories to prompt_templates.json")
