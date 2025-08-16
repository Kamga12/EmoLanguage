# Transformation Elimination Ruleset

This document defines the specific rules for which word transformations should be eliminated, evaluated on a case-by-case basis, or preserved in natural language processing tasks.

## 1. Always Eliminate

These transformations should be removed without exception as they typically don't change core semantic meaning:

### 1.1 Regular Plurals
- **Pattern**: `-s`, `-es`
- **Examples**: 
  - cats → cat
  - boxes → box
  - dogs → dog
- **Rationale**: Regular plural forms don't add semantic value beyond quantity

### 1.2 Past Tense (Regular)
- **Pattern**: `-ed`
- **Examples**:
  - walked → walk
  - talked → talk
  - played → play
- **Rationale**: Temporal information can be captured elsewhere; core action remains the same

### 1.3 Present Continuous/Progressive
- **Pattern**: `-ing`
- **Examples**:
  - running → run
  - walking → walk
  - thinking → think
- **Rationale**: Aspect information doesn't change the core verb meaning

### 1.4 Third Person Singular Present
- **Pattern**: `-s`
- **Examples**:
  - runs → run
  - walks → walk
  - thinks → think
- **Rationale**: Subject agreement doesn't affect core meaning

## 2. Case-by-Case Evaluation

These transformations require individual assessment based on semantic impact:

### 2.1 Irregular Plurals
- **Decision Criteria**: Keep if semantically distinct from singular
- **Keep Examples**:
  - children (vs child) - different connotations
  - people (vs person) - collective vs individual meaning
  - data (vs datum) - common usage makes plural the standard form
- **Eliminate Examples**:
  - feet (vs foot) - same core concept
  - mice (vs mouse) - same core concept

### 2.2 Adverbs with -ly
- **Decision Criteria**: Keep if meaning changes significantly from adjective form
- **Keep Examples**:
  - hardly (≠ hard) - completely different meaning
  - barely (≠ bare) - semantic shift
  - lately (≠ late) - temporal vs descriptive meaning
- **Eliminate Examples**:
  - quickly (≈ quick) - manner of being quick
  - slowly (≈ slow) - manner of being slow
  - carefully (≈ careful) - manner of being careful

### 2.3 Comparatives and Superlatives
- **Decision Criteria**: Eliminate unless idiomatic or lexicalized
- **Eliminate Examples**:
  - bigger → big
  - fastest → fast
  - smaller → small
- **Keep Examples**:
  - better (≠ good) - lexicalized form
  - best (≠ good) - lexicalized form
  - elder (≠ old) - specialized usage

## 3. Always Preserve

These transformations create semantically distinct words and should never be eliminated:

### 3.1 Opposites/Negation
- **Patterns**: `-less`, `un-`, `non-`, `in-`, `im-`, `ir-`, `il-`, `dis-`, `mis-`
- **Examples**:
  - hopeless (≠ hope)
  - unhappy (≠ happy)
  - nonviolent (≠ violent)
  - incomplete (≠ complete)
  - impossible (≠ possible)
  - irregular (≠ regular)
  - illegal (≠ legal)
  - disagree (≠ agree)
  - misunderstand (≠ understand)
- **Rationale**: These create antonyms or negations with distinct meanings

### 3.2 Role/Agent Transformations
- **Patterns**: `-er`, `-or`, `-ist`, `-ian`, `-ant`, `-ent`
- **Examples**:
  - teacher (≠ teach) - person who teaches vs action
  - actor (≠ act) - person vs action
  - pianist (≠ piano) - person vs instrument
  - librarian (≠ library) - person vs place
  - assistant (≠ assist) - person vs action
  - student (≠ study) - person vs action
- **Rationale**: These indicate roles, professions, or agents performing actions

### 3.3 State/Quality Transformations
- **Patterns**: `-ness`, `-ity`, `-ism`, `-tion`, `-sion`, `-ment`
- **Examples**:
  - happiness (≠ happy) - state vs quality
  - complexity (≠ complex) - abstract concept vs adjective
  - capitalism (≠ capital) - system vs resource
  - creation (≠ create) - result vs action
  - confusion (≠ confuse) - state vs action
  - movement (≠ move) - concept vs action
- **Rationale**: These create abstract nouns representing states, qualities, or concepts

## 4. Implementation Guidelines

### 4.1 Processing Order
1. Apply "Always Preserve" rules first to protect important transformations
2. Apply "Always Eliminate" rules to common inflections
3. Apply "Case-by-Case Evaluation" rules with manual review or contextual analysis

### 4.2 Edge Cases
- **Compound words**: Evaluate each component separately
- **Multiple transformations**: Process from inside out (e.g., "unhappiness" → preserve "un-" and "-ness")
- **Context dependency**: Consider domain-specific meanings
- **Frequency analysis**: High-frequency transformed words may warrant preservation

### 4.3 Quality Assurance
- Maintain exception lists for edge cases
- Regular review of case-by-case decisions
- Domain-specific adjustments as needed
- User feedback integration for ambiguous cases

## 5. Decision Matrix

| Transformation Type | Action | Confidence | Review Required |
|-------------------|--------|------------|-----------------|
| Regular plurals (-s, -es) | Eliminate | High | No |
| Past tense (-ed) | Eliminate | High | No |
| Present continuous (-ing) | Eliminate | High | No |
| 3rd person singular (-s) | Eliminate | High | No |
| Irregular plurals | Evaluate | Medium | Yes |
| -ly adverbs | Evaluate | Medium | Yes |
| Comparatives/superlatives | Evaluate | Medium | Yes |
| Opposites (un-, -less, etc.) | Preserve | High | No |
| Agent/role (-er, -ist) | Preserve | High | No |
| State/quality (-ness, -ity) | Preserve | High | No |

## 6. Practical Application Examples

### 6.1 Sample Processing Pipeline

**Input**: "The teachers were quickly running towards the unhappy children."

**Step 1 - Always Preserve** (identify and protect):
- teachers: -er suffix (role transformation) → PRESERVE
- unhappy: un- prefix (negation) → PRESERVE
- children: irregular plural (semantically distinct) → PRESERVE

**Step 2 - Always Eliminate**:
- were: past tense → eliminate → be
- quickly: -ly adverb (manner only) → eliminate → quick  
- running: -ing present continuous → eliminate → run

**Step 3 - Case-by-Case Evaluation**:
- towards: preposition (no transformation) → keep as-is

**Final Result**: "The teacher be quick run towards the unhappy child."

### 6.2 Domain-Specific Considerations

**Technical/Scientific Domains**:
- Keep technical -tion/-sion words: "optimization", "compression"
- Preserve -ity words for abstract concepts: "scalability", "reliability"

**Business/Legal Domains**:
- Preserve agent words: "contractor", "beneficiary"
- Keep state transformations: "ownership", "liability"

**Creative/Literary Domains**:
- More liberal preservation of -ly adverbs for stylistic nuance
- Keep comparative forms in fixed expressions: "better late than never"

---

**Note**: This ruleset should be applied consistently across all text processing tasks while allowing for domain-specific adjustments where necessary. Regular evaluation and refinement of the case-by-case criteria will improve accuracy over time.
