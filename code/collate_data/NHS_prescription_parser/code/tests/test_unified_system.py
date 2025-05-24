#!/usr/bin/env python3
"""
Unit tests for the unified system functionality.
"""

import unittest
import pandas as pd
import numpy as np
import tempfile
import os
import json
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unified.unified_processor import (
    DataFrameAdapter, DataFormat, LSPOAMappingManager, 
    MetricsCalculator, UnifiedProcessor, ConfigManager
)


class TestDataFrameAdapter(unittest.TestCase):
    """Test DataFrameAdapter functionality."""
    
    def test_old_format_detection(self):
        """Test detection of old format."""
        old_df = pd.DataFrame({
            '2': ['P001', 'P002'],
            '5': [10, 20],
            '7': [15.50, 25.75],
            '8': [100, 200],
            '16': ['BNF001', 'BNF002'],
            '19': [50, 75]
        })
        
        adapter = DataFrameAdapter(old_df)
        self.assertEqual(adapter.get_format(), DataFormat.OLD)
        self.assertEqual(adapter.get_practice_code_column(), '2')
        self.assertEqual(adapter.get_quantity_column(), '8')
    
    def test_new_format_detection(self):
        """Test detection of new format."""
        new_df = pd.DataFrame({
            'PRACTICE_CODE': ['P001', 'P002'],
            'ITEMS': [10, 20],
            'ACTUAL_COST': [15.50, 25.75],
            'TOTAL_QUANTITY': [100, 200],
            'BNF_CODE': ['BNF001', 'BNF002']
        })
        
        adapter = DataFrameAdapter(new_df)
        self.assertEqual(adapter.get_format(), DataFormat.NEW)
        self.assertEqual(adapter.get_practice_code_column(), 'PRACTICE_CODE')
        self.assertEqual(adapter.get_quantity_column(), 'TOTAL_QUANTITY')
        
        # Check that dosage field was added
        self.assertIn('19', adapter.get_dataframe().columns)
    
    def test_bnf_filtering(self):
        """Test BNF code filtering."""
        df = pd.DataFrame({
            'PRACTICE_CODE': ['P001', 'P001', 'P002'],
            'BNF_CODE': ['BNF001', 'BNF002', 'BNF001'],
            'ITEMS': [10, 15, 20],
            'ACTUAL_COST': [15.50, 22.75, 25.75],
            'TOTAL_QUANTITY': [100, 150, 200]
        })
        
        adapter = DataFrameAdapter(df)
        filtered = adapter.filter_by_bnf_codes(['BNF001'])
        
        self.assertEqual(len(adapter.get_dataframe()), 3)
        self.assertEqual(len(filtered.get_dataframe()), 2)


class TestConfigManager(unittest.TestCase):
    """Test configuration management."""
    
    def test_default_config(self):
        """Test default configuration loading."""
        config = ConfigManager.load_config()
        
        self.assertIn('mappings_dir', config)
        self.assertIn('output_dir', config)
        self.assertIn('logging_level', config)
        self.assertEqual(config['logging_level'], 'INFO')
    
    def test_custom_config(self):
        """Test custom configuration loading."""
        # Create temporary config file
        temp_config = {
            'mappings_dir': './custom_mappings/',
            'logging_level': 'DEBUG'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(temp_config, f)
            temp_file = f.name
        
        try:
            config = ConfigManager.load_config(temp_file)
            self.assertEqual(config['mappings_dir'], './custom_mappings/')
            self.assertEqual(config['logging_level'], 'DEBUG')
            # Should still have defaults for missing keys
            self.assertIn('output_dir', config)
        finally:
            os.unlink(temp_file)


class TestLSPOAMappingManager(unittest.TestCase):
    """Test LSOA mapping management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test mapping files
        test_gp_mapping = {
            'P001': {
                'Practice_name': 'Test Practice 1',
                'Patient_registry_LSOA': {
                    'E01000001': 100,
                    'E01000002': 50
                }
            },
            'P002': {
                'Practice_name': 'Test Practice 2',
                'Patient_registry_LSOA': {
                    'E01000002': 75,
                    'E01000003': 25
                }
            }
        }
        
        with open(os.path.join(self.temp_dir, 'GPs_2021.json'), 'w') as f:
            json.dump(test_gp_mapping, f)
        
        test_patient_dist = {
            'E01000001': 100,
            'E01000002': 125,
            'E01000003': 25
        }
        
        with open(os.path.join(self.temp_dir, 'GP_LSOA_PATIENTSDIST_2021.json'), 'w') as f:
            json.dump(test_patient_dist, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_mapping_loading(self):
        """Test LSOA mapping loading."""
        manager = LSPOAMappingManager(self.temp_dir)
        
        # Test getting specific year mapping
        mapping_2021 = manager.get_lsoa_mapping(2021)
        self.assertIn('P001', mapping_2021)
        self.assertIn('P002', mapping_2021)
        
        # Test patient population
        patient_pop = manager.get_patient_population(2021)
        self.assertEqual(patient_pop['E01000001'], 100)
        self.assertEqual(patient_pop['E01000002'], 125)


class TestMetricsCalculator(unittest.TestCase):
    """Test metrics calculation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test mapping
        test_gp_mapping = {
            'P001': {
                'Practice_name': 'Test Practice',
                'Patient_registry_LSOA': {
                    'E01000001': 0.6,
                    'E01000002': 0.4
                }
            }
        }
        
        with open(os.path.join(self.temp_dir, 'GPs_2021.json'), 'w') as f:
            json.dump(test_gp_mapping, f)
        
        self.mapping_manager = LSPOAMappingManager(self.temp_dir)
        self.calculator = MetricsCalculator(self.mapping_manager)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_lsoa_metrics_calculation(self):
        """Test LSOA metrics calculation."""
        # Create test prescription data
        df = pd.DataFrame({
            'PRACTICE_CODE': ['P001', 'P001'],
            'ITEMS': [10, 15],
            'ACTUAL_COST': [15.50, 22.75],
            'TOTAL_QUANTITY': [100, 150],
            'BNF_CODE': ['BNF001', 'BNF002']
        })
        
        adapter = DataFrameAdapter(df)
        
        # Calculate metrics
        quantity, costs, dosage, items = self.calculator.calculate_lsoa_metrics(adapter, 2021)
        
        # Verify results
        self.assertIn('E01000001', quantity)
        self.assertIn('E01000002', quantity)
        
        # Check that values are distributed according to weights
        total_quantity = 250  # 100 + 150
        expected_e01000001 = total_quantity * 0.6  # 150
        expected_e01000002 = total_quantity * 0.4  # 100
        
        self.assertAlmostEqual(quantity['E01000001'], expected_e01000001)
        self.assertAlmostEqual(quantity['E01000002'], expected_e01000002)


class TestUnifiedProcessor(unittest.TestCase):
    """Test unified processor integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create minimal mapping structure
        test_mapping = {
            'P001': {
                'Practice_name': 'Test Practice',
                'Patient_registry_LSOA': {
                    'E01000001': 0.5,
                    'E01000002': 0.5
                }
            }
        }
        
        with open(os.path.join(self.temp_dir, 'GPs_2021.json'), 'w') as f:
            json.dump(test_mapping, f)
        
        # Create test patient population
        patient_pop = {'E01000001': 1000, 'E01000002': 1000}
        with open(os.path.join(self.temp_dir, 'GP_LSOA_PATIENTSDIST_2021.json'), 'w') as f:
            json.dump(patient_pop, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_processor_initialization(self):
        """Test processor initialization."""
        processor = UnifiedProcessor(self.temp_dir)
        
        self.assertIsNotNone(processor.mapping_manager)
        self.assertIsNotNone(processor.calculator)
        self.assertIsNotNone(processor.writer)


if __name__ == '__main__':
    unittest.main()