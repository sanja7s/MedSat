#!/usr/bin/env python3
"""
Parallel processing module for NHS prescription prevalence calculation.

This module provides optimized parallel processing capabilities for computing
drug and condition prevalences across multiple monthly files simultaneously.
"""

import multiprocessing as mp
import psutil
import time
from functools import partial
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np
from tqdm import tqdm
import logging

# Import existing functions
from .commonFunc_updated import detect_file_format, calculateTemporalMetrics_LSOA
from .commonFunc import calculateTemporalMetrics_LSOA as calculateTemporalMetrics_LSOA_old


def get_optimal_cores(n_files: int, available_ram_gb: Optional[float] = None) -> int:
    """
    Determine optimal number of cores based on files, CPU cores, and available RAM.
    
    Args:
        n_files: Number of files to process
        available_ram_gb: Available RAM in GB (auto-detected if None)
    
    Returns:
        Optimal number of cores to use
    """
    max_cores = mp.cpu_count()
    
    # Auto-detect available RAM if not provided
    if available_ram_gb is None:
        available_ram_gb = psutil.virtual_memory().available / (1024**3)
    
    # Estimate 3GB per process (conservative estimate)
    # Each process needs: ~1GB for DataFrame + ~1GB for processing + ~1GB buffer
    ram_limited_cores = max(1, int(available_ram_gb // 3))
    
    # Don't exceed number of files (no point in more processes than files)
    file_limited_cores = min(max_cores, n_files)
    
    optimal_cores = min(max_cores, ram_limited_cores, file_limited_cores)
    
    logging.info(f"Resource analysis:")
    logging.info(f"  Available cores: {max_cores}")
    logging.info(f"  Available RAM: {available_ram_gb:.1f}GB")
    logging.info(f"  Files to process: {n_files}")
    logging.info(f"  Optimal cores: {optimal_cores}")
    
    return optimal_cores


def process_month_file(file_path: str, drugMap: Dict[str, List[str]], 
                      mappings_dir: str, use_old_format: bool = False) -> Tuple[str, Dict]:
    """
    Process a single monthly prescription file with all drugs.
    
    This function is designed to be called in parallel for different monthly files.
    Each process handles one file completely independently.
    
    Args:
        file_path: Path to the monthly prescription file (.gz)
        drugMap: Dictionary mapping drug names to BNF codes
        mappings_dir: Directory containing mapping files
        use_old_format: Whether to force old format processing
    
    Returns:
        Tuple of (month, results_dict) where results_dict contains all drug results
    """
    try:
        # Extract month from filename
        month = file_path.split('/')[-1].split('.')[0]
        
        # Load the monthly prescription data
        pdp = pd.read_csv(file_path, compression='gzip')
        
        # Detect file format if not specified
        if not use_old_format:
            fields = detect_file_format(pdp)
            bnf_field = fields['bnfField']
            old = (fields['format'] == 'old')
        else:
            bnf_field = 'BNF_CODE'
            old = True
        
        # Process all drugs for this month
        month_results = {
            'dosage': {},
            'costs': {},
            'quantity': {},
            'items': {}
        }
        
        for drugname, drugs in drugMap.items():
            # Filter prescriptions for this drug
            drug_prescriptions = pdp.loc[pdp[bnf_field].isin(drugs)]
            
            if len(drug_prescriptions) > 0:
                # Calculate LSOA metrics for this drug
                if old:
                    quantity, costs, dosage, items = calculateTemporalMetrics_LSOA_old(
                        drug_prescriptions, mappings_dir=mappings_dir, old=old
                    )
                else:
                    quantity, costs, dosage, items = calculateTemporalMetrics_LSOA(
                        drug_prescriptions, mappings_dir=mappings_dir, old=old
                    )
                
                month_results['quantity'][drugname] = quantity
                month_results['costs'][drugname] = costs
                month_results['dosage'][drugname] = dosage
                month_results['items'][drugname] = items
            else:
                # No prescriptions found for this drug in this month
                month_results['quantity'][drugname] = {}
                month_results['costs'][drugname] = {}
                month_results['dosage'][drugname] = {}
                month_results['items'][drugname] = {}
        
        return month, month_results
        
    except Exception as e:
        logging.error(f"Error processing file {file_path}: {str(e)}")
        return file_path.split('/')[-1].split('.')[0], None


def parallel_drug_prevalence(files_sub: List[str], drugMap: Dict[str, List[str]], 
                           mappings_dir: str, n_cores: Optional[int] = None,
                           show_progress: bool = True) -> Tuple[Dict, Dict, Dict, Dict]:
    """
    Process multiple monthly prescription files in parallel.
    
    Args:
        files_sub: List of file paths to process
        drugMap: Dictionary mapping drug names to BNF codes
        mappings_dir: Directory containing mapping files
        n_cores: Number of cores to use (auto-detected if None)
        show_progress: Whether to show progress bars
    
    Returns:
        Tuple of (monthly_quantity, monthly_costs, monthly_dosage, monthly_items)
        Each is a nested dict: {month: {drug: {lsoa: value}}}
    """
    if n_cores is None:
        n_cores = get_optimal_cores(len(files_sub))
    
    logging.info(f"Starting parallel processing with {n_cores} cores for {len(files_sub)} files")
    
    # Initialize result dictionaries
    monthly_borough_quantity_new = {}
    monthly_borough_costs_new = {}
    monthly_borough_dosage_new = {}
    monthly_borough_items_new = {}
    
    start_time = time.time()
    
    if n_cores == 1 or len(files_sub) == 1:
        # Serial processing for single core or single file
        if show_progress:
            file_iter = tqdm(files_sub, desc="Processing files")
        else:
            file_iter = files_sub
            
        for f in file_iter:
            month, month_results = process_month_file(f, drugMap, mappings_dir)
            if month_results is not None:
                monthly_borough_quantity_new[month] = month_results['quantity']
                monthly_borough_costs_new[month] = month_results['costs']
                monthly_borough_dosage_new[month] = month_results['dosage']
                monthly_borough_items_new[month] = month_results['items']
    else:
        # Parallel processing
        with mp.Pool(n_cores) as pool:
            # Create partial function with fixed arguments
            process_func = partial(process_month_file, 
                                 drugMap=drugMap, 
                                 mappings_dir=mappings_dir)
            
            # Process files in parallel
            if show_progress:
                # Use tqdm for progress tracking
                results = []
                for result in tqdm(pool.imap(process_func, files_sub), 
                                 total=len(files_sub), desc="Processing files"):
                    results.append(result)
            else:
                results = pool.map(process_func, files_sub)
        
        # Merge results from all processes
        for month, month_results in results:
            if month_results is not None:
                monthly_borough_quantity_new[month] = month_results['quantity']
                monthly_borough_costs_new[month] = month_results['costs']
                monthly_borough_dosage_new[month] = month_results['dosage']
                monthly_borough_items_new[month] = month_results['items']
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    logging.info(f"Parallel processing completed in {processing_time:.2f} seconds")
    logging.info(f"Average time per file: {processing_time/len(files_sub):.2f} seconds")
    logging.info(f"Processed {len(files_sub)} files with {len(drugMap)} drugs")
    
    return (monthly_borough_quantity_new, monthly_borough_costs_new, 
            monthly_borough_dosage_new, monthly_borough_items_new)


def parallel_condition_prevalence(files_sub: List[str], condition_drugs: Dict[str, List[str]], 
                                 mappings_dir: str, n_cores: Optional[int] = None,
                                 show_progress: bool = True) -> Tuple[Dict, Dict, Dict, Dict]:
    """
    Process multiple monthly files for condition prevalence in parallel.
    
    This is a wrapper around parallel_drug_prevalence for condition analysis.
    
    Args:
        files_sub: List of file paths to process
        condition_drugs: Dictionary mapping condition names to BNF codes
        mappings_dir: Directory containing mapping files
        n_cores: Number of cores to use (auto-detected if None)
        show_progress: Whether to show progress bars
    
    Returns:
        Same as parallel_drug_prevalence but organized by condition
    """
    return parallel_drug_prevalence(files_sub, condition_drugs, mappings_dir, 
                                  n_cores, show_progress)


def benchmark_parallel_vs_serial(files_sub: List[str], drugMap: Dict[str, List[str]], 
                                mappings_dir: str, max_files: int = 3) -> Dict[str, float]:
    """
    Benchmark parallel vs serial processing to measure speedup.
    
    Args:
        files_sub: List of file paths to process
        drugMap: Dictionary mapping drug names to BNF codes  
        mappings_dir: Directory containing mapping files
        max_files: Maximum number of files to use for benchmark
    
    Returns:
        Dictionary with timing results and speedup factor
    """
    # Limit files for benchmark
    test_files = files_sub[:max_files]
    
    print(f"Benchmarking with {len(test_files)} files...")
    
    # Serial processing
    print("Running serial processing...")
    start_serial = time.time()
    serial_results = parallel_drug_prevalence(test_files, drugMap, mappings_dir, 
                                            n_cores=1, show_progress=False)
    serial_time = time.time() - start_serial
    
    # Parallel processing
    print("Running parallel processing...")
    start_parallel = time.time()
    parallel_results = parallel_drug_prevalence(test_files, drugMap, mappings_dir, 
                                               n_cores=None, show_progress=False)
    parallel_time = time.time() - start_parallel
    
    speedup = serial_time / parallel_time if parallel_time > 0 else 0
    
    results = {
        'serial_time': serial_time,
        'parallel_time': parallel_time,
        'speedup': speedup,
        'files_tested': len(test_files),
        'cores_used': get_optimal_cores(len(test_files))
    }
    
    print(f"\nBenchmark Results:")
    print(f"  Serial time: {serial_time:.2f}s")
    print(f"  Parallel time: {parallel_time:.2f}s") 
    print(f"  Speedup: {speedup:.2f}x")
    print(f"  Cores used: {results['cores_used']}")
    
    return results


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')