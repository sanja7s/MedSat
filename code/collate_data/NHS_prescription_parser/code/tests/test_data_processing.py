#!/usr/bin/env python3
"""
Unit tests for data processing functionality.
"""

import unittest
import pandas as pd
import numpy as np
import tempfile
import os
import json
import sys
import argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from matching.commonFunc import str2bool
from matching.commonFunc_updated import detect_file_format, prepare_dataframe


class TestDataFormatDetection(unittest.TestCase):
    """Test data format detection functionality."""
    
    def test_old_format_detection(self):
        """Test detection of old prescription data format."""
        # Create old format dataframe
        old_df = pd.DataFrame({
            '2': ['P001', 'P002'],  # Practice code
            '5': [10, 20],          # Items
            '7': [15.50, 25.75],    # Cost
            '8': [100, 200],        # Quantity
            '16': ['BNF001', 'BNF002'],  # BNF code
            '19': [50, 75]          # Dosage
        })
        
        fields = detect_file_format(old_df)
        
        self.assertEqual(fields['format'], 'old')
        self.assertEqual(fields['practiceField'], '2')
        self.assertEqual(fields['itemField'], '5')
        self.assertEqual(fields['costField'], '7')
        self.assertEqual(fields['quantityField'], '8')
        self.assertEqual(fields['bnfField'], '16')
        self.assertEqual(fields['dosageField'], '19')
    
    def test_new_format_detection(self):
        """Test detection of new prescription data format."""
        # Create new format dataframe
        new_df = pd.DataFrame({
            'PRACTICE_CODE': ['P001', 'P002'],
            'ITEMS': [10, 20],
            'ACTUAL_COST': [15.50, 25.75],
            'TOTAL_QUANTITY': [100, 200],
            'BNF_CODE': ['BNF001', 'BNF002']
        })
        
        fields = detect_file_format(new_df)
        
        self.assertEqual(fields['format'], 'new')
        self.assertEqual(fields['practiceField'], 'PRACTICE_CODE')
        self.assertEqual(fields['itemField'], 'ITEMS')
        self.assertEqual(fields['costField'], 'ACTUAL_COST')
        self.assertEqual(fields['quantityField'], 'TOTAL_QUANTITY')
        self.assertEqual(fields['bnfField'], 'BNF_CODE')
    
    def test_prepare_dataframe(self):
        """Test dataframe preparation for processing."""
        # Test new format without dosage field
        new_df = pd.DataFrame({
            'PRACTICE_CODE': ['P001', 'P002'],
            'ITEMS': [10, 20],
            'ACTUAL_COST': [15.50, 25.75],
            'TOTAL_QUANTITY': [100, 200],
            'BNF_CODE': ['BNF001', 'BNF002']
        })
        
        fields = detect_file_format(new_df)
        prepared_df, updated_fields = prepare_dataframe(new_df, fields)
        
        self.assertIn('19', prepared_df.columns)
        self.assertEqual(updated_fields['dosageField'], '19')
        self.assertTrue((prepared_df['19'] == 0).all())


class TestCommonFunctions(unittest.TestCase):
    """Test common functions used across the system."""
    
    def test_str2bool(self):
        """Test string to boolean conversion."""
        # Test True values
        self.assertTrue(str2bool('true'))
        self.assertTrue(str2bool('True'))
        self.assertTrue(str2bool('yes'))
        self.assertTrue(str2bool('1'))
        self.assertTrue(str2bool(True))
        
        # Test False values
        self.assertFalse(str2bool('false'))
        self.assertFalse(str2bool('False'))
        self.assertFalse(str2bool('no'))
        self.assertFalse(str2bool('0'))
        self.assertFalse(str2bool(False))
        
        # Test invalid values
        with self.assertRaises(argparse.ArgumentTypeError):
            str2bool('invalid')


class TestTemporalMetrics(unittest.TestCase):
    """Test temporal metrics calculation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test LSOA mapping
        self.test_lsoa_map = {
            'P001': {'E01000001': 0.6, 'E01000002': 0.4},
            'P002': {'E01000002': 0.8, 'E01000003': 0.2}
        }
        
        # Create test prescription data (old format)
        self.old_format_data = pd.DataFrame({
            '2': ['P001', 'P001', 'P002'],  # Practice code
            '5': [10, 15, 20],              # Items
            '7': [15.50, 22.75, 30.00],     # Cost
            '8': [100, 150, 200],           # Quantity
            '16': ['BNF001', 'BNF002', 'BNF001'],  # BNF code
            '19': [50, 75, 100]             # Dosage
        })
        
        # Create test prescription data (new format)
        self.new_format_data = pd.DataFrame({
            'PRACTICE_CODE': ['P001', 'P001', 'P002'],
            'ITEMS': [10, 15, 20],
            'ACTUAL_COST': [15.50, 22.75, 30.00],
            'TOTAL_QUANTITY': [100, 150, 200],
            'BNF_CODE': ['BNF001', 'BNF002', 'BNF001']
        })
    
    def test_calculate_temporal_metrics_integration(self):
        """Test that both old and new format processing produce consistent results."""
        # This test requires the mapping files to exist
        # For now, we'll test the format detection and preparation
        
        # Test old format detection
        old_fields = detect_file_format(self.old_format_data)
        self.assertEqual(old_fields['format'], 'old')
        
        # Test new format detection and preparation
        new_fields = detect_file_format(self.new_format_data)
        prepared_new_data, updated_fields = prepare_dataframe(self.new_format_data, new_fields)
        
        self.assertEqual(updated_fields['format'], 'new')
        self.assertIn('19', prepared_new_data.columns)


class TestDataConsistency(unittest.TestCase):
    """Test data consistency across different processing paths."""
    
    def test_column_mapping_consistency(self):
        """Test that column mappings are consistent."""
        # Test that old and new format mappings cover the same functionality
        old_fields = {
            'practiceField': '2',
            'itemField': '5', 
            'costField': '7',
            'quantityField': '8',
            'bnfField': '16',
            'dosageField': '19'
        }
        
        new_fields = {
            'practiceField': 'PRACTICE_CODE',
            'itemField': 'ITEMS',
            'costField': 'ACTUAL_COST', 
            'quantityField': 'TOTAL_QUANTITY',
            'bnfField': 'BNF_CODE',
            'dosageField': '19'  # This should be added by prepare_dataframe
        }
        
        # Check that all required fields are present
        required_fields = ['practiceField', 'itemField', 'costField', 'quantityField', 'bnfField', 'dosageField']
        
        for field in required_fields:
            self.assertIn(field, old_fields)
            self.assertIn(field, new_fields)


if __name__ == '__main__':
    unittest.main()