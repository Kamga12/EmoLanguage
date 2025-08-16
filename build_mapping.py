#!/usr/bin/env python3
"""
Semantic Mapping Generator

This system uses an LLM to generate word-to-emoji mappings from scratch for 
words in documents/dictionary.txt. It creates semantically intuitive mappings
and saves them to logs/ for analysis.

The system supports both single-pass and multi-pass generation modes for
optimal quality control.
"""

# Standard library imports
import argparse
import logging
from typing import List

# Local imports
from lib.semantic_mapping_generator import SemanticMappingGenerator
from lib.config import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_MAPPING_BATCH_SIZE,
    DEFAULT_COLLISION_BATCH_SIZE,
    DEFAULT_DICTIONARY_PATH
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main() -> int:
    """Main function for command-line usage.
    
    Parses command-line arguments and initiates the semantic mapping
    generation process using either single-pass or multi-pass modes.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
        
    Raises:
        SystemExit: When argument parsing fails
    """
    parser = argparse.ArgumentParser(
        description="Generate semantic mappings from documents/dictionary.txt using local LLM"
    )
    
    # LLM configuration arguments
    parser.add_argument(
        "--base-url", 
        default=DEFAULT_BASE_URL,
        help=f"Base URL for local LLM server (default: {DEFAULT_BASE_URL})"
    )
    parser.add_argument(
        "--model", 
        default=DEFAULT_MODEL,
        help=f"Model name to use (default: {DEFAULT_MODEL})"
    )
    
    # Batch size configuration
    parser.add_argument(
        "--mapping-size", 
        type=int, 
        default=DEFAULT_MAPPING_BATCH_SIZE,
        help=f"Number of words to process in each mapping batch (default: {DEFAULT_MAPPING_BATCH_SIZE})"
    )
    parser.add_argument(
        "--collision-size", 
        type=int, 
        default=DEFAULT_COLLISION_BATCH_SIZE,
        help=f"Number of collision pairs to send to the LLM at once (default: {DEFAULT_COLLISION_BATCH_SIZE})"
    )
    
    # Input/output configuration
    parser.add_argument(
        "--dictionary", 
        default=DEFAULT_DICTIONARY_PATH,
        help=f"Path to dictionary file (default: {DEFAULT_DICTIONARY_PATH})"
    )
    parser.add_argument(
        "--dry-run", "-d", 
        action="store_true",
        help="Show what would be processed without making changes"
    )
    
    # Quality control arguments
    parser.add_argument(
        "--multipass", 
        action="store_true",
        help="Use multi-pass generation for higher quality (slower but better consensus)"
    )
    parser.add_argument(
        "--passes", 
        type=int, 
        default=3,
        help="Number of LLM passes for multi-pass generation (default: 3)"
    )
    parser.add_argument(
        "--collision-passes", 
        type=int, 
        default=None,
        help="Number of LLM passes for collision resolution (default: same as --passes)"
    )
    
    args = parser.parse_args()
    
    # Set default collision passes to same as passes if not specified
    if args.collision_passes is None:
        args.collision_passes = args.passes
    
    try:
        # Initialize the semantic mapping generator with LLM configuration
        generator = SemanticMappingGenerator(
            base_url=args.base_url, 
            model=args.model
        )
        
        # Display generation mode and configuration
        _display_generation_info(args)
        
        # Generate mappings using appropriate method
        mappings = _generate_mappings(generator, args)
        
        # Handle output based on dry-run mode
        if not args.dry_run:
            _save_results(generator, mappings)
        else:
            _display_dry_run_results(mappings)
        
        # Display summary statistics
        _display_summary(generator, mappings)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during generation: {e}")
        return 1


def _display_generation_info(args: argparse.Namespace) -> None:
    """Display information about the generation mode and configuration.
    
    Args:
        args: Parsed command-line arguments
    """
    if args.multipass:
        print(f"🧠 Using multi-pass generation with {args.passes} passes for higher quality...")
        if args.collision_passes != args.passes:
            print(f"🔧 Using {args.collision_passes} passes for collision resolution...")
    
    print(f"🎯 Generating emoji mappings for all words from {args.dictionary}...")
    
    if args.dry_run:
        print(f"\n🔍 DRY RUN MODE - Processing dictionary words but won't save results...\n")


def _generate_mappings(generator: SemanticMappingGenerator, args: argparse.Namespace) -> List:
    """Generate emoji mappings using the appropriate method.
    
    Args:
        generator: Initialized semantic mapping generator
        args: Parsed command-line arguments
        
    Returns:
        List of generated mappings
    """
    if args.multipass:
        return generator.generate_dictionary_mappings_multipass(
            mapping_size=args.mapping_size,
            collision_size=args.collision_size,
            dictionary_path=args.dictionary,
            num_passes=args.passes,
            collision_passes=args.collision_passes
        )
    else:
        return generator.generate_dictionary_mappings(
            mapping_size=args.mapping_size,
            collision_size=args.collision_size,
            dictionary_path=args.dictionary
        )


def _save_results(generator: SemanticMappingGenerator, mappings: List) -> None:
    """Save generation results to files.
    
    Args:
        generator: Semantic mapping generator instance
        mappings: Generated mappings to save
    """
    # Save detailed mappings
    mappings_file = generator.save_mappings(mappings)
    
    # Generate and save analysis report
    report = generator.create_generation_report(mappings)
    report_path = generator.file_manager.save_report(report)
    
    # Display success messages
    print(f"\n✅ Generation complete!")
    print(f"📄 Detailed mappings saved to: {mappings_file}")
    print(f"📊 Report saved to: {report_path}")
    print(f"🗂️ Core mappings saved to: mappings/mapping.json")
    print(f"\n🚀 Ready to use! Try: python3 encode.py \"Hello world\"")


def _display_dry_run_results(mappings: List) -> None:
    """Display sample results for dry-run mode.
    
    Args:
        mappings: Generated mappings to display
    """
    print(f"\n🔍 DRY RUN complete - no files saved!")
    
    # Show sample results (up to 10 mappings)
    print(f"\n📋 Sample Results:")
    sample_count = min(10, len(mappings))
    sample_mappings = mappings[:sample_count]
    
    for i, mapping in enumerate(sample_mappings, 1):
        print(f"\n{i}. \"{mapping.word}\" → {mapping.suggested_emojis}")
        print(f"   Category: {mapping.category}")
    
    print(f"\n💡 To save results, run without --dry-run flag")


def _display_summary(generator: SemanticMappingGenerator, mappings: List) -> None:
    """Display summary statistics for the generation process.
    
    Args:
        generator: Semantic mapping generator instance
        mappings: Generated mappings to analyze
    """
    analysis = generator.analyze_mappings(mappings)
    
    print(f"\n📊 Summary:")
    print(f"   • Total words processed: {analysis['total_mappings']}")
    print(f"   • Successful mappings: {analysis['successful_mappings']}")
    print(f"   • Success rate: {analysis['success_rate']:.1%}")
    
    # Display category breakdown if available
    if analysis['category_counts']:
        print(f"   • Category breakdown:")
        for category, count in analysis['category_counts'].items():
            print(f"     - {category}: {count}")


if __name__ == "__main__":
    exit(main())
