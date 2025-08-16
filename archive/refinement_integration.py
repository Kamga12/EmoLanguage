# Progressive Refinement Integration with Manual Override System
# ✅ Applies high-confidence improvements automatically 
# ✅ Integrates with existing manual override system
# ✅ Provides safe application of refinement suggestions
# ✅ Maintains audit trail of all changes

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import asdict
import datetime

# Import existing systems
from progressive_refinement import ProgressiveRefinementSystem, MappingImprovement
from manual_override_system import ManualOverrideSystem, Override, OverrideReason
from semantic_validator import SemanticValidator, ValidationStatus

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RefinementIntegration:
    """
    Integration system that applies progressive refinement suggestions 
    through the manual override system with safety checks.
    """
    
    def __init__(self, llm_base_url: str = "http://127.0.0.1:1234"):
        self.refinement_system = ProgressiveRefinementSystem(llm_base_url)
        self.override_system = ManualOverrideSystem()
        self.validator = SemanticValidator(llm_base_url)
        
        # Integration configuration
        self.config = {
            "auto_apply_threshold": 0.8,  # Apply improvements with confidence >= 0.8
            "validation_threshold": 3.5,  # Require validation score >= 3.5
            "min_improvement": 0.5,       # Minimum expected improvement
            "max_auto_applications": 50,  # Maximum automatic applications per run
            "require_validation": True,   # Validate before applying
            "backup_original": True       # Create backup of original mappings
        }
        
        # State tracking
        self.applied_improvements = []
        self.rejected_improvements = []
        self.validation_failures = []
    
    def run_integrated_refinement(self, mapping_file: str = "mappings/word_to_emoji.json",
                                 max_iterations: int = 3,
                                 apply_improvements: bool = True) -> Dict:
        """
        Run complete integrated refinement process with automatic application
        """
        logger.info("🚀 Starting integrated refinement process")
        
        # Load current mappings
        mappings = self.refinement_system.load_current_mappings(mapping_file)
        if not mappings:
            logger.error("Could not load mappings")
            return {}
        
        # Create backup if configured
        if self.config["backup_original"]:
            self._create_backup(mapping_file)
        
        # Run refinement process
        logger.info("Running progressive refinement analysis...")
        refinement_results = self.refinement_system.run_progressive_refinement(
            mappings, max_iterations=max_iterations
        )
        
        # Apply improvements if requested
        if apply_improvements:
            logger.info("Applying high-confidence improvements...")
            application_results = self._apply_high_confidence_improvements(
                refinement_results["final_improvements"]
            )
            refinement_results["application_results"] = application_results
        
        # Generate integration report
        integration_report = self._generate_integration_report(refinement_results)
        
        # Save all results
        self._save_integration_results(refinement_results, integration_report)
        
        logger.info("✅ Integrated refinement process complete!")
        logger.info(f"Applied {len(self.applied_improvements)} improvements automatically")
        logger.info(f"Rejected {len(self.rejected_improvements)} low-confidence suggestions")
        
        return refinement_results
    
    def _create_backup(self, mapping_file: str):
        """Create backup of original mappings"""
        backup_dir = "refinement_backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"word_to_emoji_backup_{timestamp}.json")
        
        try:
            import shutil
            shutil.copy2(mapping_file, backup_file)
            logger.info(f"Created backup: {backup_file}")
        except Exception as e:
            logger.warning(f"Could not create backup: {e}")
    
    def _apply_high_confidence_improvements(self, improvements: Dict[str, List[Dict]]) -> Dict:
        """Apply improvements that meet confidence and validation thresholds"""
        
        application_results = {
            "applied": [],
            "rejected": [],
            "validation_failures": [],
            "total_candidates": 0,
            "statistics": {}
        }
        
        # Process each word's improvements
        for word, word_improvements in improvements.items():
            for imp_dict in word_improvements:
                application_results["total_candidates"] += 1
                
                # Convert dict back to MappingImprovement
                improvement = MappingImprovement(
                    word=imp_dict["word"],
                    current_emoji=imp_dict["current_emoji"], 
                    suggested_emoji=imp_dict["suggested_emoji"],
                    reasoning=imp_dict["reasoning"],
                    expected_improvement=imp_dict["expected_improvement"],
                    confidence=imp_dict["confidence"],
                    validation_needed=imp_dict.get("validation_needed", True)
                )
                
                # Check if improvement meets thresholds
                if self._should_apply_improvement(improvement):
                    # Validate the improvement if required
                    if self.config["require_validation"]:
                        validation_result = self._validate_improvement(improvement)
                        if not validation_result["approved"]:
                            application_results["validation_failures"].append({
                                "improvement": asdict(improvement),
                                "validation_result": validation_result
                            })
                            self.validation_failures.append((improvement, validation_result))
                            continue
                    
                    # Apply the improvement
                    success = self._apply_single_improvement(improvement)
                    if success:
                        application_results["applied"].append(asdict(improvement))
                        self.applied_improvements.append(improvement)
                        
                        # Stop if we've reached the maximum
                        if len(self.applied_improvements) >= self.config["max_auto_applications"]:
                            logger.info(f"Reached maximum auto-applications ({self.config['max_auto_applications']})")
                            break
                    else:
                        application_results["rejected"].append({
                            "improvement": asdict(improvement),
                            "reason": "Application failed"
                        })
                else:
                    # Record why it was rejected
                    rejection_reason = self._get_rejection_reason(improvement)
                    application_results["rejected"].append({
                        "improvement": asdict(improvement),
                        "reason": rejection_reason
                    })
                    self.rejected_improvements.append((improvement, rejection_reason))
            
            # Break outer loop if we've hit the limit
            if len(self.applied_improvements) >= self.config["max_auto_applications"]:
                break
        
        # Calculate statistics
        application_results["statistics"] = {
            "total_candidates": application_results["total_candidates"],
            "applied_count": len(application_results["applied"]),
            "rejected_count": len(application_results["rejected"]),
            "validation_failure_count": len(application_results["validation_failures"]),
            "application_rate": len(application_results["applied"]) / max(application_results["total_candidates"], 1),
            "avg_confidence_applied": sum(imp["confidence"] for imp in application_results["applied"]) / max(len(application_results["applied"]), 1),
            "avg_expected_improvement": sum(imp["expected_improvement"] for imp in application_results["applied"]) / max(len(application_results["applied"]), 1)
        }
        
        return application_results
    
    def _should_apply_improvement(self, improvement: MappingImprovement) -> bool:
        """Determine if an improvement should be automatically applied"""
        
        # Check confidence threshold
        if improvement.confidence < self.config["auto_apply_threshold"]:
            return False
        
        # Check expected improvement threshold
        if improvement.expected_improvement < self.config["min_improvement"]:
            return False
        
        # Additional safety checks
        if not improvement.suggested_emoji or improvement.suggested_emoji == improvement.current_emoji:
            return False
        
        # Check for potentially problematic suggestions
        if len(improvement.suggested_emoji) > 2:  # Too many emojis
            return False
        
        return True
    
    def _get_rejection_reason(self, improvement: MappingImprovement) -> str:
        """Get human-readable reason for rejection"""
        
        if improvement.confidence < self.config["auto_apply_threshold"]:
            return f"Low confidence: {improvement.confidence:.2f} < {self.config['auto_apply_threshold']}"
        
        if improvement.expected_improvement < self.config["min_improvement"]:
            return f"Low expected improvement: {improvement.expected_improvement:.2f} < {self.config['min_improvement']}"
        
        if not improvement.suggested_emoji:
            return "No suggested emoji provided"
        
        if improvement.suggested_emoji == improvement.current_emoji:
            return "Suggested emoji same as current"
        
        if len(improvement.suggested_emoji) > 2:
            return f"Too many emojis: {len(improvement.suggested_emoji)} > 2"
        
        return "Unknown reason"
    
    def _validate_improvement(self, improvement: MappingImprovement) -> Dict:
        """Validate an improvement before applying"""
        
        try:
            # Use semantic validator to check the suggested mapping
            validation = self.validator.validate_single_mapping(
                improvement.word, 
                improvement.suggested_emoji,
                improvement.reasoning
            )
            
            # Determine if validation passes
            approved = (validation.overall_score >= self.config["validation_threshold"] and 
                       validation.status not in [ValidationStatus.REJECTED, ValidationStatus.WEAK])
            
            return {
                "approved": approved,
                "validation_score": validation.overall_score,
                "status": validation.status.value,
                "issues": validation.issues,
                "reasoning": f"Validation score: {validation.overall_score:.2f}"
            }
            
        except Exception as e:
            logger.error(f"Validation failed for {improvement.word}: {e}")
            return {
                "approved": False,
                "validation_score": 0.0,
                "status": "error",
                "issues": [f"Validation error: {str(e)}"],
                "reasoning": "Validation system error"
            }
    
    def _apply_single_improvement(self, improvement: MappingImprovement) -> bool:
        """Apply a single improvement using the override system"""
        
        try:
            # Create override for the improvement
            override = Override(
                word=improvement.word,
                original_emoji=improvement.current_emoji,
                new_emoji=improvement.suggested_emoji,
                reason=OverrideReason.SEMANTIC_IMPROVEMENT,
                human_readable_reason=f"Progressive refinement: {improvement.reasoning}",
                confidence_score=improvement.confidence,
                expected_improvement=improvement.expected_improvement,
                source="progressive_refinement",
                notes=[
                    f"Expected improvement: +{improvement.expected_improvement:.2f}",
                    f"Confidence: {improvement.confidence:.2f}",
                    f"Auto-applied via refinement integration"
                ]
            )
            
            # Apply the override
            success = self.override_system.apply_override(override)
            
            if success:
                logger.info(f"✅ Applied improvement: {improvement.word} → {improvement.suggested_emoji}")
                return True
            else:
                logger.warning(f"❌ Failed to apply improvement for {improvement.word}")
                return False
                
        except Exception as e:
            logger.error(f"Error applying improvement for {improvement.word}: {e}")
            return False
    
    def _generate_integration_report(self, refinement_results: Dict) -> str:
        """Generate comprehensive integration report"""
        
        lines = [
            "# Progressive Refinement Integration Report",
            "=" * 50,
            "",
            f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Refinement Iterations:** {len(refinement_results.get('iterations', []))}",
            f"**Total Improvements Analyzed:** {sum(len(imps) for imps in refinement_results.get('final_improvements', {}).values())}",
            ""
        ]
        
        # Application summary
        if "application_results" in refinement_results:
            app_results = refinement_results["application_results"]
            stats = app_results.get("statistics", {})
            
            lines.extend([
                "## Application Summary",
                "",
                f"- **Total Candidates:** {stats.get('total_candidates', 0)}",
                f"- **Successfully Applied:** {stats.get('applied_count', 0)}",
                f"- **Rejected:** {stats.get('rejected_count', 0)}",
                f"- **Validation Failures:** {stats.get('validation_failure_count', 0)}",
                f"- **Application Rate:** {stats.get('application_rate', 0):.1%}",
                "",
                f"- **Average Confidence (Applied):** {stats.get('avg_confidence_applied', 0):.2f}",
                f"- **Average Expected Improvement:** {stats.get('avg_expected_improvement', 0):.2f}",
                ""
            ])
            
            # Successfully applied improvements
            if app_results.get("applied"):
                lines.extend([
                    "## Successfully Applied Improvements",
                    ""
                ])
                
                for imp in app_results["applied"][:10]:  # Show top 10
                    lines.extend([
                        f"### {imp['word']}",
                        f"- **Before:** {imp['current_emoji']}",
                        f"- **After:** {imp['suggested_emoji']}",
                        f"- **Reasoning:** {imp['reasoning']}",
                        f"- **Confidence:** {imp['confidence']:.2f}",
                        f"- **Expected Improvement:** +{imp['expected_improvement']:.2f}",
                        ""
                    ])
                
                if len(app_results["applied"]) > 10:
                    lines.append(f"... and {len(app_results['applied']) - 10} more improvements")
                    lines.append("")
            
            # Rejected improvements
            if app_results.get("rejected"):
                lines.extend([
                    "## Rejected Improvements",
                    "",
                    "Improvements that did not meet automatic application criteria:",
                    ""
                ])
                
                rejection_reasons = {}
                for rejection in app_results["rejected"]:
                    reason = rejection["reason"]
                    rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
                
                for reason, count in sorted(rejection_reasons.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"- **{reason}:** {count} improvements")
                
                lines.append("")
            
            # Validation failures  
            if app_results.get("validation_failures"):
                lines.extend([
                    "## Validation Failures",
                    "",
                    "High-confidence improvements that failed validation:",
                    ""
                ])
                
                for failure in app_results["validation_failures"][:5]:  # Show top 5
                    imp = failure["improvement"]
                    val = failure["validation_result"]
                    lines.extend([
                        f"### {imp['word']}",
                        f"- **Suggested:** {imp['suggested_emoji']} (confidence: {imp['confidence']:.2f})",
                        f"- **Validation Score:** {val['validation_score']:.2f}",
                        f"- **Issues:** {'; '.join(val['issues']) if val['issues'] else 'None'}",
                        ""
                    ])
        
        # Configuration used
        lines.extend([
            "## Configuration Used",
            "",
            f"- **Auto-apply Threshold:** {self.config['auto_apply_threshold']}",
            f"- **Validation Threshold:** {self.config['validation_threshold']}",
            f"- **Minimum Improvement:** {self.config['min_improvement']}",
            f"- **Max Auto Applications:** {self.config['max_auto_applications']}",
            f"- **Validation Required:** {self.config['require_validation']}",
            ""
        ])
        
        # Recommendations
        lines.extend([
            "## Recommendations",
            ""
        ])
        
        if refinement_results.get("recommendations"):
            for i, rec in enumerate(refinement_results["recommendations"], 1):
                lines.append(f"{i}. {rec}")
        
        # Add integration-specific recommendations
        if hasattr(self, 'applied_improvements') and len(self.applied_improvements) > 0:
            lines.append(f"{len(lines)-2}. Monitor applied improvements for user feedback")
        
        if hasattr(self, 'rejected_improvements') and len(self.rejected_improvements) > 10:
            lines.append(f"{len(lines)-2}. Review rejected improvements - consider lowering thresholds")
        
        if hasattr(self, 'validation_failures') and len(self.validation_failures) > 5:
            lines.append(f"{len(lines)-2}. High validation failure rate - review validation criteria")
        
        return "\n".join(lines)
    
    def _save_integration_results(self, refinement_results: Dict, integration_report: str):
        """Save all integration results"""
        
        output_dir = "refinement_integration_results"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save main results
        with open(os.path.join(output_dir, "integration_results.json"), 'w', encoding='utf-8') as f:
            json.dump(refinement_results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save integration report
        with open(os.path.join(output_dir, "integration_report.md"), 'w', encoding='utf-8') as f:
            f.write(integration_report)
        
        # Save detailed application log
        application_log = {
            "applied_improvements": [asdict(imp) for imp in self.applied_improvements],
            "rejected_improvements": [
                {"improvement": asdict(imp), "reason": reason} 
                for imp, reason in self.rejected_improvements
            ],
            "validation_failures": [
                {"improvement": asdict(imp), "validation_result": val} 
                for imp, val in self.validation_failures
            ],
            "configuration": self.config,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        with open(os.path.join(output_dir, "application_log.json"), 'w', encoding='utf-8') as f:
            json.dump(application_log, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Integration results saved to {output_dir}/")
    
    def review_pending_improvements(self, mapping_file: str = "mappings/word_to_emoji.json") -> Dict:
        """
        Review improvements that were rejected for potential manual application
        """
        logger.info("📋 Reviewing rejected improvements for manual consideration")
        
        if not self.rejected_improvements:
            logger.info("No rejected improvements to review")
            return {"manual_candidates": []}
        
        # Analyze rejection reasons
        manual_candidates = []
        
        for improvement, reason in self.rejected_improvements:
            # Improvements that might be worth manual review
            if ("Low confidence" in reason and improvement.confidence > 0.6) or \
               ("Low expected improvement" in reason and improvement.expected_improvement > 0.3):
                
                manual_candidates.append({
                    "improvement": asdict(improvement),
                    "rejection_reason": reason,
                    "manual_review_priority": self._calculate_manual_review_priority(improvement, reason),
                    "recommendation": self._get_manual_review_recommendation(improvement, reason)
                })
        
        # Sort by priority
        manual_candidates.sort(key=lambda x: x["manual_review_priority"], reverse=True)
        
        review_results = {
            "manual_candidates": manual_candidates,
            "total_rejected": len(self.rejected_improvements),
            "candidates_for_review": len(manual_candidates),
            "review_rate": len(manual_candidates) / max(len(self.rejected_improvements), 1)
        }
        
        logger.info(f"Found {len(manual_candidates)} improvements for manual review")
        return review_results
    
    def _calculate_manual_review_priority(self, improvement: MappingImprovement, rejection_reason: str) -> float:
        """Calculate priority score for manual review"""
        
        priority = 0.0
        
        # Base priority from confidence and expected improvement
        priority += improvement.confidence * 0.4
        priority += improvement.expected_improvement * 0.3
        
        # Adjust based on rejection reason
        if "Low confidence" in rejection_reason:
            if improvement.confidence > 0.6:
                priority += 0.2  # Close to threshold
        
        if "Low expected improvement" in rejection_reason:
            if improvement.expected_improvement > 0.3:
                priority += 0.1
        
        return min(priority, 1.0)
    
    def _get_manual_review_recommendation(self, improvement: MappingImprovement, rejection_reason: str) -> str:
        """Get recommendation for manual review"""
        
        if improvement.confidence > 0.7:
            return "High confidence despite rejection - consider manual application"
        elif improvement.expected_improvement > 0.8:
            return "High expected improvement - worth human evaluation"
        elif "Low confidence" in rejection_reason and improvement.confidence > 0.6:
            return "Close to confidence threshold - manual review recommended"
        else:
            return "Low priority - manual review optional"

# Main execution function
def run_integrated_refinement_process():
    """Main function to run the complete integrated refinement process"""
    
    logger.info("🚀 Starting Progressive Refinement Integration Process")
    
    # Initialize integration system
    integration = RefinementIntegration()
    
    # Run the complete process
    results = integration.run_integrated_refinement(
        mapping_file="mappings/word_to_emoji.json",
        max_iterations=3,
        apply_improvements=True
    )
    
    if results:
        # Review pending improvements
        review_results = integration.review_pending_improvements()
        results["manual_review_results"] = review_results
        
        # Final summary
        logger.info("🏁 Integration Process Complete!")
        logger.info("="*50)
        logger.info("SUMMARY:")
        logger.info(f"- Refinement iterations: {len(results.get('iterations', []))}")
        logger.info(f"- Improvements applied: {len(integration.applied_improvements)}")
        logger.info(f"- Improvements rejected: {len(integration.rejected_improvements)}")
        logger.info(f"- Manual review candidates: {len(review_results.get('manual_candidates', []))}")
        logger.info("="*50)
        logger.info("Check refinement_integration_results/ for detailed reports")
    
    return results

# Example usage and testing
if __name__ == "__main__":
    results = run_integrated_refinement_process()
