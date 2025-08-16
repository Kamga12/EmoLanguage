# EmoLanguage Prompting Strategy

This document outlines the comprehensive prompting strategies used across the EmoLanguage project for consistent and effective LLM interactions.

## Overview

The EmoLanguage system relies on Large Language Models (LLMs) for two primary tasks:
1. **Semantic Mapping Generation** - Creating new word-to-emoji mappings from scratch
2. **Duplicate Resolution** - Resolving conflicts where multiple words map to the same emoji

Both tasks require sophisticated prompting strategies to ensure semantic accuracy, cultural universality, and system consistency.

## Core Prompting Principles

### 1. Expert Persona Establishment
All prompts begin by establishing the LLM as an expert in semantic analysis and emoji communication:
```
You are an expert in semantic analysis and emoji communication.
```

This primes the model to approach tasks with the appropriate domain knowledge and professional methodology.

### 2. Multi-Emoji Assignment Strategy
The system prioritizes semantic accuracy through flexible emoji assignment:

- **Single Emoji Preferred**: Use one emoji when it adequately represents the concept
- **Multi-Emoji Combinations**: Use 2-3 emojis only when necessary for semantic clarity
- **Maximum Limit**: Never exceed 3 emojis per word to maintain readability

**Priority Hierarchy:**
1. Single emoji with direct semantic connection
2. Single emoji with clear conceptual relationship  
3. Two-emoji combination for compound concepts
4. Three-emoji combination only for complex abstract concepts

### 3. Semantic Accuracy Requirements

#### Primary Criteria
- **Clear semantic connection** between word meaning and emoji representation
- **Universal recognizability** across cultures and demographics
- **Encoding/decoding efficiency** for practical communication
- **Visual clarity** and memorability

#### Semantic Mapping Examples
- **Direct representation**: "cat" → 🐱
- **Conceptual relationship**: "kitten" → 🐾 (related to cats but distinct)
- **Action representation**: "run" → 🏃
- **Emotional mapping**: "happy" → 😊
- **Abstract concepts**: "friendship" → 👥❤️ (people + love)
- **Compound concepts**: "birthday" → 🎂🎉 (cake + celebration)

### 4. Cultural Universality Guidelines

#### Preferred Emoji Categories
- **Universal objects**: 🌍 🏠 🚗 📱
- **Common emotions**: 😊 😢 😍 😤  
- **Basic actions**: 🏃 🚶 👋 👏
- **Natural elements**: 🌞 🌙 ⭐ 🌊
- **Food items**: 🍎 🍞 🍕 🥛

#### Avoided Emoji Categories
- **Culture-specific foods**: Regional cuisines without global recognition
- **Religious symbols**: May not be universally appropriate
- **Complex gestures**: Hand signals with varying cultural meanings
- **Country flags**: Unless specifically needed for geographic reference

## Prompt Structure Templates

### 1. Semantic Mapping Generation Template

```
You are an expert in semantic analysis and emoji communication. Please generate the best possible emoji mapping for this word:

WORD: "{word}"

Please provide:

1. SUGGESTED_EMOJIS: The best emoji(s) to represent this word that:
   - Have clear semantic connection to the word's meaning
   - Are universally recognizable and culturally appropriate
   - Work well for encoding/decoding text
   - Are as simple as possible while being clear
   - Use 1-3 emojis maximum (prefer the fewest emojis possible)

2. CATEGORY: Classify the word into one of these categories:
   - "common" (pronouns, articles, prepositions, frequent words)
   - "action" (verbs, movement, activities)
   - "object" (nouns for physical things)
   - "abstract" (concepts, emotions, ideas)
   - "technical" (specialized terms, jargon)

3. REASONING: Explain why this emoji choice is semantically appropriate (1-2 sentences)

4. CONFIDENCE: Rate your confidence in this mapping (0.0-1.0 scale)
```

### 2. Duplicate Resolution Template

```
You are an expert in semantic analysis and emoji communication. You need to resolve a duplicate emoji mapping conflict where multiple words are mapped to the same emoji, breaking the reversibility requirement.

CONFLICT:
- Emoji: {emoji}
- Description: {emoji_description}  
- Conflicting words: {words_list}

IMPORTANT - EXISTING EMOJIS TO AVOID:
These emojis are already used by other words, DO NOT suggest them: {existing_sample_text}

TASK: Resolve this conflict by assigning each word a unique emoji or emoji combination that:
1. Has clear semantic connection to the word's meaning
2. Is universally recognizable and culturally appropriate
3. Works well for encoding/decoding text
4. Uses 1-3 emojis maximum (prefer the fewest emojis possible)
5. Is UNIQUE and doesn't conflict with existing mappings
```

## JSON Response Formatting

### Standard Response Structure
All LLM responses must follow strict JSON formatting for automated processing:

```json
{
    "suggested_emojis": "emoji_string",
    "emoji_description": "human_readable_description", 
    "category": "category_name",
    "reasoning": "explanation_text",
    "confidence": 0.85
}
```

### Batch Processing Format
For multiple words processed simultaneously:

```json
[
    {
        "word": "word1",
        "suggested_emojis": "emoji1",
        "emoji_description": "description1",
        "category": "category1", 
        "reasoning": "reasoning1",
        "confidence": 0.90
    },
    {
        "word": "word2",
        "suggested_emojis": "emoji2emoji3",
        "emoji_description": "description2",
        "category": "category2",
        "reasoning": "reasoning2", 
        "confidence": 0.75
    }
]
```

## Conflict Resolution Strategies

### 1. Semantic Differentiation
When multiple words share an emoji, the system resolves conflicts by:
- **Identifying the most semantically appropriate word** for the original emoji
- **Finding related but distinct emojis** for other words
- **Using semantic categories** to guide differentiation

**Example Resolution:**
- Conflict: "house" and "home" both map to 🏠
- Resolution: "house" → 🏠 (building), "home" → 🏡 (dwelling/family)

### 2. Abstraction Level Management
The system handles different abstraction levels:
- **Concrete concepts**: Direct emoji representation preferred
- **Abstract concepts**: Metaphorical or symbolic representation
- **Compound concepts**: Multi-emoji combinations when needed

### 3. Collision Detection and Prevention
- **Existing mappings awareness**: All prompts include exclusion lists
- **Batch consistency**: Within-batch uniqueness enforcement
- **Recursive resolution**: Automatic handling of secondary conflicts

## Quality Assurance Measures

### 1. Confidence Scoring
- **High confidence (≥0.8)**: Direct, clear semantic mappings
- **Medium confidence (0.5-0.79)**: Reasonable but potentially ambiguous mappings
- **Low confidence (<0.5)**: Difficult mappings requiring review

### 2. Validation Criteria
- **Semantic accuracy**: Clear connection between word and emoji meaning
- **Cultural appropriateness**: Universal understanding across cultures
- **Visual clarity**: Emoji distinctiveness and recognizability
- **System consistency**: Alignment with existing mapping patterns

### 3. Fallback Mechanisms
When LLM assignment fails:
1. **Algorithmic fallback**: Letter-based or hash-based unique assignment
2. **Manual review queuing**: Flagging for human evaluation
3. **Iterative refinement**: Re-prompting with additional context

## Examples and Best Practices

### Single Emoji Assignments
- **"sun"** → ☀️ (direct representation)
- **"car"** → 🚗 (direct representation) 
- **"love"** → ❤️ (universal symbol)
- **"question"** → ❓ (symbolic representation)

### Multi-Emoji Assignments
- **"software"** → 💻⚙️ (computer + gear)
- **"morning"** → 🌅☀️ (sunrise + sun)
- **"birthday"** → 🎂🎉 (cake + celebration)
- **"friendship"** → 👥❤️ (people + love)

### Conflict Resolution Examples
- **Happy/Joy**: "happy" → 😊, "joy" → 🎉
- **Big/Large**: "big" → 🔍➕, "large" → 📏➕  
- **Fast/Quick**: "fast" → ⚡, "quick" → 🏃💨

## Integration Guidelines

### 1. Temperature Settings
- **Semantic mapping**: 0.3 (consistent, focused responses)
- **Conflict resolution**: 0.3 (deterministic solutions)

### 2. Token Limits
- **Single mapping**: 1,000 tokens sufficient
- **Batch processing**: 8,000 tokens for 50+ words
- **Complex conflicts**: 30,000 tokens for detailed resolution

### 3. Error Handling
- **JSON extraction**: Robust parsing with fallback methods
- **Retry mechanisms**: Automatic re-prompting on failure
- **Logging**: Comprehensive tracking of all LLM interactions

## Future Enhancements

### 1. Dynamic Context Awareness
- **Usage frequency integration**: Prioritize common words
- **Domain-specific adaptation**: Specialized prompts for technical domains
- **User feedback incorporation**: Learning from correction patterns

### 2. Advanced Semantic Analysis
- **Synonym cluster recognition**: Coordinated mapping for related terms
- **Polysemy handling**: Context-dependent emoji selection
- **Metaphorical mapping**: Enhanced abstract concept representation

### 3. Cross-Cultural Optimization
- **Regional emoji preferences**: Culture-specific optimization
- **Accessibility considerations**: Support for visual impairments
- **Multilingual consistency**: Coordinated mapping across languages

This prompting strategy ensures consistent, high-quality emoji assignments that maintain semantic accuracy while supporting the scalability and reliability of the EmoLanguage system.
