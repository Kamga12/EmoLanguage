#!/usr/bin/env python3
# Integration Script for Semantic Validation
# ✅ Validates existing emoji mappings from the mapping files
# ✅ Identifies weak or problematic mappings
# ✅ Suggests improvements and alternatives
# ✅ Ensures consistency across semantic groups
# ✅ Generates comprehensive reports and recommendations

import os
import json
import argparse
import logging
from typing import Dict, List, Optional
from pathlib import Path

from semantic_validator import SemanticValidator, ValidationStatus, MappingValidation

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MappingValidationIntegration:
    """
    Integration layer for semantic validation with existing emoji mapping system
    """
    
    def __init__(self, mappings_dir: str = "mappings", 
                 llm_base_url: str = "http://127.0.0.1:1234"):
        self.mappings_dir = Path(mappings_dir)
        self.validator = SemanticValidator(llm_base_url)
        
        # Paths to mapping files
        self.word_to_emoji_file = self.mappings_dir / "word_to_emoji.json"
        self.emoji_to_word_file = self.mappings_dir / "emoji_to_word.json"
        self.reasoning_file = self.mappings_dir / "mapping_reasoning.json"
        
    def load_existing_mappings(self) -> Dict[str, str]:
        """Load existing word-to-emoji mappings"""
        if not self.word_to_emoji_file.exists():
            logger.error(f"Mapping file not found: {self.word_to_emoji_file}")
            return {}
            
        try:
            with open(self.word_to_emoji_file, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
            logger.info(f"Loaded {len(mappings)} existing mappings")
            return mappings
        except Exception as e:
            logger.error(f"Failed to load mappings: {e}")
            return {}
    
    def load_mapping_reasoning(self) -> Dict[str, str]:
        """Load existing reasoning for mappings if available"""
        if not self.reasoning_file.exists():
            logger.warning(f"No reasoning file found at {self.reasoning_file}")
            return {}
            
        try:
            with open(self.reasoning_file, 'r', encoding='utf-8') as f:
                reasoning = json.load(f)
            logger.info(f"Loaded reasoning for {len(reasoning)} mappings")
            return reasoning
        except Exception as e:
            logger.warning(f"Failed to load reasoning: {e}")
            return {}
    
    def validate_all_mappings(self) -> Dict[str, MappingValidation]:
        """Validate all existing mappings"""
        logger.info("Starting comprehensive validation of all mappings...")
        
        # Load mappings and reasoning
        mappings = self.load_existing_mappings()
        reasoning = self.load_mapping_reasoning()
        
        if not mappings:
            logger.error("No mappings to validate")
            return {}
        
        # Validate each mapping with its reasoning if available
        validations = {}
        for word, emoji in mappings.items():
            word_reasoning = reasoning.get(word, "")
            validations[word] = self.validator.validate_single_mapping(
                word, emoji, word_reasoning
            )
            
        logger.info(f"Completed validation of {len(validations)} mappings")
        return validations
    
    def validate_sample_mappings(self, sample_size: int = 50) -> Dict[str, MappingValidation]:
        """Validate a sample of mappings for quicker testing"""
        logger.info(f"Validating sample of {sample_size} mappings...")
        
        mappings = self.load_existing_mappings()
        reasoning = self.load_mapping_reasoning()
        
        if not mappings:
            return {}
        
        # Take a sample (sorted by word length to get variety)
        sorted_words = sorted(mappings.keys(), key=len)
        sample_words = sorted_words[:sample_size]
        
        sample_mappings = {word: mappings[word] for word in sample_words}
        
        # Validate sample
        validations = {}
        for word, emoji in sample_mappings.items():
            word_reasoning = reasoning.get(word, "")
            validations[word] = self.validator.validate_single_mapping(
                word, emoji, word_reasoning
            )
            
        logger.info(f"Completed sample validation of {len(validations)} mappings")
        return validations
    
    def identify_problematic_mappings(self, validations: Dict[str, MappingValidation]) -> Dict[str, List[MappingValidation]]:
        """Identify mappings that need attention"""
        problems = {
            'rejected': [],
            'weak': [],
            'consistency_issues': [],
            'disambiguation_issues': []
        }
        
        for validation in validations.values():
            if validation.status == ValidationStatus.REJECTED:
                problems['rejected'].append(validation)
            elif validation.status == ValidationStatus.WEAK:
                problems['weak'].append(validation)
                
            if validation.consistency_notes:
                problems['consistency_issues'].append(validation)
                
            # Check for disambiguation issues
            for score in validation.scores:
                if (score.criterion.value == 'disambiguation' and 
                    score.score < 2.5):
                    problems['disambiguation_issues'].append(validation)
                    break
        
        logger.info(f"Identified problems:")
        logger.info(f"  Rejected: {len(problems['rejected'])}")
        logger.info(f"  Weak: {len(problems['weak'])}")
        logger.info(f"  Consistency issues: {len(problems['consistency_issues'])}")
        logger.info(f"  Disambiguation issues: {len(problems['disambiguation_issues'])}")
        
        return problems
    
    def generate_improvement_suggestions(self, validations: Dict[str, MappingValidation]) -> Dict[str, Dict]:
        """Generate specific improvement suggestions for mappings"""
        improvements = {}
        
        for word, validation in validations.items():
            if validation.status in [ValidationStatus.WEAK, ValidationStatus.REJECTED]:
                improvements[word] = {
                    'current_emoji': validation.emoji,
                    'current_score': validation.overall_score,
                    'issues': validation.issues,
                    'suggested_improvements': validation.improvements,
                    'alternative_emojis': validation.alternative_suggestions,
                    'priority': 'high' if validation.status == ValidationStatus.REJECTED else 'medium'
                }
        
        return improvements
    
    def create_validation_report(self, validations: Dict[str, MappingValidation], 
                               output_dir: str = "validation_reports") -> str:
        """Create comprehensive validation report"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate main report
        report = self.validator.generate_improvement_report(
            validations, 
            os.path.join(output_dir, "validation_report.md")
        )
        
        # Identify problems
        problems = self.identify_problematic_mappings(validations)
        
        # Generate improvements
        improvements = self.generate_improvement_suggestions(validations)
        
        # Save detailed results
        self.validator.save_validation_results(validations, output_dir)
        
        # Save improvement suggestions
        with open(os.path.join(output_dir, "improvement_suggestions.json"), 'w') as f:
            json.dump(improvements, f, indent=2, ensure_ascii=False)
        
        # Save problem categorization
        problems_serializable = {}
        for category, validations_list in problems.items():
            problems_serializable[category] = [
                {
                    'word': v.word,
                    'emoji': v.emoji,
                    'score': v.overall_score,
                    'status': v.status.value,
                    'issues': v.issues
                } for v in validations_list
            ]
        
        with open(os.path.join(output_dir, "problem_categories.json"), 'w') as f:
            json.dump(problems_serializable, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Validation report saved to {output_dir}/")
        return report
    
    def suggest_mapping_replacements(self, validations: Dict[str, MappingValidation]) -> Dict[str, str]:
        """Suggest specific emoji replacements for problematic mappings"""
        replacements = {}
        
        for word, validation in validations.items():
            if (validation.status in [ValidationStatus.WEAK, ValidationStatus.REJECTED] and 
                validation.alternative_suggestions):
                
                # Take the first alternative suggestion
                first_alt = validation.alternative_suggestions[0]
                # Extract emoji from suggestion (usually format like "🐵 - monkey emoji")
                if ' - ' in first_alt:
                    suggested_emoji = first_alt.split(' - ')[0].strip()
                    replacements[word] = suggested_emoji
        
        return replacements
    
    def update_mappings_with_suggestions(self, replacements: Dict[str, str], backup: bool = True):
        """Update mapping files with suggested improvements"""
        if not replacements:
            logger.info("No replacements to apply")
            return
        
        # Backup original files if requested
        if backup:
            import shutil
            backup_suffix = ".backup"
            shutil.copy(self.word_to_emoji_file, str(self.word_to_emoji_file) + backup_suffix)
            shutil.copy(self.emoji_to_word_file, str(self.emoji_to_word_file) + backup_suffix)
            logger.info("Backed up original mapping files")
        
        # Load current mappings
        with open(self.word_to_emoji_file, 'r', encoding='utf-8') as f:
            word_to_emoji = json.load(f)
        
        with open(self.emoji_to_word_file, 'r', encoding='utf-8') as f:
            emoji_to_word = json.load(f)
        
        # Apply replacements
        updated_count = 0
        for word, new_emoji in replacements.items():
            if word in word_to_emoji:
                old_emoji = word_to_emoji[word]
                
                # Update word-to-emoji mapping
                word_to_emoji[word] = new_emoji
                
                # Update emoji-to-word mapping
                if old_emoji in emoji_to_word:
                    del emoji_to_word[old_emoji]
                emoji_to_word[new_emoji] = word
                
                updated_count += 1
                logger.info(f"Updated '{word}': {old_emoji} → {new_emoji}")
        
        # Save updated mappings
        with open(self.word_to_emoji_file, 'w', encoding='utf-8') as f:
            json.dump(word_to_emoji, f, indent=2, ensure_ascii=False)
        
        with open(self.emoji_to_word_file, 'w', encoding='utf-8') as f:
            json.dump(emoji_to_word, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Updated {updated_count} mappings in the mapping files")

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="Semantic Validation for Emoji Mappings")
    parser.add_argument('--emoji-dir', default='mappings', help='Directory containing emoji mappings')
    parser.add_argument('--llm-url', default='http://127.0.0.1:1234', help='LLM API base URL')
    parser.add_argument('--sample-size', type=int, default=0, help='Validate only N mappings for testing (0 = all)')
    parser.add_argument('--output-dir', default='validation_reports', help='Output directory for reports')
    parser.add_argument('--apply-suggestions', action='store_true', help='Apply improvement suggestions to mapping files')
    parser.add_argument('--no-backup', action='store_true', help='Skip backing up original files when applying suggestions')
    
    args = parser.parse_args()
    
    # Initialize integration
    integration = MappingValidationIntegration(args.emoji_dir, args.llm_url)
    
    # Validate mappings
    if args.sample_size > 0:
        validations = integration.validate_sample_mappings(args.sample_size)
    else:
        validations = integration.validate_all_mappings()
    
    if not validations:
        logger.error("No mappings were validated")
        return
    
    # Generate reports
    report = integration.create_validation_report(validations, args.output_dir)
    
    # Print summary
    total = len(validations)
    excellent = sum(1 for v in validations.values() if v.status == ValidationStatus.EXCELLENT)
    good = sum(1 for v in validations.values() if v.status == ValidationStatus.GOOD)
    acceptable = sum(1 for v in validations.values() if v.status == ValidationStatus.ACCEPTABLE)
    weak = sum(1 for v in validations.values() if v.status == ValidationStatus.WEAK)
    rejected = sum(1 for v in validations.values() if v.status == ValidationStatus.REJECTED)
    
    print(f"\n{'='*60}")
    print("SEMANTIC VALIDATION RESULTS")
    print(f"{'='*60}")
    print(f"Total mappings validated: {total}")
    print(f"Excellent: {excellent} ({excellent/total*100:.1f}%)")
    print(f"Good: {good} ({good/total*100:.1f}%)")
    print(f"Acceptable: {acceptable} ({acceptable/total*100:.1f}%)")
    print(f"Weak: {weak} ({weak/total*100:.1f}%)")
    print(f"Rejected: {rejected} ({rejected/total*100:.1f}%)")
    
    avg_score = sum(v.overall_score for v in validations.values()) / total
    print(f"Average quality score: {avg_score:.2f}/5.0")
    
    high_quality = excellent + good
    needs_improvement = weak + rejected
    print(f"High quality mappings: {high_quality} ({high_quality/total*100:.1f}%)")
    print(f"Needs improvement: {needs_improvement} ({needs_improvement/total*100:.1f}%)")
    
    # Apply suggestions if requested
    if args.apply_suggestions:
        replacements = integration.suggest_mapping_replacements(validations)
        if replacements:
            print(f"\nApplying {len(replacements)} suggested improvements...")
            integration.update_mappings_with_suggestions(replacements, backup=not args.no_backup)
        else:
            print("\nNo clear replacement suggestions available")
    
    print(f"\nDetailed reports saved to: {args.output_dir}/")
    print("- validation_report.md: Human-readable improvement report")
    print("- validation_results.json: Complete validation data")
    print("- improvement_suggestions.json: Specific improvement recommendations")
    print("- problem_categories.json: Categorized problem mappings")

if __name__ == "__main__":
    main()
