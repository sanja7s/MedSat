#!/usr/bin/env python3
"""
Concrete WorkloadProcessor implementations for NHS prescription analysis.

This module contains specific processors for different types of prescription
analysis workloads that can be executed with the ParallelEngine.
"""

import pandas as pd
import time
from typing import Dict, List, Tuple, Any
from .parallel_engine import WorkloadProcessor, ProcessingResult
from .commonFunc_updated import detect_file_format, calculateTemporalMetrics_LSOA
from .commonFunc import calculateTemporalMetrics_LSOA as calculateTemporalMetrics_LSOA_old


class MonthlyFileProcessor(WorkloadProcessor):
    """
    Processor for analyzing monthly prescription files.
    
    Each work item is a file path, and the processor computes prevalence
    for all specified drugs/conditions within that month.
    """
    
    def __init__(self, drug_map: Dict[str, List[str]], mappings_dir: str):
        """
        Initialize the monthly file processor.
        
        Args:
            drug_map: Dictionary mapping drug/condition names to BNF codes
            mappings_dir: Directory containing mapping files
        """
        self.drug_map = drug_map
        self.mappings_dir = mappings_dir
    
    def process_single_item(self, file_path: str, **kwargs) -> ProcessingResult:
        """
        Process a single monthly prescription file.
        
        Args:
            file_path: Path to the monthly prescription file (.gz)
            **kwargs: Additional arguments (force_old_format, etc.)
            
        Returns:
            ProcessingResult containing the month's data for all drugs
        """
        start_time = time.time()
        
        try:
            # Extract month from filename
            month = file_path.split('/')[-1].split('.')[0]
            
            # Load the monthly prescription data
            pdp = pd.read_csv(file_path, compression='gzip')
            
            # Detect file format
            force_old = kwargs.get('force_old_format', False)
            if not force_old:
                fields = detect_file_format(pdp)
                bnf_field = fields['bnfField']
                old = (fields['format'] == 'old')
            else:
                bnf_field = 'BNF_CODE'
                old = True
            
            # Process all drugs/conditions for this month
            month_results = {
                'dosage': {},
                'costs': {},
                'quantity': {},
                'items': {}
            }
            
            for drug_name, bnf_codes in self.drug_map.items():
                # Filter prescriptions for this drug/condition
                drug_prescriptions = pdp.loc[pdp[bnf_field].isin(bnf_codes)]
                
                if len(drug_prescriptions) > 0:
                    # Calculate LSOA metrics
                    if old:
                        quantity, costs, dosage, items = calculateTemporalMetrics_LSOA_old(
                            drug_prescriptions, mappings_dir=self.mappings_dir, old=old
                        )
                    else:
                        quantity, costs, dosage, items = calculateTemporalMetrics_LSOA(
                            drug_prescriptions, mappings_dir=self.mappings_dir, old=old
                        )
                    
                    month_results['quantity'][drug_name] = quantity
                    month_results['costs'][drug_name] = costs
                    month_results['dosage'][drug_name] = dosage
                    month_results['items'][drug_name] = items
                else:
                    # No prescriptions found for this drug in this month
                    month_results['quantity'][drug_name] = {}
                    month_results['costs'][drug_name] = {}
                    month_results['dosage'][drug_name] = {}
                    month_results['items'][drug_name] = {}
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                data=(month, month_results),
                processing_time=processing_time,
                metadata={'file_path': file_path, 'month': month, 'drugs_processed': len(self.drug_map)}
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return ProcessingResult(
                success=False,
                data=None,
                error=f"Error processing {file_path}: {str(e)}",
                processing_time=processing_time
            )
    
    def combine_results(self, results: List[ProcessingResult]) -> Tuple[Dict, Dict, Dict, Dict]:
        """
        Combine results from multiple monthly files.
        
        Args:
            results: List of ProcessingResult objects from monthly file processing
            
        Returns:
            Tuple of (monthly_quantity, monthly_costs, monthly_dosage, monthly_items)
        """
        monthly_quantity = {}
        monthly_costs = {}
        monthly_dosage = {}
        monthly_items = {}
        
        for result in results:
            if result.success and result.data is not None:
                month, month_data = result.data
                monthly_quantity[month] = month_data['quantity']
                monthly_costs[month] = month_data['costs']
                monthly_dosage[month] = month_data['dosage']
                monthly_items[month] = month_data['items']
        
        return monthly_quantity, monthly_costs, monthly_dosage, monthly_items
    
    def get_item_identifier(self, file_path: str) -> str:
        """Get identifier for a file path."""
        return file_path.split('/')[-1].split('.')[0]  # Return month


class DrugWithinMonthProcessor(WorkloadProcessor):
    """
    Processor for analyzing different drugs within a single monthly file.
    
    Each work item is a (drug_name, bnf_codes) tuple, and the processor
    computes prevalence for that specific drug within the loaded DataFrame.
    """
    
    def __init__(self, monthly_data: pd.DataFrame, mappings_dir: str, old_format: bool = False):
        """
        Initialize the drug-within-month processor.
        
        Args:
            monthly_data: Pre-loaded monthly prescription DataFrame
            mappings_dir: Directory containing mapping files
            old_format: Whether using old data format
        """
        self.monthly_data = monthly_data
        self.mappings_dir = mappings_dir
        self.old_format = old_format
        
        # Detect BNF field
        if not old_format:
            fields = detect_file_format(monthly_data)
            self.bnf_field = fields['bnfField']
        else:
            self.bnf_field = 'BNF_CODE'
    
    def process_single_item(self, drug_info: Tuple[str, List[str]], **kwargs) -> ProcessingResult:
        """
        Process a single drug within the monthly data.
        
        Args:
            drug_info: Tuple of (drug_name, bnf_codes)
            **kwargs: Additional arguments
            
        Returns:
            ProcessingResult containing the drug's LSOA metrics
        """
        start_time = time.time()
        
        try:
            drug_name, bnf_codes = drug_info
            
            # Filter prescriptions for this drug
            drug_prescriptions = self.monthly_data.loc[self.monthly_data[self.bnf_field].isin(bnf_codes)]
            
            if len(drug_prescriptions) > 0:
                # Calculate LSOA metrics
                if self.old_format:
                    quantity, costs, dosage, items = calculateTemporalMetrics_LSOA_old(
                        drug_prescriptions, mappings_dir=self.mappings_dir, old=True
                    )
                else:
                    quantity, costs, dosage, items = calculateTemporalMetrics_LSOA(
                        drug_prescriptions, mappings_dir=self.mappings_dir, old=False
                    )
                
                result_data = {
                    'quantity': quantity,
                    'costs': costs,
                    'dosage': dosage,
                    'items': items
                }
            else:
                # No prescriptions found
                result_data = {
                    'quantity': {},
                    'costs': {},
                    'dosage': {},
                    'items': {}
                }
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                data=(drug_name, result_data),
                processing_time=processing_time,
                metadata={'drug_name': drug_name, 'prescriptions_found': len(drug_prescriptions)}
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return ProcessingResult(
                success=False,
                data=None,
                error=f"Error processing drug {drug_info[0]}: {str(e)}",
                processing_time=processing_time
            )
    
    def combine_results(self, results: List[ProcessingResult]) -> Dict[str, Dict]:
        """
        Combine results from multiple drugs.
        
        Args:
            results: List of ProcessingResult objects from drug processing
            
        Returns:
            Dictionary with combined drug results
        """
        combined = {
            'quantity': {},
            'costs': {},
            'dosage': {},
            'items': {}
        }
        
        for result in results:
            if result.success and result.data is not None:
                drug_name, drug_data = result.data
                combined['quantity'][drug_name] = drug_data['quantity']
                combined['costs'][drug_name] = drug_data['costs']
                combined['dosage'][drug_name] = drug_data['dosage']
                combined['items'][drug_name] = drug_data['items']
        
        return combined
    
    def get_item_identifier(self, drug_info: Tuple[str, List[str]]) -> str:
        """Get identifier for a drug."""
        return drug_info[0]  # Return drug name


class HierarchicalProcessor(WorkloadProcessor):
    """
    Hierarchical processor that combines file-level and drug-level parallelization.
    
    This processor first parallelizes across files, then within each file,
    parallelizes across drugs for optimal resource utilization.
    """
    
    def __init__(self, drug_map: Dict[str, List[str]], mappings_dir: str):
        """
        Initialize the hierarchical processor.
        
        Args:
            drug_map: Dictionary mapping drug/condition names to BNF codes
            mappings_dir: Directory containing mapping files
        """
        self.drug_map = drug_map
        self.mappings_dir = mappings_dir
    
    def process_single_item(self, file_path: str, **kwargs) -> ProcessingResult:
        """
        Process a single file with internal drug-level parallelization.
        
        Args:
            file_path: Path to the monthly prescription file
            **kwargs: Additional arguments (max_drug_cores, etc.)
            
        Returns:
            ProcessingResult containing the month's data for all drugs
        """
        start_time = time.time()
        
        try:
            # Load monthly data
            month = file_path.split('/')[-1].split('.')[0]
            monthly_data = pd.read_csv(file_path, compression='gzip')
            
            # Detect format
            force_old = kwargs.get('force_old_format', False)
            old_format = force_old or (detect_file_format(monthly_data)['format'] == 'old')
            
            # Create drug processor for this month
            drug_processor = DrugWithinMonthProcessor(monthly_data, self.mappings_dir, old_format)
            
            # Use a smaller parallel engine for drugs within this file
            from .parallel_engine import ParallelEngine, ProcessingConfig
            
            max_drug_cores = kwargs.get('max_drug_cores', 4)  # Limit cores for inner parallelization
            drug_config = ProcessingConfig(
                n_cores=min(max_drug_cores, len(self.drug_map)),
                show_progress=False,
                enable_logging=False
            )
            drug_engine = ParallelEngine(drug_config)
            
            # Process drugs in parallel within this month
            drug_items = list(self.drug_map.items())
            month_results = drug_engine.execute(drug_processor, drug_items)
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                data=(month, month_results),
                processing_time=processing_time,
                metadata={'file_path': file_path, 'month': month, 'drugs_processed': len(self.drug_map)}
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return ProcessingResult(
                success=False,
                data=None,
                error=f"Error processing {file_path}: {str(e)}",
                processing_time=processing_time
            )
    
    def combine_results(self, results: List[ProcessingResult]) -> Tuple[Dict, Dict, Dict, Dict]:
        """Combine results from multiple monthly files."""
        monthly_quantity = {}
        monthly_costs = {}
        monthly_dosage = {}
        monthly_items = {}
        
        for result in results:
            if result.success and result.data is not None:
                month, month_data = result.data
                monthly_quantity[month] = month_data['quantity']
                monthly_costs[month] = month_data['costs']
                monthly_dosage[month] = month_data['dosage']
                monthly_items[month] = month_data['items']
        
        return monthly_quantity, monthly_costs, monthly_dosage, monthly_items
    
    def get_item_identifier(self, file_path: str) -> str:
        """Get identifier for a file path."""
        return file_path.split('/')[-1].split('.')[0]


class BatchedFileProcessor(WorkloadProcessor):
    """
    Processor that handles files in batches to manage memory usage.
    
    Useful for very large numbers of files that might exceed available RAM
    if all processed simultaneously.
    """
    
    def __init__(self, drug_map: Dict[str, List[str]], mappings_dir: str, batch_size: int = 6):
        """
        Initialize the batched file processor.
        
        Args:
            drug_map: Dictionary mapping drug/condition names to BNF codes
            mappings_dir: Directory containing mapping files
            batch_size: Number of files to process in each batch
        """
        self.drug_map = drug_map
        self.mappings_dir = mappings_dir
        self.batch_size = batch_size
    
    def process_single_item(self, file_batch: List[str], **kwargs) -> ProcessingResult:
        """
        Process a batch of files.
        
        Args:
            file_batch: List of file paths to process as a batch
            **kwargs: Additional arguments
            
        Returns:
            ProcessingResult containing data from all files in the batch
        """
        start_time = time.time()
        
        try:
            # Use the regular MonthlyFileProcessor for the batch
            file_processor = MonthlyFileProcessor(self.drug_map, self.mappings_dir)
            
            # Process files in this batch serially (to manage memory)
            batch_results = []
            for file_path in file_batch:
                result = file_processor.process_single_item(file_path, **kwargs)
                batch_results.append(result)
            
            # Combine batch results
            combined_results = file_processor.combine_results(batch_results)
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                data=combined_results,
                processing_time=processing_time,
                metadata={'batch_size': len(file_batch), 'files': file_batch}
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return ProcessingResult(
                success=False,
                data=None,
                error=f"Error processing batch: {str(e)}",
                processing_time=processing_time
            )
    
    def combine_results(self, results: List[ProcessingResult]) -> Tuple[Dict, Dict, Dict, Dict]:
        """Combine results from multiple batches."""
        all_monthly_quantity = {}
        all_monthly_costs = {}
        all_monthly_dosage = {}
        all_monthly_items = {}
        
        for result in results:
            if result.success and result.data is not None:
                monthly_quantity, monthly_costs, monthly_dosage, monthly_items = result.data
                
                # Merge into overall results
                all_monthly_quantity.update(monthly_quantity)
                all_monthly_costs.update(monthly_costs)
                all_monthly_dosage.update(monthly_dosage)
                all_monthly_items.update(monthly_items)
        
        return all_monthly_quantity, all_monthly_costs, all_monthly_dosage, all_monthly_items
    
    def get_item_identifier(self, file_batch: List[str]) -> str:
        """Get identifier for a batch."""
        if len(file_batch) == 1:
            return file_batch[0].split('/')[-1].split('.')[0]
        else:
            months = [f.split('/')[-1].split('.')[0] for f in file_batch]
            return f"Batch({'-'.join(months)})"