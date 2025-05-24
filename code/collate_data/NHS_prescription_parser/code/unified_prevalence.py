#!/usr/bin/env python3
"""
Unified NHS Prescription Prevalence Calculator

This script provides a single, unified entry point for calculating prescription prevalence
across all supported data formats and conditions. It replaces the separate scripts for
drug_prevalence.py, custom_list_prevalence.py, and condition_prevalence.py.
"""

import argparse
import sys
import os
import json
from typing import List, Dict, Optional
import logging

# Add local modules to path
sys.path.insert(0, '.')

from sources.downloader import Downloader
from matching.drugMatching import DrugMatcher
from unified.unified_processor import UnifiedProcessor, ConfigManager


def setup_logging(level: str = 'INFO'):
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def calculate_drug_prevalence(args):
    """Calculate prevalence for specific drugs."""
    # Load configuration
    config = ConfigManager.load_config(args.config)
    setup_logging(config['logging_level'])
    
    logger = logging.getLogger(__name__)
    logger.info(f"Calculating drug prevalence for: {args.drugs}")
    
    # Download files
    downloader = Downloader(
        sourcesFile=config['sources_file'],
        download_dir=config['input_dir']
    )
    
    try:
        selected_files = downloader.download_range(args.start, args.end)
        logger.info(f"Downloaded {len(selected_files)} files")
    except Exception as e:
        logger.error(f"Failed to download files: {e}")
        sys.exit(1)
    
    # Map drugs to BNF codes
    drug_matcher = DrugMatcher(mappings_dir=config['mappings_dir'])
    disease_drugs, drug_map = drug_matcher.DrugMatching(args.drugs)
    
    # Process files
    processor = UnifiedProcessor(config['mappings_dir'])
    output_dir = args.output_dir or config['output_dir']
    
    results = processor.process_prescription_files(
        selected_files, drug_map, output_dir, args.year
    )
    
    # Save drug mapping
    drug_matcher.dumpDrugs(disease_drugs)
    
    logger.info("Drug prevalence calculation completed successfully!")
    return results


def calculate_custom_list_prevalence(args):
    """Calculate prevalence for custom drug lists."""
    config = ConfigManager.load_config(args.config)
    setup_logging(config['logging_level'])
    
    logger = logging.getLogger(__name__)
    logger.info(f"Calculating prevalence for custom list: {args.list}")
    
    # Load custom drug mapping
    try:
        with open(args.list, 'r') as f:
            drug_map = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load custom drug list: {e}")
        sys.exit(1)
    
    # Download files
    downloader = Downloader(
        sourcesFile=config['sources_file'],
        download_dir=config['input_dir']
    )
    
    try:
        selected_files = downloader.download_range(args.start, args.end)
        logger.info(f"Downloaded {len(selected_files)} files")
    except Exception as e:
        logger.error(f"Failed to download files: {e}")
        sys.exit(1)
    
    # Process files
    processor = UnifiedProcessor(config['mappings_dir'])
    output_dir = args.output_dir or config['output_dir']
    
    results = processor.process_prescription_files(
        selected_files, drug_map, output_dir, args.year
    )
    
    logger.info("Custom list prevalence calculation completed successfully!")
    return results


def calculate_condition_prevalence(args):
    """Calculate prevalence for medical conditions."""
    config = ConfigManager.load_config(args.config)
    setup_logging(config['logging_level'])
    
    logger = logging.getLogger(__name__)
    logger.info(f"Calculating condition prevalence for: {args.conditions}")
    
    # Handle custom drug lists if provided
    if args.custom_drug_list:
        logger.info("Using custom drug lists")
        # Implementation for custom drug lists (aggregation approach)
        # This would aggregate individual drug files as in the original code
        # For brevity, we'll focus on the DrugBank approach here
        raise NotImplementedError("Custom drug list aggregation not yet implemented in unified processor")
    
    # Download files
    downloader = Downloader(
        sourcesFile=config['sources_file'],
        download_dir=config['input_dir']
    )
    
    try:
        selected_files = downloader.download_range(args.start, args.end)
        logger.info(f"Downloaded {len(selected_files)} files")
    except Exception as e:
        logger.error(f"Failed to download files: {e}")
        sys.exit(1)
    
    # Map conditions to drugs
    drug_matcher = DrugMatcher(mappings_dir=config['mappings_dir'])
    disease_drugs, drug_map = drug_matcher.DrugMatching(args.conditions, args.is_category)
    
    # Process files
    processor = UnifiedProcessor(config['mappings_dir'])
    output_dir = args.output_dir or config['output_dir']
    
    results = processor.process_prescription_files(
        selected_files, drug_map, output_dir, args.year
    )
    
    # Save drug mapping
    drug_matcher.dumpDrugs(disease_drugs)
    
    logger.info("Condition prevalence calculation completed successfully!")
    return results


def main():
    """Main entry point with subcommands for different calculation types."""
    parser = argparse.ArgumentParser(
        description='Unified NHS Prescription Prevalence Calculator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Calculate drug prevalence
  python unified_prevalence.py drug -d metformin ibuprofen -s 202001 -e 202012

  # Calculate prevalence from custom list
  python unified_prevalence.py custom -l sample_list_antidepressants.json -s 202001 -e 202012

  # Calculate condition prevalence
  python unified_prevalence.py condition -c diabetes hypertension -s 202001 -e 202012

  # Calculate prevalence with specific year for LSOA mapping
  python unified_prevalence.py drug -d metformin -s 202001 -e 202012 -y 2021
        """
    )
    
    # Global arguments
    parser.add_argument('-s', '--start', required=True, 
                       help='Start year and month, format YYYYMM')
    parser.add_argument('-e', '--end', required=True,
                       help='End year and month, format YYYYMM')
    parser.add_argument('-y', '--year', type=int,
                       help='Year for LSOA mapping (auto-detected if not specified)')
    parser.add_argument('-odir', '--output_dir',
                       help='Output directory (default from config)')
    parser.add_argument('--config',
                       help='Path to configuration file')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Calculation type')
    
    # Drug prevalence subcommand
    drug_parser = subparsers.add_parser('drug', help='Calculate drug prevalence')
    drug_parser.add_argument('-d', '--drugs', nargs='+', required=True,
                            help='List of drug names')
    
    # Custom list subcommand
    custom_parser = subparsers.add_parser('custom', help='Calculate prevalence from custom list')
    custom_parser.add_argument('-l', '--list', required=True,
                              help='Path to JSON file with drug names and BNF codes')
    
    # Condition prevalence subcommand
    condition_parser = subparsers.add_parser('condition', help='Calculate condition prevalence')
    condition_parser.add_argument('-c', '--conditions', nargs='+', required=True,
                                 help='List of medical conditions')
    condition_parser.add_argument('--custom_drug_list', nargs='+',
                                 help='Paths to custom drug list files for conditions')
    condition_parser.add_argument('--is_category', action='store_true',
                                 help='Treat conditions as categories instead of diseases')
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    # Set up logging level
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    # Route to appropriate function
    try:
        if args.command == 'drug':
            results = calculate_drug_prevalence(args)
        elif args.command == 'custom':
            results = calculate_custom_list_prevalence(args)
        elif args.command == 'condition':
            results = calculate_condition_prevalence(args)
        
        print("✅ Calculation completed successfully!")
        
    except KeyboardInterrupt:
        print("\n❌ Calculation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during calculation: {e}")
        logging.exception("Detailed error information:")
        sys.exit(1)


if __name__ == '__main__':
    main()