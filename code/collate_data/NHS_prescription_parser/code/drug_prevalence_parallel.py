#!/usr/bin/env python3
"""
Enhanced drug prevalence calculation with parallel processing support.

This module provides the same functionality as drug_prevalence.py but with
optional parallel processing capabilities for significant performance improvements.
"""

import argparse
import glob
import pandas as pd
import sys
import time
import multiprocessing as mp
from matching.utils import *
from matching.drugMatching import DrugMatcher
from sources.downloader import Downloader
from tqdm import tqdm
from matching.commonFunc import writeResultFiles, calculateTemporalMetrics_LSOA
from matching.commonFunc_updated import detect_file_format

# Import parallel processing components
from matching.parallel_integration import (
    parallel_drug_prevalence, 
    benchmark_processing, 
    print_processing_info
)


def add_parallel_arguments(parser):
    """Add parallel processing arguments to an argument parser."""
    parallel_group = parser.add_argument_group('Parallel Processing Options')
    parallel_group.add_argument('--cores', type=int, default=None,
                               help='Number of CPU cores to use (default: all available, 0 = max)')
    parallel_group.add_argument('--serial', action='store_true',
                               help='Force serial processing (disable parallelization)')
    parallel_group.add_argument('--benchmark', action='store_true',
                               help='Run benchmark comparing serial vs parallel performance')
    parallel_group.add_argument('--strategy', choices=['auto', 'file_parallel', 'hierarchical', 'batched'],
                               default='auto', help='Parallelization strategy (default: auto)')
    parallel_group.add_argument('--max-ram', type=float, default=None,
                               help='Maximum RAM to use in GB (default: auto-detect)')
    parallel_group.add_argument('--info', action='store_true',
                               help='Show system resources and processing recommendations')


def main():
    parser = argparse.ArgumentParser(description='Enhanced NHS Drug Prevalence Calculator with Parallel Processing')
    parser.add_argument('-d', '--drugs', nargs="+", 
                       help="List of drug names for prescription prevalence calculation")
    parser.add_argument('-s', "--start", help="Start year and month, format YYYYMM")
    parser.add_argument('-e', "--end", help="End year and month, format YYYYMM")
    parser.add_argument('-odir', "--output_dir", 
                       help="Directory for output files (default: ../data_prep/)")
    
    # Add parallel processing arguments
    add_parallel_arguments(parser)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    
    # Handle info request
    if args.info:
        print("🖥️ NHS Prescription Parser - System Information")
        print("=" * 50)
        print_processing_info()
        return

    # Validate required arguments
    if not args.drugs or not args.start or not args.end:
        print("❌ Error: --drugs, --start, and --end arguments are required")
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Setup directories
    input_dir = "./prescriptionfiles/"
    output_dir = args.output_dir or "../data_prep/"
    
    drug_list = args.drugs
    start = str(args.start)
    end = str(args.end)
    
    print(f"🏥 NHS Drug Prevalence Analysis (Enhanced)")
    print(f"==========================================")
    print(f"Drugs: {drug_list}")
    print(f"Period: {start} to {end}")
    print(f"Output: {output_dir}")
    
    # Configure parallel processing
    n_cores = args.cores
    if n_cores == 0:
        n_cores = mp.cpu_count()
    
    if args.serial:
        n_cores = 1
        print(f"Processing: Serial (1 core)")
    elif n_cores:
        print(f"Processing: Parallel ({n_cores} cores)")
    else:
        print(f"Processing: Parallel (auto-detect cores)")
    
    print()

    # Download files
    print("📥 Downloading prescription files...")
    downloader = Downloader(sourcesFile="sources/serialized_file_paths.json", download_dir=input_dir)
    
    try:
        selected_files = downloader.download_range(start, end)
    except Exception as e:
        print(f"❌ Download failed: {e}")
        # Try to find existing files
        selected_files = []
        for yyyymm in generate_date_range(start, end):
            file_path = f"{input_dir}{yyyymm}.gz"
            if os.path.exists(file_path):
                selected_files.append(file_path)
        
        if not selected_files:
            print(f"❌ No files found for period {start} to {end}")
            sys.exit(1)
        else:
            print(f"⚠️ Using existing files: {len(selected_files)} found")

    print("Finished download process")
    print(f"📁 Processing {len(selected_files)} files")
    
    # Create drug mapping
    print("🔍 Creating drug mapping...")
    drug_matcher = DrugMatcher()
    drug_map = {}
    
    for drug in drug_list:
        drug_match_result = drug_matcher.get_drugs_for_disease(drug)
        if drug_match_result:
            drug_map[drug] = drug_match_result
        else:
            print(f"⚠️ No BNF codes found for drug: {drug}")
            drug_map[drug] = []
    
    print(f"📊 Drug mapping created: {len(drug_map)} drugs")
    for drug, codes in drug_map.items():
        print(f"  {drug}: {len(codes)} BNF codes")

    # Run benchmark if requested
    if args.benchmark:
        print("\n🏃 Running performance benchmark...")
        benchmark_results = benchmark_processing(
            selected_files, drug_map, './mappings/', max_test_files=min(3, len(selected_files))
        )
        print(f"\n✅ Benchmark completed. Recommended strategy: {benchmark_results.get('recommended_strategy', 'file_parallel')}")
    
    # Main processing
    print(f"\n🚀 Starting prevalence calculation...")
    start_time = time.time()
    
    if args.serial or n_cores == 1:
        # Use original serial processing
        print("Using serial processing...")
        from drug_prevalence import main as original_main
        # This would require modifying the original script
        # For now, we'll use the parallel processor with 1 core
        results = parallel_drug_prevalence(
            selected_files, drug_map, './mappings/',
            n_cores=1, show_progress=True, strategy='auto'
        )
    else:
        # Use parallel processing
        print(f"Using parallel processing with {n_cores or 'auto'} cores...")
        results = parallel_drug_prevalence(
            selected_files, drug_map, './mappings/',
            n_cores=n_cores, max_ram_gb=args.max_ram,
            show_progress=True, strategy=args.strategy
        )
    
    processing_time = time.time() - start_time
    
    # Unpack results
    monthly_quantity, monthly_costs, monthly_dosage, monthly_items = results
    
    print(f"\n✅ Processing completed in {processing_time:.2f} seconds")
    print(f"📊 Processed {len(selected_files)} files with {len(drug_list)} drugs")
    
    # Write output files
    print("💾 Writing result files...")
    writeResultFiles(
        monthly_quantity, monthly_dosage, monthly_costs, monthly_items,
        drug_list, output_dir, './mappings/', isOld=False
    )
    
    print(f"🎉 Analysis complete! Results saved to {output_dir}")
    
    # Performance summary
    avg_time_per_file = processing_time / len(selected_files)
    print(f"\n📈 Performance Summary:")
    print(f"   Total time: {processing_time:.2f}s")
    print(f"   Average per file: {avg_time_per_file:.2f}s")
    print(f"   Files processed: {len(selected_files)}")
    print(f"   Drugs analyzed: {len(drug_list)}")
    
    if not args.serial and len(selected_files) > 1:
        theoretical_serial_time = avg_time_per_file * len(selected_files)
        if theoretical_serial_time > processing_time:
            speedup = theoretical_serial_time / processing_time
            print(f"   Estimated speedup: {speedup:.2f}x")


def generate_date_range(start_yyyymm, end_yyyymm):
    """Generate list of YYYYMM strings between start and end dates."""
    import datetime
    
    start_year = int(start_yyyymm[:4])
    start_month = int(start_yyyymm[4:6])
    end_year = int(end_yyyymm[:4])
    end_month = int(end_yyyymm[4:6])
    
    dates = []
    current_year = start_year
    current_month = start_month
    
    while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
        dates.append(f"{current_year:04d}{current_month:02d}")
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1
    
    return dates


if __name__ == '__main__':
    main()