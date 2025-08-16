#!/usr/bin/env python3
# Interactive Review Interface for Manual Override System
# ✅ Simple command-line interface for reviewing word-emoji mappings
# ✅ Shows alternatives with scores and allows easy selection
# ✅ Supports batch processing and filtering by priority

import os
import sys
from typing import Optional
from manual_override_system import ManualOverrideSystem, OverridePriority, OverrideStatus

class InteractiveReviewer:
    """Interactive command-line interface for reviewing override entries"""
    
    def __init__(self):
        print("🎯 Manual Override System - Interactive Reviewer")
        print("=" * 60)
        
        self.override_system = ManualOverrideSystem()
        self.current_entries = []
        self.current_index = 0
        
        print(f"✅ System initialized with {len(self.override_system.override_entries)} override entries")
        
    def load_pending_entries(self, priority_filter: Optional[OverridePriority] = None) -> int:
        """Load entries that are pending review"""
        self.current_entries = []
        
        for word, entry in self.override_system.override_entries.items():
            if entry.status == OverrideStatus.PENDING_REVIEW:
                if priority_filter is None or entry.priority == priority_filter:
                    self.current_entries.append(entry)
        
        # Sort by priority and frequency
        priority_order = {
            OverridePriority.CRITICAL: 0,
            OverridePriority.HIGH: 1,
            OverridePriority.MEDIUM: 2,
            OverridePriority.LOW: 3
        }
        
        self.current_entries.sort(key=lambda e: (
            priority_order[e.priority],
            -(e.frequency_rank or 9999)
        ))
        
        self.current_index = 0
        return len(self.current_entries)
    
    def display_current_entry(self):
        """Display current entry for review"""
        if not self.current_entries or self.current_index >= len(self.current_entries):
            return False
        
        entry = self.current_entries[self.current_index]
        
        print(f"\n{'='*60}")
        print(f"📝 REVIEWING: {entry.word.upper()} ({self.current_index + 1}/{len(self.current_entries)})")
        print(f"{'='*60}")
        print(f"Priority: {entry.priority.value.upper()} | Category: {entry.category}")
        print(f"Frequency Rank: {entry.frequency_rank or 'Unknown'}")
        print(f"\n🔸 Current Mapping: {entry.word} → {entry.current_emoji}")
        
        if entry.current_reasoning:
            print(f"   Reasoning: {entry.current_reasoning}")
        
        print(f"\n🔸 Alternative Suggestions:")
        
        # Option A: Keep current
        print(f"   A. {entry.current_emoji} (KEEP CURRENT)")
        
        # Show alternatives
        for i, alt in enumerate(entry.alternatives, 1):
            option_letter = chr(ord('A') + i)
            print(f"   {option_letter}. {alt.emoji} - {alt.reasoning}")
            print(f"      📊 Confidence: {alt.confidence_score:.2f} | Semantic: {alt.semantic_fit:.2f} | Visual: {alt.visual_clarity:.2f}")
            print(f"      🔍 Source: {alt.source} | By: {alt.suggested_by}")
        
        return True
    
    def get_user_choice(self) -> tuple[str, str, str]:
        """Get user's choice and reasoning"""
        while True:
            print(f"\n{'─'*40}")
            choice = input("Select option [A/B/C/...] or 'skip'/'quit': ").strip().upper()
            
            if choice == 'QUIT':
                return 'quit', '', ''
            elif choice == 'SKIP':
                return 'skip', '', ''
            elif choice == 'HELP':
                self.show_help()
                continue
            
            # Validate choice
            entry = self.current_entries[self.current_index]
            max_options = len(entry.alternatives) + 1  # +1 for current option (A)
            
            if len(choice) == 1 and 'A' <= choice <= chr(ord('A') + max_options - 1):
                # Get reasoning
                reasoning = input("Enter reasoning for your choice: ").strip()
                if not reasoning:
                    reasoning = "No specific reasoning provided"
                
                # Get reviewer name
                reviewer = input("Your name/ID (optional): ").strip() or "interactive_reviewer"
                
                return choice, reasoning, reviewer
            else:
                print(f"❌ Invalid choice. Please select A-{chr(ord('A') + max_options - 1)}")
    
    def process_choice(self, choice: str, reasoning: str, reviewer: str) -> bool:
        """Process user's choice"""
        if choice in ['quit', 'skip']:
            return choice == 'quit'
        
        entry = self.current_entries[self.current_index]
        
        # Determine selected emoji
        if choice == 'A':
            # Keep current emoji
            selected_emoji = entry.current_emoji
        else:
            # Get alternative
            alt_index = ord(choice) - ord('A') - 1  # -1 because A is current, B is first alt
            if 0 <= alt_index < len(entry.alternatives):
                selected_emoji = entry.alternatives[alt_index].emoji
            else:
                print("❌ Invalid selection")
                return False
        
        # Apply the override
        success = self.override_system.review_override(
            entry.word, 
            selected_emoji, 
            reasoning, 
            reviewer
        )
        
        if success:
            if selected_emoji == entry.current_emoji:
                print(f"✅ Kept current mapping for '{entry.word}': {selected_emoji}")
            else:
                print(f"✅ Approved override for '{entry.word}': {entry.current_emoji} → {selected_emoji}")
        else:
            print(f"❌ Failed to process override for '{entry.word}'")
            return False
        
        return False  # Continue processing
    
    def show_help(self):
        """Show help information"""
        print(f"\n{'🔍 HELP':<20}")
        print("─" * 60)
        print("Commands:")
        print("  A, B, C, ...  - Select option (A = keep current, B+ = alternatives)")
        print("  skip          - Skip current entry without making changes")
        print("  quit          - Save and exit the reviewer")
        print("  help          - Show this help message")
        print("\nWhen making your choice, consider:")
        print("  • Semantic accuracy: Does the emoji represent the word's meaning?")
        print("  • Visual clarity: Is the connection obvious to users?")
        print("  • Cultural universality: Will it work across cultures?")
        print("  • Disambiguation: Is it specific enough for this word?")
        print("─" * 60)
    
    def show_progress(self):
        """Show current progress"""
        if self.current_entries:
            completed = self.current_index
            total = len(self.current_entries)
            percentage = (completed / total) * 100
            print(f"\n📊 Progress: {completed}/{total} entries reviewed ({percentage:.1f}%)")
    
    def run_interactive_review(self, priority_filter: Optional[str] = None):
        """Main interactive review loop"""
        
        # Parse priority filter
        filter_priority = None
        if priority_filter:
            try:
                filter_priority = OverridePriority(priority_filter.lower())
            except ValueError:
                print(f"❌ Invalid priority: {priority_filter}")
                return
        
        # Load entries
        count = self.load_pending_entries(filter_priority)
        if count == 0:
            print("🎉 No entries pending review!")
            return
        
        print(f"\n🔍 Loaded {count} entries for review")
        if filter_priority:
            print(f"   Filtered by priority: {filter_priority.value}")
        
        print("\nℹ️  Type 'help' for commands")
        
        # Review loop
        try:
            while self.current_index < len(self.current_entries):
                # Display current entry
                if not self.display_current_entry():
                    break
                
                # Get and process user choice
                choice, reasoning, reviewer = self.get_user_choice()
                
                # Process choice
                should_quit = self.process_choice(choice, reasoning, reviewer)
                if should_quit:
                    break
                
                # Move to next entry (unless we're skipping/quitting)
                if choice not in ['skip', 'quit']:
                    self.current_index += 1
                elif choice == 'skip':
                    self.current_index += 1
                
                # Show progress
                self.show_progress()
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Review interrupted by user")
        
        # Save all data
        print(f"\n💾 Saving all data...")
        self.override_system.save_all_data()
        print("✅ Data saved successfully")
        
        # Show final summary
        self.show_final_summary()
    
    def show_final_summary(self):
        """Show summary of review session"""
        stats = self.override_system._generate_statistics()
        
        print(f"\n{'📊 REVIEW SUMMARY':<20}")
        print("=" * 60)
        print(f"Total override entries: {stats['total_override_entries']}")
        print(f"Pending review: {stats['status_distribution'].get('pending_review', 0)}")
        print(f"Approved: {stats['status_distribution'].get('approved', 0)}")
        print(f"Rejected: {stats['status_distribution'].get('rejected', 0)}")
        print(f"Completion rate: {stats['completion_rate']:.1f}%")
        print(f"Improvement rate: {stats['improvement_rate']:.1f}%")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Interactive Review Interface for Manual Overrides")
    parser.add_argument('--priority', choices=['critical', 'high', 'medium', 'low'],
                       help='Filter by priority level')
    parser.add_argument('--create-sample', type=int, metavar='N',
                       help='Create N sample override entries for testing')
    
    args = parser.parse_args()
    
    if args.create_sample:
        print(f"🔧 Creating {args.create_sample} sample override entries...")
        reviewer = InteractiveReviewer()
        count = reviewer.override_system.batch_create_critical_overrides(args.create_sample)
        print(f"✅ Created {count} sample entries")
        return
    
    # Run interactive review
    reviewer = InteractiveReviewer()
    reviewer.run_interactive_review(args.priority)

if __name__ == "__main__":
    main()
