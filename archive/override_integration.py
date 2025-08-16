#!/usr/bin/env python3
# Override Integration Utility
# ✅ Bridges manual override system with existing source builders
# ✅ Analyzes current mappings and suggests improvements
# ✅ Generates reports on mapping quality

import os
import json
import time
from typing import Dict, List, Set
from manual_override_system import ManualOverrideSystem, OverridePriority, OverrideStatus
from semantic_validator import SemanticValidator, ValidationStatus

class OverrideIntegration:
    """Integration utility for manual override system"""
    
    def __init__(self):
        self.override_system = ManualOverrideSystem()
        self.semantic_validator = SemanticValidator()
        
    def analyze_current_mappings(self, sample_size: int = 200) -> Dict:
        """Analyze current mappings and identify candidates for override"""
        
        print(f"🔍 Analyzing current mappings (sample size: {sample_size})")
        
        # Get a representative sample of mappings
        mappings = dict(list(self.override_system.word_to_emoji.items())[:sample_size])
        
        # Validate mappings using semantic validator
        print("📊 Running semantic validation...")
        validations = self.semantic_validator.validate_mapping_batch(mappings)
        
        # Analyze results
        candidates = {
            'weak_mappings': [],
            'rejected_mappings': [],
            'inconsistent_mappings': [],
            'high_frequency_weak': [],
            'critical_improvements': []
        }
        
        for word, validation in validations.items():
            # Check if it's a weak or rejected mapping
            if validation.status == ValidationStatus.WEAK:
                candidates['weak_mappings'].append((word, validation))
            elif validation.status == ValidationStatus.REJECTED:
                candidates['rejected_mappings'].append((word, validation))
            
            # Check for consistency issues
            if validation.consistency_notes:
                candidates['inconsistent_mappings'].append((word, validation))
            
            # Check if it's a high-frequency word with poor mapping
            freq_rank = self.override_system._get_frequency_rank(word)
            if freq_rank and freq_rank <= 1000 and validation.overall_score < 3.0:
                candidates['high_frequency_weak'].append((word, validation, freq_rank))
            
            # Critical words that need immediate attention
            if (word in self.override_system.critical_words and 
                validation.overall_score < 2.5):
                candidates['critical_improvements'].append((word, validation))
        
        return candidates
    
    def create_overrides_from_analysis(self, analysis: Dict, max_per_category: int = 20) -> int:
        """Create override entries based on analysis results"""
        
        created_count = 0
        
        # Critical improvements first
        for word, validation in analysis['critical_improvements'][:max_per_category]:
            if word not in self.override_system.override_entries:
                try:
                    self.override_system.create_override_entry(word, OverridePriority.CRITICAL)
                    created_count += 1
                    time.sleep(0.1)  # Rate limiting
                except Exception as e:
                    print(f"❌ Failed to create override for '{word}': {e}")
        
        # High frequency weak mappings
        sorted_freq_weak = sorted(
            analysis['high_frequency_weak'], 
            key=lambda x: x[2]  # Sort by frequency rank
        )
        for word, validation, freq_rank in sorted_freq_weak[:max_per_category]:
            if word not in self.override_system.override_entries:
                try:
                    priority = OverridePriority.CRITICAL if freq_rank <= 500 else OverridePriority.HIGH
                    self.override_system.create_override_entry(word, priority)
                    created_count += 1
                    time.sleep(0.1)
                except Exception as e:
                    print(f"❌ Failed to create override for '{word}': {e}")
        
        # Rejected mappings
        for word, validation in analysis['rejected_mappings'][:max_per_category]:
            if word not in self.override_system.override_entries:
                try:
                    self.override_system.create_override_entry(word, OverridePriority.HIGH)
                    created_count += 1
                    time.sleep(0.1)
                except Exception as e:
                    print(f"❌ Failed to create override for '{word}': {e}")
        
        print(f"✅ Created {created_count} new override entries from analysis")
        return created_count
    
    def generate_improvement_candidates_report(self, analysis: Dict) -> str:
        """Generate report of improvement candidates"""
        
        report_lines = [
            "# Mapping Improvement Candidates Report",
            "=" * 60,
            "",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            f"- Critical improvements needed: {len(analysis['critical_improvements'])}",
            f"- High-frequency weak mappings: {len(analysis['high_frequency_weak'])}",
            f"- Rejected mappings: {len(analysis['rejected_mappings'])}",
            f"- Weak mappings: {len(analysis['weak_mappings'])}",
            f"- Inconsistent mappings: {len(analysis['inconsistent_mappings'])}",
            "",
        ]
        
        # Critical improvements section
        if analysis['critical_improvements']:
            report_lines.extend([
                "## 🚨 Critical Improvements Needed",
                "",
                "These are high-priority words with poor mappings that need immediate attention:",
                ""
            ])
            
            for word, validation in analysis['critical_improvements'][:15]:
                report_lines.append(
                    f"- **{word}** → {validation.emoji} "
                    f"(Score: {validation.overall_score:.2f})"
                )
                if validation.issues:
                    for issue in validation.issues[:2]:
                        report_lines.append(f"  - Issue: {issue}")
                if validation.alternative_suggestions:
                    alt = validation.alternative_suggestions[0]
                    report_lines.append(f"  - Suggestion: {alt}")
                report_lines.append("")
        
        # High frequency weak mappings
        if analysis['high_frequency_weak']:
            report_lines.extend([
                "## 📈 High-Frequency Words with Weak Mappings",
                "",
                "Common words that users encounter frequently but have poor emoji mappings:",
                ""
            ])
            
            sorted_freq_weak = sorted(
                analysis['high_frequency_weak'], 
                key=lambda x: x[2]  # Sort by frequency rank
            )
            
            for word, validation, freq_rank in sorted_freq_weak[:15]:
                report_lines.append(
                    f"- **{word}** (rank #{freq_rank}) → {validation.emoji} "
                    f"(Score: {validation.overall_score:.2f})"
                )
                if validation.alternative_suggestions:
                    alt = validation.alternative_suggestions[0]
                    report_lines.append(f"  - Better option: {alt}")
                report_lines.append("")
        
        # Rejected mappings
        if analysis['rejected_mappings']:
            report_lines.extend([
                "## ❌ Rejected Mappings",
                "",
                "Mappings that scored very poorly and should be replaced:",
                ""
            ])
            
            for word, validation in analysis['rejected_mappings'][:10]:
                report_lines.append(
                    f"- **{word}** → {validation.emoji} "
                    f"(Score: {validation.overall_score:.2f})"
                )
                if validation.issues:
                    main_issue = validation.issues[0]
                    report_lines.append(f"  - Main issue: {main_issue}")
                report_lines.append("")
        
        return "\n".join(report_lines)
    
    def export_high_frequency_list(self, top_n: int = 1000) -> List[str]:
        """Export list of high-frequency words for manual curation"""
        
        sorted_words = sorted(
            self.override_system.word_frequencies.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        high_freq_words = []
        for word, freq in sorted_words[:top_n]:
            if word in self.override_system.word_to_emoji:
                emoji = self.override_system.word_to_emoji[word]
                high_freq_words.append({
                    'word': word,
                    'emoji': emoji,
                    'frequency': freq,
                    'rank': len(high_freq_words) + 1,
                    'category': self.override_system._determine_semantic_category(word),
                    'has_override': word in self.override_system.override_entries
                })
        
        return high_freq_words
    
    def save_high_frequency_report(self, output_file: str = None) -> str:
        """Save high-frequency words report"""
        
        if not output_file:
            output_file = os.path.join(
                self.override_system.override_dir, 
                "high_frequency_words.json"
            )
        
        high_freq_data = self.export_high_frequency_list()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(high_freq_data, f, indent=2, ensure_ascii=False)
        
        # Also create a markdown report
        md_file = output_file.replace('.json', '.md')
        md_lines = [
            "# High-Frequency Words Report",
            "=" * 50,
            "",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total words:** {len(high_freq_data)}",
            "",
            "## Top 100 Most Frequent Words",
            "",
            "| Rank | Word | Emoji | Category | Has Override |",
            "|------|------|-------|----------|-------------|"
        ]
        
        for item in high_freq_data[:100]:
            override_status = "✅" if item['has_override'] else "❌"
            md_lines.append(
                f"| {item['rank']} | {item['word']} | {item['emoji']} | "
                f"{item['category']} | {override_status} |"
            )
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(md_lines))
        
        print(f"💾 High-frequency words report saved to {output_file}")
        print(f"📄 Markdown report saved to {md_file}")
        
        return output_file
    
    def update_manual_overrides_file(self):
        """Update the manual_overrides.json file that the builders use"""
        
        approved_overrides = self.override_system.export_approved_overrides()
        
        override_file = os.path.join(
            self.override_system.mappings_dir, 
            "manual_overrides.json"
        )
        
        # Load existing overrides
        existing_overrides = {}
        if os.path.exists(override_file):
            with open(override_file, 'r', encoding='utf-8') as f:
                existing_overrides = json.load(f)
        
        # Merge with approved overrides (approved takes precedence)
        merged_overrides = {**existing_overrides, **approved_overrides}
        
        # Save updated file
        with open(override_file, 'w', encoding='utf-8') as f:
            json.dump(merged_overrides, f, indent=2, ensure_ascii=False)
        
        print(f"📝 Updated manual_overrides.json with {len(approved_overrides)} approved overrides")
        
        return len(merged_overrides)

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Override Integration Utility")
    parser.add_argument('command', choices=[
        'analyze', 'create-from-analysis', 'report', 'high-frequency', 
        'update-overrides', 'full-analysis'
    ], help='Command to execute')
    parser.add_argument('--sample-size', type=int, default=200,
                       help='Sample size for analysis')
    parser.add_argument('--max-per-category', type=int, default=20,
                       help='Maximum overrides to create per category')
    parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    integration = OverrideIntegration()
    
    if args.command == 'analyze':
        print("🔍 Analyzing current mappings...")
        analysis = integration.analyze_current_mappings(args.sample_size)
        
        print("\n📊 Analysis Results:")
        print(f"- Critical improvements: {len(analysis['critical_improvements'])}")
        print(f"- High-frequency weak: {len(analysis['high_frequency_weak'])}")
        print(f"- Rejected mappings: {len(analysis['rejected_mappings'])}")
        print(f"- Weak mappings: {len(analysis['weak_mappings'])}")
        
    elif args.command == 'create-from-analysis':
        print("🔍 Analyzing and creating override entries...")
        analysis = integration.analyze_current_mappings(args.sample_size)
        count = integration.create_overrides_from_analysis(analysis, args.max_per_category)
        print(f"✅ Created {count} override entries")
        
    elif args.command == 'report':
        print("📄 Generating improvement candidates report...")
        analysis = integration.analyze_current_mappings(args.sample_size)
        report = integration.generate_improvement_candidates_report(analysis)
        
        output_file = args.output or os.path.join(
            integration.override_system.override_dir,
            "improvement_candidates.md"
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 Report saved to {output_file}")
        
    elif args.command == 'high-frequency':
        print("📈 Generating high-frequency words report...")
        output_file = integration.save_high_frequency_report(args.output)
        
    elif args.command == 'update-overrides':
        print("📝 Updating manual overrides file...")
        count = integration.update_manual_overrides_file()
        print(f"✅ Manual overrides file updated with {count} total overrides")
        
    elif args.command == 'full-analysis':
        print("🚀 Running full analysis pipeline...")
        
        # Step 1: Analyze current mappings
        print("\n1️⃣ Analyzing current mappings...")
        analysis = integration.analyze_current_mappings(args.sample_size)
        
        # Step 2: Create override entries
        print("\n2️⃣ Creating override entries...")
        count = integration.create_overrides_from_analysis(analysis, args.max_per_category)
        
        # Step 3: Generate reports
        print("\n3️⃣ Generating reports...")
        
        # Improvement candidates report
        report = integration.generate_improvement_candidates_report(analysis)
        report_file = os.path.join(
            integration.override_system.override_dir,
            "improvement_candidates.md"
        )
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # High-frequency words report
        integration.save_high_frequency_report()
        
        # Update manual overrides
        print("\n4️⃣ Updating manual overrides file...")
        total_overrides = integration.update_manual_overrides_file()
        
        print("\n✅ Full analysis complete!")
        print(f"   - Created {count} new override entries")
        print(f"   - Generated improvement report: {report_file}")
        print(f"   - Total manual overrides: {total_overrides}")
        
    # Save all data
    integration.override_system.save_all_data()

if __name__ == "__main__":
    main()
