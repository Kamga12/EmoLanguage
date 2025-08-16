#!/usr/bin/env python3
"""
Semantic Mapping Generator

This system uses an LLM to generate word-to-emoji mappings from scratch for words in documents/dictionary.txt.
It creates semantically intuitive mappings and saves them to logs/ for analysis.

REFACTORED VERSION: Now uses modular architecture with separated concerns.
"""

import logging
import argparse
from pathlib import Path

from lib.semantic_mapping_generator import SemanticMappingGenerator
from lib.config import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL, 
    DEFAULT_MAPPING_BATCH_SIZE,
    DEFAULT_COLLISION_BATCH_SIZE,
    DEFAULT_DICTIONARY_PATH,
    LOG_FORMAT,
    LOG_LEVEL
)

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="Generate semantic mappings from documents/dictionary.txt using local LLM")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL,
                       help=f"Base URL for local LLM server (default: {DEFAULT_BASE_URL})")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                       help=f"Model name to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--mapping-size", type=int, default=DEFAULT_MAPPING_BATCH_SIZE,
                       help=f"Number of words to process in each mapping batch (default: {DEFAULT_MAPPING_BATCH_SIZE})")
    parser.add_argument("--collision-size", type=int, default=DEFAULT_COLLISION_BATCH_SIZE,
                       help=f"Number of collision pairs to send to the LLM at once (default: {DEFAULT_COLLISION_BATCH_SIZE})")
    parser.add_argument("--dictionary", default=DEFAULT_DICTIONARY_PATH,
                       help=f"Path to dictionary file (default: {DEFAULT_DICTIONARY_PATH})")
    parser.add_argument("--dry-run", "-d", action="store_true",
                       help="Show what would be processed without making changes")
    
    args = parser.parse_args()
    
    try:
        # Initialize generator
        generator = SemanticMappingGenerator(base_url=args.base_url, model=args.model)
        
        print(f"🎯 Generating emoji mappings for all words from {args.dictionary}...")
        
        if args.dry_run:
            print(f"\n🔍 DRY RUN MODE - Processing dictionary words but won't save results...\n")
        
        # Generate mappings from dictionary
        mappings = generator.generate_dictionary_mappings(
            mapping_size=args.mapping_size,
            collision_size=args.collision_size,
            dictionary_path=args.dictionary
        )
        
        if not args.dry_run:
            # Save mappings
            mappings_file = generator.save_mappings(mappings)
            
            # Generate report
            report = generator.create_generation_report(mappings)
            report_path = generator.file_manager.save_report(report)
            
            print(f"\n✅ Generation complete!")
            print(f"📄 Detailed mappings saved to: {mappings_file}")
            print(f"📊 Report saved to: {report_path}")
            print(f"🗂️ Core mappings saved to: mappings/mapping.json")
            print(f"\n🚀 Ready to use! Try: python3 encode.py \"Hello world\"")
            
        else:
            print(f"\n🔍 DRY RUN complete - no files saved!")
            
            # Show some sample results in dry-run
            print(f"\n📋 Sample Results:")
            sample_mappings = mappings[:10] if len(mappings) >= 10 else mappings
            for i, mapping in enumerate(sample_mappings, 1):
                print(f"\n{i}. \"{mapping.word}\" → {mapping.suggested_emojis}")
                print(f"   Category: {mapping.category}")
            
            print(f"\n💡 To save results, run without --dry-run flag")
        
        # Print summary
        analysis = generator.analyze_mappings(mappings)
        print(f"\n📊 Summary:")
        print(f"   • Total words processed: {analysis['total_mappings']}")
        print(f"   • Successful mappings: {analysis['successful_mappings']}")
        print(f"   • Success rate: {analysis['success_rate']:.1%}")
        
        # Print category breakdown
        if analysis['category_counts']:
            print(f"   • Category breakdown:")
            for category, count in analysis['category_counts'].items():
                print(f"     - {category}: {count}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during generation: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
