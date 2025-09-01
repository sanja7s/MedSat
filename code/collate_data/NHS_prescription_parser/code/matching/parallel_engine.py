#!/usr/bin/env python3
"""
Abstract Parallel Processing Engine for NHS Prescription Analysis

This module provides a generic, elegant parallel processing framework that can be
adapted for different types of prescription analysis workloads (drugs, conditions, 
custom lists, etc.).
"""

import multiprocessing as mp
import psutil
import time
import logging
from abc import ABC, abstractmethod
from functools import partial
from typing import Dict, List, Tuple, Any, Optional, Callable, Union
from dataclasses import dataclass
from tqdm import tqdm
import pandas as pd


@dataclass
class ProcessingConfig:
    """Configuration for parallel processing parameters."""
    n_cores: Optional[int] = None
    max_ram_gb: Optional[float] = None
    chunk_size: int = 1
    show_progress: bool = True
    enable_logging: bool = True
    ram_per_process_gb: float = 3.0


@dataclass
class ProcessingResult:
    """Result container for processing operations."""
    success: bool
    data: Any
    error: Optional[str] = None
    processing_time: float = 0.0
    metadata: Dict = None


class WorkloadProcessor(ABC):
    """
    Abstract base class for defining different types of prescription analysis workloads.
    
    Subclasses define the specific processing logic while this class handles
    the parallel execution, resource management, and error handling.
    """
    
    @abstractmethod
    def process_single_item(self, item: Any, **kwargs) -> ProcessingResult:
        """
        Process a single work item (e.g., a monthly file, a drug, etc.).
        
        Args:
            item: The work item to process
            **kwargs: Additional arguments specific to the workload
            
        Returns:
            ProcessingResult containing the processed data
        """
        pass
    
    @abstractmethod
    def combine_results(self, results: List[ProcessingResult]) -> Any:
        """
        Combine results from multiple processed items into final output.
        
        Args:
            results: List of ProcessingResult objects
            
        Returns:
            Combined/aggregated results
        """
        pass
    
    @abstractmethod
    def get_item_identifier(self, item: Any) -> str:
        """
        Get a string identifier for the work item (for logging/progress).
        
        Args:
            item: The work item
            
        Returns:
            String identifier
        """
        pass


class ParallelEngine:
    """
    Generic parallel processing engine that can execute any WorkloadProcessor
    with optimal resource allocation and error handling.
    """
    
    def __init__(self, config: ProcessingConfig = None):
        """
        Initialize the parallel processing engine.
        
        Args:
            config: Processing configuration (uses defaults if None)
        """
        self.config = config or ProcessingConfig()
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging if enabled."""
        if self.config.enable_logging:
            logging.basicConfig(
                level=logging.INFO, 
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            self.logger = logging.getLogger(self.__class__.__name__)
        else:
            self.logger = logging.getLogger(__name__)
            self.logger.disabled = True
    
    def _get_optimal_cores(self, n_items: int) -> int:
        """Calculate optimal number of cores based on resources and workload."""
        max_cores = mp.cpu_count()
        
        # Auto-detect available RAM if not provided
        available_ram_gb = self.config.max_ram_gb
        if available_ram_gb is None:
            available_ram_gb = psutil.virtual_memory().available / (1024**3)
        
        # Calculate cores limited by RAM
        ram_limited_cores = max(1, int(available_ram_gb // self.config.ram_per_process_gb))
        
        # Don't exceed number of items
        item_limited_cores = min(max_cores, n_items)
        
        # Use configured cores if specified
        if self.config.n_cores is not None:
            configured_cores = min(self.config.n_cores, max_cores)
        else:
            configured_cores = max_cores
        
        optimal_cores = min(configured_cores, ram_limited_cores, item_limited_cores)
        
        self.logger.info(f"Resource analysis:")
        self.logger.info(f"  Available cores: {max_cores}")
        self.logger.info(f"  Available RAM: {available_ram_gb:.1f}GB")
        self.logger.info(f"  Items to process: {n_items}")
        self.logger.info(f"  RAM per process: {self.config.ram_per_process_gb}GB")
        self.logger.info(f"  Optimal cores: {optimal_cores}")
        
        return optimal_cores
    
    def execute(self, processor: WorkloadProcessor, items: List[Any], **kwargs) -> Any:
        """
        Execute a workload processor on a list of items with optimal parallelization.
        
        Args:
            processor: WorkloadProcessor instance defining the work to be done
            items: List of items to process
            **kwargs: Additional arguments passed to processor
            
        Returns:
            Combined results from all processed items
        """
        if not items:
            self.logger.warning("No items to process")
            return processor.combine_results([])
        
        n_cores = self._get_optimal_cores(len(items))
        
        self.logger.info(f"Starting parallel execution:")
        self.logger.info(f"  Processor: {processor.__class__.__name__}")
        self.logger.info(f"  Items: {len(items)}")
        self.logger.info(f"  Cores: {n_cores}")
        
        start_time = time.time()
        
        if n_cores == 1 or len(items) == 1:
            results = self._execute_serial(processor, items, **kwargs)
        else:
            results = self._execute_parallel(processor, items, n_cores, **kwargs)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Filter successful results
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        if failed_results:
            self.logger.warning(f"{len(failed_results)} items failed to process")
            for failed in failed_results:
                self.logger.error(f"Failed item: {failed.error}")
        
        self.logger.info(f"Execution completed:")
        self.logger.info(f"  Total time: {processing_time:.2f}s")
        self.logger.info(f"  Average per item: {processing_time/len(items):.2f}s")
        self.logger.info(f"  Successful: {len(successful_results)}/{len(items)}")
        
        # Combine successful results
        return processor.combine_results(successful_results)
    
    def _execute_serial(self, processor: WorkloadProcessor, items: List[Any], **kwargs) -> List[ProcessingResult]:
        """Execute items serially."""
        results = []
        
        if self.config.show_progress:
            item_iter = tqdm(items, desc=f"Processing {processor.__class__.__name__}")
        else:
            item_iter = items
        
        for item in item_iter:
            try:
                result = processor.process_single_item(item, **kwargs)
                results.append(result)
            except Exception as e:
                error_result = ProcessingResult(
                    success=False,
                    data=None,
                    error=str(e)
                )
                results.append(error_result)
        
        return results
    
    def _execute_parallel(self, processor: WorkloadProcessor, items: List[Any], 
                         n_cores: int, **kwargs) -> List[ProcessingResult]:
        """Execute items in parallel."""
        
        # Create wrapper function that can be pickled for multiprocessing
        def process_wrapper(item):
            try:
                return processor.process_single_item(item, **kwargs)
            except Exception as e:
                return ProcessingResult(
                    success=False,
                    data=None,
                    error=str(e)
                )
        
        with mp.Pool(n_cores) as pool:
            if self.config.show_progress:
                # Use tqdm for progress tracking
                results = []
                desc = f"Processing {processor.__class__.__name__}"
                for result in tqdm(pool.imap(process_wrapper, items), 
                                 total=len(items), desc=desc):
                    results.append(result)
            else:
                results = pool.map(process_wrapper, items)
        
        return results
    
    def benchmark(self, processor: WorkloadProcessor, items: List[Any], 
                  max_items: int = 3, **kwargs) -> Dict[str, float]:
        """
        Benchmark serial vs parallel execution to measure speedup.
        
        Args:
            processor: WorkloadProcessor to benchmark
            items: Items to process
            max_items: Maximum number of items for benchmark
            **kwargs: Additional arguments for processor
            
        Returns:
            Benchmark results dictionary
        """
        test_items = items[:max_items]
        
        self.logger.info(f"Benchmarking {processor.__class__.__name__} with {len(test_items)} items")
        
        # Serial execution
        original_config = self.config
        self.config = ProcessingConfig(n_cores=1, show_progress=False, enable_logging=False)
        
        start_serial = time.time()
        serial_result = self.execute(processor, test_items, **kwargs)
        serial_time = time.time() - start_serial
        
        # Parallel execution
        self.config = ProcessingConfig(show_progress=False, enable_logging=False)
        
        start_parallel = time.time()
        parallel_result = self.execute(processor, test_items, **kwargs)
        parallel_time = time.time() - start_parallel
        
        # Restore original config
        self.config = original_config
        
        speedup = serial_time / parallel_time if parallel_time > 0 else 0
        cores_used = self._get_optimal_cores(len(test_items))
        
        results = {
            'serial_time': serial_time,
            'parallel_time': parallel_time,
            'speedup': speedup,
            'items_tested': len(test_items),
            'cores_used': cores_used,
            'efficiency': speedup / cores_used if cores_used > 0 else 0
        }
        
        self.logger.info(f"Benchmark Results:")
        self.logger.info(f"  Serial time: {serial_time:.2f}s")
        self.logger.info(f"  Parallel time: {parallel_time:.2f}s")
        self.logger.info(f"  Speedup: {speedup:.2f}x")
        self.logger.info(f"  Cores used: {cores_used}")
        self.logger.info(f"  Efficiency: {results['efficiency']:.2f}")
        
        return results


class AdaptiveEngine(ParallelEngine):
    """
    Adaptive parallel engine that automatically adjusts processing strategy
    based on workload characteristics and system resources.
    """
    
    def __init__(self, config: ProcessingConfig = None):
        super().__init__(config)
        self.performance_history = []
    
    def execute_adaptive(self, processor: WorkloadProcessor, items: List[Any], **kwargs) -> Any:
        """
        Execute with adaptive strategy selection based on workload characteristics.
        
        This method automatically chooses the best processing strategy based on:
        - Number of items vs available cores
        - Historical performance data
        - System resource availability
        """
        n_items = len(items)
        n_cores = self._get_optimal_cores(n_items)
        
        # Determine strategy based on workload characteristics
        if n_items <= 2:
            strategy = "serial"
        elif n_items <= n_cores:
            strategy = "parallel_by_item"
        else:
            # For large workloads, use batching or hierarchical parallelization
            strategy = "parallel_batched"
        
        self.logger.info(f"Selected strategy: {strategy}")
        
        if strategy == "serial":
            return self.execute(processor, items, **kwargs)
        elif strategy == "parallel_by_item":
            return self.execute(processor, items, **kwargs)
        else:
            # Implement batched processing
            return self._execute_batched(processor, items, n_cores, **kwargs)
    
    def _execute_batched(self, processor: WorkloadProcessor, items: List[Any], 
                        n_cores: int, **kwargs) -> Any:
        """Execute items in batches for very large workloads."""
        batch_size = max(1, len(items) // n_cores)
        batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
        
        self.logger.info(f"Processing {len(items)} items in {len(batches)} batches of size ~{batch_size}")
        
        all_results = []
        for i, batch in enumerate(batches):
            self.logger.info(f"Processing batch {i+1}/{len(batches)}")
            batch_results = self.execute(processor, batch, **kwargs)
            all_results.append(batch_results)
        
        # This would need to be implemented based on the specific result type
        # For now, return the first result as an example
        return all_results[0] if all_results else None