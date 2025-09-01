#!/usr/bin/env python3
"""
Unified NHS Prescription Data Processor

This module provides a unified interface for processing NHS prescription data,
abstracting away the differences between old and new data formats.
"""

import pandas as pd
import numpy as np
import json
import os
import glob
import re
from typing import Dict, List, Tuple, Optional, Union
from abc import ABC, abstractmethod
from enum import Enum
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFormat(Enum):
    """Enumeration of supported data formats."""
    OLD = "old"
    NEW = "new"
    UNKNOWN = "unknown"


class DataFrameAdapter:
    """
    Adapter class that provides a unified interface for both old and new prescription data formats.
    
    This class abstracts away the differences between the two formats, allowing the rest of the
    codebase to work with a consistent interface.
    """
    
    # Field mappings for different formats
    OLD_FORMAT_FIELDS = {
        'practice_code': '2',
        'items': '5',
        'cost': '7',
        'quantity': '8',
        'bnf_code': '16',
        'dosage': '19'
    }
    
    NEW_FORMAT_FIELDS = {
        'practice_code': 'PRACTICE_CODE',
        'items': 'ITEMS',
        'cost': 'ACTUAL_COST',
        'quantity': 'TOTAL_QUANTITY',
        'bnf_code': 'BNF_CODE',
        'dosage': '19'  # This may need to be added
    }
    
    def __init__(self, dataframe: pd.DataFrame):
        """
        Initialize the adapter with a dataframe.
        
        Args:
            dataframe: The prescription dataframe to adapt
        """
        self.df = dataframe.copy()
        self.format = self._detect_format()
        self.field_mapping = self._get_field_mapping()
        self._prepare_dataframe()
    
    def _detect_format(self) -> DataFormat:
        """Detect the format of the dataframe based on column names."""
        # Check for old format (numeric column names)
        old_format_columns = ['2', '5', '7', '8', '16']
        if all(col in self.df.columns for col in old_format_columns):
            return DataFormat.OLD
        
        # Check for new format (named columns)
        new_format_columns = ['PRACTICE_CODE', 'ITEMS', 'ACTUAL_COST']
        if all(col in self.df.columns for col in new_format_columns):
            return DataFormat.NEW
        
        return DataFormat.UNKNOWN
    
    def _get_field_mapping(self) -> Dict[str, str]:
        """Get the appropriate field mapping for the detected format."""
        if self.format == DataFormat.OLD:
            return self.OLD_FORMAT_FIELDS
        elif self.format == DataFormat.NEW:
            return self.NEW_FORMAT_FIELDS
        else:
            # Try to infer mappings for unknown format
            return self._infer_field_mapping()
    
    def _infer_field_mapping(self) -> Dict[str, str]:
        """Infer field mappings for unknown formats."""
        mapping = {}
        
        for col in self.df.columns:
            col_lower = col.lower()
            if 'practice' in col_lower and 'code' in col_lower:
                mapping['practice_code'] = col
            elif 'quantity' in col_lower:
                mapping['quantity'] = col
            elif 'cost' in col_lower:
                mapping['cost'] = col
            elif 'item' in col_lower:
                mapping['items'] = col
            elif 'bnf' in col_lower and 'code' in col_lower:
                mapping['bnf_code'] = col
        
        # Default dosage field
        mapping['dosage'] = '19'
        
        return mapping
    
    def _prepare_dataframe(self):
        """Prepare the dataframe by ensuring all required fields are present."""
        # Add dosage field if it doesn't exist
        if self.field_mapping['dosage'] not in self.df.columns:
            self.df[self.field_mapping['dosage']] = 0.0
            logger.info(f"Added missing dosage field: {self.field_mapping['dosage']}")
    
    def get_practice_code_column(self) -> str:
        """Get the practice code column name."""
        return self.field_mapping['practice_code']
    
    def get_quantity_column(self) -> str:
        """Get the quantity column name."""
        return self.field_mapping['quantity']
    
    def get_cost_column(self) -> str:
        """Get the cost column name."""
        return self.field_mapping['cost']
    
    def get_items_column(self) -> str:
        """Get the items column name."""
        return self.field_mapping['items']
    
    def get_bnf_code_column(self) -> str:
        """Get the BNF code column name."""
        return self.field_mapping['bnf_code']
    
    def get_dosage_column(self) -> str:
        """Get the dosage column name."""
        return self.field_mapping['dosage']
    
    def get_dataframe(self) -> pd.DataFrame:
        """Get the adapted dataframe."""
        return self.df
    
    def get_format(self) -> DataFormat:
        """Get the detected format."""
        return self.format
    
    def filter_by_bnf_codes(self, bnf_codes: List[str]) -> 'DataFrameAdapter':
        """Filter the dataframe by BNF codes and return a new adapter."""
        bnf_column = self.get_bnf_code_column()
        filtered_df = self.df[self.df[bnf_column].isin(bnf_codes)]
        return DataFrameAdapter(filtered_df)


class LSPOAMappingManager:
    """
    Manages LSOA (Lower Super Output Area) mappings for different years and formats.
    
    This class abstracts the complexity of handling different LSOA mapping files
    and provides a unified interface for accessing patient distributions.
    """
    
    def __init__(self, mappings_dir: str):
        """
        Initialize the mapping manager.
        
        Args:
            mappings_dir: Directory containing mapping files
        """
        self.mappings_dir = mappings_dir
        self._lsoa_mappings = {}
        self._patient_populations = {}
        self._load_mappings()
    
    def _load_mappings(self):
        """Load all available LSOA mappings."""
        # Load original mappings
        old_gp_file = os.path.join(self.mappings_dir, 'GPs.json')
        old_gp_2013_file = os.path.join(self.mappings_dir, 'GPs_2013.json')
        old_dist_file = os.path.join(self.mappings_dir, 'GP_LSOA_PATIENTSDIST.json')
        
        if os.path.exists(old_gp_file):
            with open(old_gp_file, 'r') as f:
                self._lsoa_mappings['default'] = json.load(f)
        
        if os.path.exists(old_gp_2013_file):
            with open(old_gp_2013_file, 'r') as f:
                self._lsoa_mappings['2013'] = json.load(f)
        
        if os.path.exists(old_dist_file):
            with open(old_dist_file, 'r') as f:
                self._patient_populations['default'] = json.load(f)
        
        # Load year-specific mappings
        year_pattern = re.compile(r'GPs?_(\d{4})\.json')
        dist_pattern = re.compile(r'GP_LSOA_PATIENTSDIST_(\d{4})\.json')
        
        for file in os.listdir(self.mappings_dir):
            year_match = year_pattern.match(file)
            dist_match = dist_pattern.match(file)
            
            if year_match:
                year = year_match.group(1)
                file_path = os.path.join(self.mappings_dir, file)
                with open(file_path, 'r') as f:
                    self._lsoa_mappings[year] = json.load(f)
            
            elif dist_match:
                year = dist_match.group(1)
                file_path = os.path.join(self.mappings_dir, file)
                with open(file_path, 'r') as f:
                    self._patient_populations[year] = json.load(f)
    
    def get_lsoa_mapping(self, year: Optional[Union[str, int]] = None) -> Dict:
        """
        Get LSOA mapping for a specific year.
        
        Args:
            year: Year for which to get the mapping (if None, uses most recent)
        
        Returns:
            Dictionary mapping GP practices to LSOA distributions
        """
        if year is None:
            # Return the most recent mapping
            available_years = [y for y in self._lsoa_mappings.keys() if y.isdigit()]
            if available_years:
                latest_year = max(available_years, key=int)
                return self._lsoa_mappings[latest_year]
            else:
                return self._lsoa_mappings.get('default', {})
        
        year_str = str(year)
        if year_str in self._lsoa_mappings:
            return self._lsoa_mappings[year_str]
        
        # Find closest year
        available_years = [int(y) for y in self._lsoa_mappings.keys() if y.isdigit()]
        if available_years:
            closest_year = min(available_years, key=lambda x: abs(x - int(year)))
            logger.warning(f"Year {year} not found, using closest year: {closest_year}")
            return self._lsoa_mappings[str(closest_year)]
        
        return self._lsoa_mappings.get('default', {})
    
    def get_patient_population(self, year: Optional[Union[str, int]] = None) -> Dict:
        """
        Get patient population distribution for a specific year.
        
        Args:
            year: Year for which to get the population (if None, uses most recent)
        
        Returns:
            Dictionary mapping LSOA codes to patient counts
        """
        # First try to get direct patient population
        if year is not None:
            year_str = str(year)
            if year_str in self._patient_populations:
                return self._patient_populations[year_str]
        
        # If not available, compute from GP mappings
        gp_mapping = self.get_lsoa_mapping(year)
        patient_pop = {}
        
        for gp_code, gp_data in gp_mapping.items():
            if 'Patient_registry_LSOA' in gp_data:
                for lsoa_code, patient_count in gp_data['Patient_registry_LSOA'].items():
                    if lsoa_code not in patient_pop:
                        patient_pop[lsoa_code] = 0
                    patient_pop[lsoa_code] += patient_count
        
        return patient_pop


class MetricsCalculator:
    """
    Calculates temporal metrics at LSOA level using a unified approach.
    
    This class provides a consistent interface for calculating metrics regardless
    of the data format being processed.
    """
    
    def __init__(self, mapping_manager: LSPOAMappingManager):
        """
        Initialize the metrics calculator.
        
        Args:
            mapping_manager: LSOA mapping manager instance
        """
        self.mapping_manager = mapping_manager
    
    def calculate_lsoa_metrics(self, 
                              adapter: DataFrameAdapter, 
                              year: Optional[Union[str, int]] = None) -> Tuple[Dict, Dict, Dict, Dict]:
        """
        Calculate temporal metrics at LSOA level.
        
        Args:
            adapter: DataFrameAdapter instance with prescription data
            year: Year for LSOA mapping (if None, auto-detects)
        
        Returns:
            Tuple of (quantity, costs, dosage, items) dictionaries by LSOA
        """
        # Initialize result dictionaries
        lsoa_quantity = {}
        lsoa_costs = {}
        lsoa_dosage = {}
        lsoa_items = {}
        
        # Get the appropriate LSOA mapping
        lsoa_mapping = self.mapping_manager.get_lsoa_mapping(year)
        
        # Get column names from adapter
        practice_col = adapter.get_practice_code_column()
        quantity_col = adapter.get_quantity_column()
        cost_col = adapter.get_cost_column()
        dosage_col = adapter.get_dosage_column()
        items_col = adapter.get_items_column()
        
        # Get the dataframe
        df = adapter.get_dataframe()
        
        # Process by practice
        for practice_code, group in df.groupby(practice_col):
            # Calculate totals for this practice
            total_quantity = np.sum(group[quantity_col])
            total_cost = np.sum(group[cost_col])
            total_dosage = np.sum(group[dosage_col]) if dosage_col in group.columns else 0
            total_items = np.sum(group[items_col])
            
            # Distribute to LSOAs based on mapping
            if practice_code in lsoa_mapping:
                lsoa_distribution = lsoa_mapping[practice_code]
                
                # Handle different mapping structures
                if isinstance(lsoa_distribution, dict):
                    if 'Patient_registry_LSOA' in lsoa_distribution:
                        # New format with nested structure
                        distribution = lsoa_distribution['Patient_registry_LSOA']
                    else:
                        # Old format with direct mapping
                        distribution = lsoa_distribution
                else:
                    continue
                
                # Distribute metrics to LSOAs
                for lsoa_code, weight in distribution.items():
                    if lsoa_code not in lsoa_quantity:
                        lsoa_quantity[lsoa_code] = 0.0
                        lsoa_costs[lsoa_code] = 0.0
                        lsoa_dosage[lsoa_code] = 0.0
                        lsoa_items[lsoa_code] = 0.0
                    
                    # Convert weight to float and apply
                    weight_float = float(weight)
                    lsoa_quantity[lsoa_code] += total_quantity * weight_float
                    lsoa_costs[lsoa_code] += total_cost * weight_float
                    lsoa_dosage[lsoa_code] += total_dosage * weight_float
                    lsoa_items[lsoa_code] += total_items * weight_float
        
        return lsoa_quantity, lsoa_costs, lsoa_dosage, lsoa_items
    
    def calculate_opioid_metrics(self,
                                adapter: DataFrameAdapter,
                                ome_mapping: Dict[str, float],
                                year: Optional[Union[str, int]] = None) -> Tuple[Dict, Dict, Dict, Dict]:
        """
        Calculate opioid-specific metrics including OME (Oral Morphine Equivalent).
        
        Args:
            adapter: DataFrameAdapter instance with opioid prescription data
            ome_mapping: Mapping of BNF codes to OME multipliers
            year: Year for LSOA mapping
        
        Returns:
            Tuple of (quantity, costs, ome, items) dictionaries by LSOA
        """
        # Add OME calculation to the dataframe
        df = adapter.get_dataframe().copy()
        bnf_col = adapter.get_bnf_code_column()
        quantity_col = adapter.get_quantity_column()
        
        # Calculate OME for each prescription
        df['presc_ome'] = 0.0
        for bnf_code, ome_multiplier in ome_mapping.items():
            mask = df[bnf_col] == bnf_code
            if '15' in df.columns:  # Assuming column '15' exists for some multiplier
                df.loc[mask, 'presc_ome'] = df.loc[mask, quantity_col] * df.loc[mask, '15'] * ome_multiplier
            else:
                df.loc[mask, 'presc_ome'] = df.loc[mask, quantity_col] * ome_multiplier
        
        # Create new adapter with OME data
        ome_adapter = DataFrameAdapter(df)
        
        # Calculate regular metrics but replace dosage with OME
        lsoa_quantity, lsoa_costs, _, lsoa_items = self.calculate_lsoa_metrics(ome_adapter, year)
        
        # Calculate OME separately
        lsoa_ome = {}
        lsoa_mapping = self.mapping_manager.get_lsoa_mapping(year)
        practice_col = ome_adapter.get_practice_code_column()
        
        for practice_code, group in df.groupby(practice_col):
            total_ome = np.sum(group['presc_ome'])
            
            if practice_code in lsoa_mapping:
                lsoa_distribution = lsoa_mapping[practice_code]
                
                if isinstance(lsoa_distribution, dict):
                    if 'Patient_registry_LSOA' in lsoa_distribution:
                        distribution = lsoa_distribution['Patient_registry_LSOA']
                    else:
                        distribution = lsoa_distribution
                else:
                    continue
                
                for lsoa_code, weight in distribution.items():
                    if lsoa_code not in lsoa_ome:
                        lsoa_ome[lsoa_code] = 0.0
                    
                    lsoa_ome[lsoa_code] += total_ome * float(weight)
        
        return lsoa_quantity, lsoa_costs, lsoa_ome, lsoa_items


class ResultsWriter:
    """
    Unified results writer that handles output formatting consistently.
    """
    
    def __init__(self, mapping_manager: LSPOAMappingManager):
        """
        Initialize the results writer.
        
        Args:
            mapping_manager: LSOA mapping manager instance
        """
        self.mapping_manager = mapping_manager
    
    def write_standard_results(self,
                              monthly_data: Dict,
                              output_dir: str,
                              year: Optional[Union[str, int]] = None):
        """
        Write standard prevalence results to files.
        
        Args:
            monthly_data: Dictionary with structure {month: {condition: {lsoa: metrics}}}
            output_dir: Output directory
            year: Year for patient population data
        """
        # Get patient population
        patient_pop = self.mapping_manager.get_patient_population(year)
        
        # Extract conditions from the first month's data
        first_month = next(iter(monthly_data.values()))
        conditions = list(first_month.keys())
        
        for condition in conditions:
            self._write_condition_results(monthly_data, condition, output_dir, patient_pop)
    
    def _write_condition_results(self,
                                monthly_data: Dict,
                                condition: str,
                                output_dir: str,
                                patient_pop: Dict):
        """Write results for a specific condition."""
        # Prepare data structure
        result_data = {
            'YYYYMM': [],
            'LSOA_CODE': [],
            'Total_quantity': [],
            'Dosage_ratio': [],
            'Total_cost': [],
            'Total_items': [],
            'Patient_count': []
        }
        
        # Extract data from monthly structure
        for month, month_data in monthly_data.items():
            if condition in month_data:
                condition_data = month_data[condition]
                
                for metric_type, lsoa_data in condition_data.items():
                    if metric_type == 'quantity':
                        for lsoa_code, value in lsoa_data.items():
                            if lsoa_code.startswith('E'):  # England LSOAs
                                result_data['YYYYMM'].append(month)
                                result_data['LSOA_CODE'].append(lsoa_code)
                                result_data['Total_quantity'].append(value)
                                
                                # Get corresponding values from other metrics
                                result_data['Dosage_ratio'].append(
                                    condition_data.get('dosage', {}).get(lsoa_code, 0)
                                )
                                result_data['Total_cost'].append(
                                    condition_data.get('costs', {}).get(lsoa_code, 0)
                                )
                                result_data['Total_items'].append(
                                    condition_data.get('items', {}).get(lsoa_code, 0)
                                )
                                result_data['Patient_count'].append(
                                    patient_pop.get(lsoa_code, 0)
                                )
        
        # Write to file
        df = pd.DataFrame(result_data)
        output_file = os.path.join(output_dir, f"{condition}_V4.csv.gz")
        df.to_csv(output_file, index=False, compression='gzip')
        logger.info(f"Results written to: {output_file}")


class UnifiedProcessor:
    """
    Main unified processor that orchestrates the entire prescription processing pipeline.
    
    This class provides a high-level interface that abstracts away all the complexity
    of handling different data formats and processing steps.
    """
    
    def __init__(self, mappings_dir: str = './mappings/'):
        """
        Initialize the unified processor.
        
        Args:
            mappings_dir: Directory containing mapping files
        """
        self.mappings_dir = mappings_dir
        self.mapping_manager = LSPOAMappingManager(mappings_dir)
        self.calculator = MetricsCalculator(self.mapping_manager)
        self.writer = ResultsWriter(self.mapping_manager)
    
    def process_prescription_files(self,
                                  file_paths: List[str],
                                  drug_mapping: Dict[str, List[str]],
                                  output_dir: str,
                                  year: Optional[Union[str, int]] = None) -> Dict:
        """
        Process multiple prescription files and calculate prevalence metrics.
        
        Args:
            file_paths: List of paths to prescription files
            drug_mapping: Dictionary mapping condition names to BNF codes
            output_dir: Output directory for results
            year: Year for LSOA mappings
        
        Returns:
            Dictionary containing calculated metrics
        """
        results = {}
        
        for file_path in file_paths:
            # Extract month from filename
            month = self._extract_month_from_path(file_path)
            
            # Load and adapt the data
            df = pd.read_csv(file_path, compression='gzip')
            adapter = DataFrameAdapter(df)
            
            logger.info(f"Processing {file_path} (format: {adapter.get_format().value})")
            
            # Initialize month results
            results[month] = {}
            
            # Process each condition
            for condition, bnf_codes in drug_mapping.items():
                # Filter data for this condition
                filtered_adapter = adapter.filter_by_bnf_codes(bnf_codes)
                
                # Calculate metrics
                quantity, costs, dosage, items = self.calculator.calculate_lsoa_metrics(
                    filtered_adapter, year
                )
                
                # Store results
                results[month][condition] = {
                    'quantity': quantity,
                    'costs': costs,
                    'dosage': dosage,
                    'items': items
                }
        
        # Write results
        self.writer.write_standard_results(results, output_dir, year)
        
        return results
    
    def _extract_month_from_path(self, file_path: str) -> str:
        """Extract month (YYYYMM) from file path."""
        filename = os.path.basename(file_path)
        return filename.split('.')[0]


# Configuration management
class ConfigManager:
    """Centralized configuration management."""
    
    DEFAULT_CONFIG = {
        'mappings_dir': './mappings/',
        'output_dir': '../data_prep/',
        'input_dir': './prescriptionfiles/',
        'sources_file': './sources/serialized_file_paths.json',
        'logging_level': 'INFO'
    }
    
    @classmethod
    def load_config(cls, config_path: Optional[str] = None) -> Dict:
        """Load configuration from file or use defaults."""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            # Merge with defaults
            merged_config = cls.DEFAULT_CONFIG.copy()
            merged_config.update(config)
            return merged_config
        return cls.DEFAULT_CONFIG.copy()


if __name__ == "__main__":
    # Example usage
    processor = UnifiedProcessor()
    
    # Example drug mapping
    drug_mapping = {
        'diabetes': ['BNF_CODE_1', 'BNF_CODE_2'],
        'hypertension': ['BNF_CODE_3', 'BNF_CODE_4']
    }
    
    # Process files
    file_paths = ['./prescriptionfiles/202001.gz']
    results = processor.process_prescription_files(
        file_paths, drug_mapping, '../data_prep/', 2020
    )
    
    print("Processing complete!")