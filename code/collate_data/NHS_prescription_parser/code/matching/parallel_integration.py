#!/usr/bin/env python3
"""
Integration module for parallel processing with existing NHS prescription scripts.

This module provides easy-to-use functions that integrate the parallel processing
engine with the existing drug_prevalence.py, condition_prevalence.py, etc.
"""

import multiprocessing as mp
from typing import Dict, List, Tuple, Optional
from .parallel_engine import ParallelEngine, ProcessingConfig
from .workload_processors import MonthlyFileProcessor, HierarchicalProcessor, BatchedFileProcessor


def parallel_drug_prevalence(files_sub: List[str], 
                           drug_map: Dict[str, List[str]], 
                           mappings_dir: str = './mappings/',
                           n_cores: Optional[int] = None,
                           max_ram_gb: Optional[float] = None,
                           show_progress: bool = True,
                           strategy: str = 'auto') -> Tuple[Dict, Dict, Dict, Dict]:
    """
    Compute drug prevalence across multiple files with parallel processing.
    
    Args:
        files_sub: List of file paths to process
        drug_map: Dictionary mapping drug names to BNF codes
        mappings_dir: Directory containing mapping files
        n_cores: Number of cores to use (None = auto-detect, 0 = max available)
        max_ram_gb: Maximum RAM to use in GB (None = auto-detect)
        show_progress: Whether to show progress bars
        strategy: Processing strategy ('auto', 'file_parallel', 'hierarchical', 'batched')
    
    Returns:
        Tuple of (monthly_quantity, monthly_costs, monthly_dosage, monthly_items)
    """
    
    # Handle core configuration
    if n_cores == 0 or n_cores is None:
        n_cores = mp.cpu_count()  # Use all available cores
    
    # Create processing configuration
    config = ProcessingConfig(
        n_cores=n_cores,
        max_ram_gb=max_ram_gb,
        show_progress=show_progress,
        enable_logging=True
    )
    
    # Create parallel engine
    engine = ParallelEngine(config)
    
    # Select processing strategy
    if strategy == 'auto':
        strategy = _select_optimal_strategy(len(files_sub), len(drug_map), n_cores)
    
    # Create appropriate processor
    if strategy == 'file_parallel':
        processor = MonthlyFileProcessor(drug_map, mappings_dir)
        
    elif strategy == 'hierarchical':
        processor = HierarchicalProcessor(drug_map, mappings_dir)
        
    elif strategy == 'batched':
        # Calculate optimal batch size based on available RAM
        batch_size = _calculate_batch_size(n_cores, max_ram_gb)
        file_batches = [files_sub[i:i + batch_size] for i in range(0, len(files_sub), batch_size)]
        processor = BatchedFileProcessor(drug_map, mappings_dir, batch_size)
        return engine.execute(processor, file_batches)
        
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    
    # Execute processing
    return engine.execute(processor, files_sub)


def parallel_condition_prevalence(files_sub: List[str], 
                                condition_drugs: Dict[str, List[str]], 
                                mappings_dir: str = './mappings/',
                                n_cores: Optional[int] = None,
                                max_ram_gb: Optional[float] = None,
                                show_progress: bool = True,
                                strategy: str = 'auto') -> Tuple[Dict, Dict, Dict, Dict]:
    """
    Compute condition prevalence across multiple files with parallel processing.
    
    This is essentially the same as drug prevalence but organized by condition.
    
    Args:
        files_sub: List of file paths to process
        condition_drugs: Dictionary mapping condition names to BNF codes
        mappings_dir: Directory containing mapping files
        n_cores: Number of cores to use (None = auto-detect, 0 = max available)
        max_ram_gb: Maximum RAM to use in GB (None = auto-detect)
        show_progress: Whether to show progress bars
        strategy: Processing strategy ('auto', 'file_parallel', 'hierarchical', 'batched')
    
    Returns:
        Tuple of (monthly_quantity, monthly_costs, monthly_dosage, monthly_items)
    """
    return parallel_drug_prevalence(files_sub, condition_drugs, mappings_dir, 
                                  n_cores, max_ram_gb, show_progress, strategy)


def benchmark_processing(files_sub: List[str], 
                        drug_map: Dict[str, List[str]], 
                        mappings_dir: str = './mappings/',
                        max_test_files: int = 3) -> Dict[str, any]:
    """
    Benchmark different processing strategies to find the optimal approach.
    
    Args:
        files_sub: List of file paths to process
        drug_map: Dictionary mapping drug names to BNF codes
        mappings_dir: Directory containing mapping files
        max_test_files: Maximum number of files to use for benchmarking
    
    Returns:
        Dictionary with benchmark results for different strategies
    """
    test_files = files_sub[:max_test_files]
    results = {}
    
    strategies = ['file_parallel', 'hierarchical']
    if len(test_files) > 6:
        strategies.append('batched')
    
    print(f"Benchmarking {len(strategies)} strategies with {len(test_files)} files...")
    
    for strategy in strategies:
        print(f"\nTesting strategy: {strategy}")
        
        config = ProcessingConfig(show_progress=False, enable_logging=False)
        engine = ParallelEngine(config)
        
        if strategy == 'file_parallel':
            processor = MonthlyFileProcessor(drug_map, mappings_dir)
        elif strategy == 'hierarchical':
            processor = HierarchicalProcessor(drug_map, mappings_dir)
        elif strategy == 'batched':
            processor = BatchedFileProcessor(drug_map, mappings_dir, batch_size=2)
            test_files = [test_files]  # Wrap in batch
        
        bench_results = engine.benchmark(processor, test_files, max_test_files)
        results[strategy] = bench_results
    
    # Find best strategy
    best_strategy = min(results.keys(), key=lambda s: results[s]['parallel_time'])
    results['recommended_strategy'] = best_strategy
    
    print(f"\nBenchmark Summary:")
    for strategy, bench in results.items():
        if strategy != 'recommended_strategy':
            print(f"  {strategy}: {bench['parallel_time']:.2f}s ({bench['speedup']:.2f}x speedup)")
    print(f"\nRecommended strategy: {best_strategy}")
    
    return results


def _select_optimal_strategy(n_files: int, n_drugs: int, n_cores: int) -> str:
    """
    Automatically select the optimal processing strategy based on workload characteristics.
    
    Args:
        n_files: Number of files to process
        n_drugs: Number of drugs/conditions
        n_cores: Number of available cores
    
    Returns:
        Recommended strategy name
    """
    # Decision logic based on workload characteristics
    if n_files <= 2:
        return 'file_parallel'  # Simple case
    
    elif n_files <= n_cores:
        return 'file_parallel'  # Files fit within cores
    
    elif n_drugs > 4 and n_files > n_cores:
        return 'hierarchical'  # Both files and drugs can be parallelized
    
    elif n_files > n_cores * 2:
        return 'batched'  # Too many files, use batching
    
    else:
        return 'file_parallel'  # Default


def _calculate_batch_size(n_cores: int, max_ram_gb: Optional[float]) -> int:
    """
    Calculate optimal batch size for batched processing.
    
    Args:
        n_cores: Number of available cores
        max_ram_gb: Maximum RAM available (None for auto-detect)
    
    Returns:
        Optimal batch size
    """
    if max_ram_gb is None:
        import psutil
        max_ram_gb = psutil.virtual_memory().available / (1024**3)
    
    # Estimate 3GB per file, with some buffer
    safe_ram_gb = max_ram_gb * 0.8  # Use 80% of available RAM
    max_concurrent_files = max(1, int(safe_ram_gb // 3))
    
    # Batch size should be multiple of cores for efficiency
    batch_size = min(max_concurrent_files, n_cores * 2)
    
    return max(1, batch_size)


def get_processing_info(n_files: int = None, n_drugs: int = None) -> Dict[str, any]:
    """
    Get information about processing capabilities and recommendations.
    
    Args:
        n_files: Number of files to process (optional)
        n_drugs: Number of drugs/conditions (optional)
    
    Returns:
        Dictionary with processing information
    """
    import psutil
    
    n_cores = mp.cpu_count()
    available_ram_gb = psutil.virtual_memory().available / (1024**3)
    total_ram_gb = psutil.virtual_memory().total / (1024**3)
    
    info = {
        'system': {
            'cpu_cores': n_cores,
            'total_ram_gb': total_ram_gb,
            'available_ram_gb': available_ram_gb,
            'ram_usage_percent': (1 - available_ram_gb/total_ram_gb) * 100
        },
        'recommendations': {
            'max_cores_safe': n_cores,
            'max_cores_ram_limited': max(1, int(available_ram_gb // 3)),
            'estimated_ram_per_process_gb': 3.0
        }
    }
    
    if n_files is not None and n_drugs is not None:
        strategy = _select_optimal_strategy(n_files, n_drugs, n_cores)
        batch_size = _calculate_batch_size(n_cores, available_ram_gb)
        
        info['workload'] = {
            'files': n_files,
            'drugs': n_drugs,
            'recommended_strategy': strategy,
            'optimal_batch_size': batch_size,
            'estimated_speedup': min(n_cores, n_files) * 0.8  # Conservative estimate
        }
    
    return info


# Convenience function for CLI integration
def print_processing_info(n_files: int = None, n_drugs: int = None):
    """Print processing information in a user-friendly format."""
    info = get_processing_info(n_files, n_drugs)
    
    print("🖥️  System Resources:")
    print(f"   CPU Cores: {info['system']['cpu_cores']}")
    print(f"   Total RAM: {info['system']['total_ram_gb']:.1f}GB")
    print(f"   Available RAM: {info['system']['available_ram_gb']:.1f}GB")
    
    print("\n⚙️  Processing Recommendations:")
    print(f"   Safe max cores: {info['recommendations']['max_cores_safe']}")
    print(f"   RAM-limited cores: {info['recommendations']['max_cores_ram_limited']}")
    
    if 'workload' in info:
        print(f"\n📊 Workload Analysis:")
        print(f"   Files to process: {info['workload']['files']}")
        print(f"   Drugs/conditions: {info['workload']['drugs']}")
        print(f"   Recommended strategy: {info['workload']['recommended_strategy']}")
        print(f"   Estimated speedup: {info['workload']['estimated_speedup']:.1f}x")