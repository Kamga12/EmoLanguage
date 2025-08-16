# Preserved Derivations List

## Overview
This document lists word transformations that must be preserved in the simplified emoji mapping system due to their distinct semantic meanings and cultural importance.

## Preservation Criteria

### 1. Semantic Distinction
- Derived word has significantly different meaning from base word
- Cannot be inferred from context alone
- Represents a distinct concept or category

### 2. Cultural/Professional Importance  
- Professional titles and specialized roles
- Cultural concepts and social structures
- Technical terminology with specific meanings

### 3. Emotional/Intensity Variations
- Words expressing different emotional intensities
- Opposite meanings (positive/negative pairs)
- Gradations of meaning that affect interpretation

## Categories of Preserved Derivations

### A. ABSTRACT NOUNS - Concept Transformations (1,415 preserved)

#### Philosophy & Ideas
```
real → reality (adjective vs abstract concept)
human → humanity (individual vs collective concept)
solid → solidarity (physical property vs social bond)
individual → individuality (person vs philosophical concept)
moral → morality (adjective vs ethical system)
personal → personality (adjective vs character traits)
```

#### States & Conditions
```
possible → possibility (potential vs specific opportunity)
probable → probability (likely vs statistical measure)
necessary → necessity (required vs essential need)
responsible → responsibility (adjective vs duty)
available → availability (accessible vs state of access)
```

#### Qualities & Measurements
```
dense → density (thick vs measurable property)
intense → intensity (strong vs degree of strength)
popular → popularity (well-liked vs social standing)
secure → security (safe vs protection system)
pure → purity (clean vs state of cleanliness)
```

### B. ADJECTIVE FORMS - Meaningful Variations (1,385 preserved)

#### Opposite Meaning Pairs
```
use → useful vs useless (positive/negative meaning)
hope → hopeful vs hopeless (optimism/pessimism)
care → careful vs careless (cautious/reckless)
harm → harmful vs harmless (dangerous/safe)
rest → restful vs restless (calm/agitated)
```

#### Professional/Technical Distinctions
```
medicine → medicinal vs medical (therapeutic vs field of study)
economy → economic vs economical (relating to economics vs cost-effective)
history → historic vs historical (significant vs relating to history)
strategy → strategic vs strategical (planned vs relating to strategy)
```

#### Capability/Potential Distinctions  
```
read → readable (able to be read)
believe → believable (credible)
achieve → achievable (attainable)
question → questionable (doubtful)
reason → reasonable (logical)
```

### C. SPECIALIZED AGENT NOUNS - Professional Roles (404 preserved)

#### Medical & Healthcare
```
medicine → doctor (👨‍⚕️), nurse (👩‍⚕️), surgeon, therapist
psychology → psychologist, psychiatrist
```

#### Education & Research
```
teach → teacher (👨‍🏫), professor, instructor
research → researcher, scientist (👨‍🔬)
study → student (👨‍🎓)
```

#### Creative & Technical Professions  
```
art → artist (👨‍🎨), painter, sculptor
write → writer (✍️), author, journalist
engineer → engineer (👨‍💻), architect (👨‍💼)
```

#### Legal & Government
```
law → lawyer (👨‍⚖️), judge, attorney  
govern → governor, politician
manage → manager (👨‍💼), director, supervisor
```

### D. COMPOUND CONCEPTS - Multi-word Meanings

#### Social & Institutional
```
school → schooling (education process)
church → churchgoing (religious practice)
government → governing (act of ruling)
community → communion (spiritual connection)
```

#### Process & Activity
```
develop → development (process of growing)
manage → management (act of controlling)
organize → organization (structured group)
create → creation (act of making)
```

## Elimination Exceptions

### DO NOT ELIMINATE these patterns:

#### 1. Irregular Transformations
- `good → better → best` (completely different forms)
- `go → went → gone` (irregular verbs) 
- `person → people` (irregular plurals)

#### 2. Emotionally Distinct Words
- `anger → angry → angrily` (noun vs adjective vs adverb - different contexts)
- `beauty → beautiful → beautifully` (concept vs quality vs manner)

#### 3. Scientific/Technical Precision
- `chemistry → chemical → chemist` (field vs property vs profession)
- `physics → physical → physicist` (science vs adjective vs professional)

#### 4. Cultural/Religious Significance
- `spirit → spiritual → spirituality` (entity vs quality vs belief system)
- `religion → religious → religiosity` (institution vs quality vs devotion)

## Implementation Guidelines

### For Word_Normalizer Integration:

#### 1. Semantic Check Function
```python
def is_semantically_distinct(base_word: str, derived_word: str) -> bool:
    # Check against preserved derivations list
    # Use semantic distance measurement
    # Consider cultural/professional importance
```

#### 2. Professional Title Preservation
```python
PRESERVED_PROFESSIONS = {
    'doctor', 'lawyer', 'teacher', 'engineer', 'scientist',
    'artist', 'writer', 'manager', 'director', 'professor'
}
```

#### 3. Concept Distinction Rules
```python
ABSTRACT_CONCEPTS = {
    'reality', 'humanity', 'personality', 'morality', 
    'possibility', 'responsibility', 'security', 'density'
}
```

## Quality Assurance

### Validation Tests:
1. **Semantic Roundtrip Test**: Encode→Decode preserves meaning 95%+ accuracy
2. **Professional Context Test**: Career/technical terms maintain precision
3. **Emotional Distinction Test**: Positive/negative pairs remain distinct
4. **Cultural Sensitivity Test**: Important cultural concepts preserved

### Monitoring Metrics:
- **Preservation Rate**: 2,204/5,291 derivations (42% preserved)
- **Semantic Accuracy**: Target >95%
- **User Satisfaction**: Target >90% comprehension
- **System Performance**: <10% increase in processing time

## Usage in Updated System

The preserved derivations will be:
1. **Flagged** in Word_Normalizer as non-normalizable
2. **Maintained** in emoji mappings with distinct emojis
3. **Validated** during encoding/decoding processes  
4. **Documented** for user reference and system maintenance

This preservation list ensures the simplified system maintains semantic richness while eliminating purely grammatical variations.
