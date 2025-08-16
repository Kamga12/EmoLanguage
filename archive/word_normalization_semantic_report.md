# Word Normalization Semantic Completeness Test Report
Generated: 2025-08-07 11:06:15

## Executive Summary

- **Rule Compliance Accuracy**: 81.4%
- **Edge Case Handling**: 37.5%
- **Semantic Scenario Accuracy**: 80.0%

**Overall Assessment**: ⚠️ **NEEDS IMPROVEMENT** - Significant semantic completeness issues

## Rule Compliance Analysis

**Overall Accuracy**: 81.4% (35/43)

### Accuracy by Rule Type
- **Always Eliminate**: 92.3% (12/13)
- **Case By Case**: 50.0% (6/12)
- **Always Preserve**: 91.7% (11/12)
- **Special Case**: 100.0% (2/2)
- **Context Dependent**: 100.0% (2/2)
- **Domain Specific**: 100.0% (2/2)

### Accuracy by Semantic Impact Level
- **Low Impact**: 86.4% (19/22)
- **Medium Impact**: 20.0% (1/5)
- **High Impact**: 93.8% (15/16)

### ⚠️ Critical Semantic Errors (High Impact)
- **teach → teacher**: normalized (should preserve)
  *Person who teaches vs action*

## Edge Case Analysis

**Accuracy**: 37.5% (6/16)

### Problematic Edge Cases
- **news**: expected 'news', got 'new'
  *Always plural, no singular form*
- **scissors**: expected 'scissors', got 'scissor'
  *Always plural tool*
- **pants**: expected 'pants', got 'pant'
  *Always plural clothing*
- **glasses**: expected 'glasses', got 'glass'
  *Ambiguous - eyewear vs drinking vessel*
- **better**: expected 'better', got 'good'
  *Lexicalized comparative*
- **best**: expected 'best', got 'good'
  *Lexicalized superlative*
- **worse**: expected 'worse', got 'bad'
  *Lexicalized comparative*
- **worst**: expected 'worst', got 'bad'
  *Lexicalized superlative*
- **analyses**: expected 'analysis', got 'analys'
  *Irregular plural of analysis*
- **hypotheses**: expected 'hypothesis', got 'hypothes'
  *Irregular plural*

## Semantic Preservation Scenarios

**Overall Scenario Accuracy**: 80.0%

### Professional roles should remain distinct from actions
**Accuracy**: 40.0% (2/5)
**Issues found**:
- teach → teacher: normalized to (teach, teach)
- paint → painter: normalized to (paint, paint)
- develop → developer: normalized to (develop, develop)

### Negations should remain distinct from base words
**Accuracy**: 100.0% (5/5)

### Quality abstractions should remain distinct
**Accuracy**: 100.0% (5/5)

### Regular inflections should normalize
**Accuracy**: 80.0% (4/5)
**Issues found**:
- quick → quickly: normalized to (quick, quickly)

## Recommendations

📝 **Review case-by-case decisions** - refine semantic impact assessment
🔍 **Address edge cases** - add special handling for problematic word patterns
🎯 **Improve professional roles should remain distinct from actions** handling

### Priority Actions
1. Fix high semantic impact errors first
2. Review and refine case-by-case evaluation criteria
3. Add special rules for identified edge cases
4. Validate improvements with expanded test coverage