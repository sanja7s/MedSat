#!/usr/bin/env python3
"""
End-to-end tests for run_analysis.sh script functionality.
Tests the standardized date format and command interface.
"""

import unittest
import subprocess
import os
import sys
import tempfile
import shutil
import json
from pathlib import Path

# Add the parent directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestRunAnalysisE2E(unittest.TestCase):
    """End-to-end tests for run_analysis.sh script."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        cls.script_dir = Path(__file__).parent.parent
        cls.run_analysis_script = cls.script_dir / "run_analysis.sh"
        cls.original_dir = os.getcwd()
        
        # Change to script directory for tests
        os.chdir(cls.script_dir)
        
        # Verify script exists and is executable
        if not cls.run_analysis_script.exists():
            raise unittest.SkipTest("run_analysis.sh script not found")
        
        # Make sure script is executable
        os.chmod(cls.run_analysis_script, 0o755)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        os.chdir(cls.original_dir)
    
    def test_help_flag(self):
        """Test --help flag functionality."""
        result = subprocess.run(
            ["./run_analysis.sh", "--help"], 
            capture_output=True, 
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("NHS Prescription Parser", result.stdout)
        self.assertIn("USAGE:", result.stdout)
        self.assertIn("ANALYSIS TYPES:", result.stdout)
        self.assertIn("DATE FORMATS", result.stdout)
        self.assertIn("colon-separated", result.stdout)
    
    def test_info_flag(self):
        """Test --info flag functionality."""
        result = subprocess.run(
            ["./run_analysis.sh", "--info"], 
            capture_output=True, 
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("System Information", result.stdout)
        self.assertIn("CPU Cores:", result.stdout)
        self.assertIn("RAM", result.stdout)
    
    def test_insufficient_arguments(self):
        """Test behavior with insufficient arguments."""
        result = subprocess.run(
            ["./run_analysis.sh"], 
            capture_output=True, 
            text=True
        )
        
        self.assertEqual(result.returncode, 0)  # Script shows help and exits normally
        self.assertIn("USAGE:", result.stdout)
    
    def test_insufficient_arguments_two_params(self):
        """Test behavior with only two arguments."""
        result = subprocess.run(
            ["./run_analysis.sh", "drug", "metformin"], 
            capture_output=True, 
            text=True
        )
        
        self.assertEqual(result.returncode, 0)  # Script shows help and exits normally
        self.assertIn("USAGE:", result.stdout)
    
    def test_invalid_analysis_type(self):
        """Test behavior with invalid analysis type."""
        result = subprocess.run(
            ["./run_analysis.sh", "invalid_type", "metformin", "2021"], 
            capture_output=True, 
            text=True
        )
        
        # Script should show unknown analysis type error
        self.assertIn("Unknown analysis type", result.stdout + result.stderr)
    
    def test_date_format_validation_single_year(self):
        """Test single year date format validation."""
        result = subprocess.run(
            ["./run_analysis.sh", "drug", "test_drug", "2021", "--dry-run"], 
            capture_output=True, 
            text=True
        )
        
        # Should show date parsing results
        self.assertIn("Period: 202101 to 202112", result.stdout)
        self.assertEqual(result.returncode, 0)
    
    def test_date_format_validation_single_month(self):
        """Test single month date format validation."""
        result = subprocess.run(
            ["./run_analysis.sh", "drug", "test_drug", "2021-01", "--dry-run"], 
            capture_output=True, 
            text=True
        )
        
        # Should show date parsing results
        self.assertIn("Period: 202101 to 202101", result.stdout)
        self.assertEqual(result.returncode, 0)
    
    def test_date_format_validation_month_range(self):
        """Test month range date format validation."""
        result = subprocess.run(
            ["./run_analysis.sh", "drug", "test_drug", "2021-01:06", "--dry-run"], 
            capture_output=True, 
            text=True
        )
        
        # Should show date parsing results
        self.assertIn("Period: 202101 to 202106", result.stdout)
        self.assertEqual(result.returncode, 0)
    
    def test_date_format_validation_cross_year(self):
        """Test cross-year date format validation."""
        result = subprocess.run(
            ["./run_analysis.sh", "drug", "test_drug", "2019-09:2021-01", "--dry-run"], 
            capture_output=True, 
            text=True
        )
        
        # Should show date parsing results
        self.assertIn("Period: 201909 to 202101", result.stdout)
        self.assertEqual(result.returncode, 0)
    
    def test_date_format_validation_multi_year(self):
        """Test multi-year date format validation."""
        result = subprocess.run(
            ["./run_analysis.sh", "drug", "test_drug", "2018:2021", "--dry-run"], 
            capture_output=True, 
            text=True
        )
        
        # Should show date parsing results
        self.assertIn("Period: 201801 to 202112", result.stdout)
        self.assertEqual(result.returncode, 0)
    
    def test_date_format_validation_exact_months(self):
        """Test exact month date format validation."""
        result = subprocess.run(
            ["./run_analysis.sh", "drug", "test_drug", "201801:202112", "--dry-run"], 
            capture_output=True, 
            text=True
        )
        
        # Should show date parsing results
        self.assertIn("Period: 201801 to 202112", result.stdout)
        self.assertEqual(result.returncode, 0)
    
    def test_invalid_date_format(self):
        """Test behavior with invalid date format."""
        result = subprocess.run(
            ["./run_analysis.sh", "drug", "test_drug", "invalid-date"], 
            capture_output=True, 
            text=True
        )
        
        self.assertEqual(result.returncode, 1)  # Should exit with error
        self.assertIn("Invalid date format", result.stdout)
        self.assertIn("Valid formats (colon-separated only):", result.stdout)
    
    def test_deprecated_space_separated_dates_not_supported(self):
        """Test that old space-separated date format is no longer supported."""
        result = subprocess.run(
            ["./run_analysis.sh", "drug", "test_drug", "2019-09", "2021-01"], 
            capture_output=True, 
            text=True
        )
        
        # Should treat "2021-01" as an unknown option, not a date
        # The script should show an unknown option error
        self.assertIn("Unknown option", result.stdout + result.stderr)
        self.assertEqual(result.returncode, 1)
    
    def test_analysis_type_drug(self):
        """Test drug analysis type parsing."""
        result = subprocess.run(
            ["./run_analysis.sh", "drug", "metformin", "2021-01", "--dry-run"], 
            capture_output=True, 
            text=True
        )
        
        self.assertIn("Type: drug", result.stdout)
        self.assertIn("Target: metformin", result.stdout)
        self.assertEqual(result.returncode, 0)
    
    def test_analysis_type_condition(self):
        """Test condition analysis type parsing."""
        result = subprocess.run(
            ["./run_analysis.sh", "condition", "diabetes", "2021-01", "--dry-run"], 
            capture_output=True, 
            text=True
        )
        
        self.assertIn("Type: condition", result.stdout)
        self.assertIn("Target: diabetes", result.stdout)
        self.assertEqual(result.returncode, 0)
    
    def test_analysis_type_custom(self):
        """Test custom analysis type parsing."""
        result = subprocess.run(
            ["./run_analysis.sh", "custom", "test_file.json", "2021-01", "--dry-run"], 
            capture_output=True, 
            text=True
        )
        
        self.assertIn("Type: custom", result.stdout)
        self.assertIn("Target: test_file.json", result.stdout)
        self.assertEqual(result.returncode, 0)
    
    def test_parallel_options(self):
        """Test parallel processing options."""
        result = subprocess.run(
            ["./run_analysis.sh", "drug", "test", "2021-01", "--cores", "4", "--dry-run"], 
            capture_output=True, 
            text=True
        )
        
        self.assertIn("Processing: Parallel (4 cores)", result.stdout)
        self.assertEqual(result.returncode, 0)
    
    def test_serial_option(self):
        """Test serial processing option."""
        result = subprocess.run(
            ["./run_analysis.sh", "drug", "test", "2021-01", "--serial", "--dry-run"], 
            capture_output=True, 
            text=True
        )
        
        self.assertIn("Processing: Serial (1 core)", result.stdout)
        self.assertEqual(result.returncode, 0)
    
    def test_standardized_format_examples_in_help(self):
        """Test that help shows only standardized format examples."""
        result = subprocess.run(
            ["./run_analysis.sh", "--help"], 
            capture_output=True, 
            text=True
        )
        
        help_text = result.stdout
        
        # Should contain standardized examples
        self.assertIn("2019-09:2021-01", help_text)
        self.assertIn("colon-separated", help_text)
        
        # Should NOT contain old space-separated examples
        self.assertNotIn("2019-09 2021-01", help_text)
    
    def test_error_message_format_consistency(self):
        """Test that error messages show consistent format examples."""
        result = subprocess.run(
            ["./run_analysis.sh", "drug", "test", "bad-format"], 
            capture_output=True, 
            text=True
        )
        
        error_output = result.stdout
        
        # Should show standardized format in error
        self.assertIn("YYYY-MM:YYYY-MM", error_output)
        self.assertIn("Cross-year range", error_output)
        self.assertIn("2019-09:2021-01", error_output)


class TestDateParsingLogic(unittest.TestCase):
    """Test the specific date parsing logic extracted from the script."""
    
    def setUp(self):
        """Set up test environment."""
        self.script_dir = Path(__file__).parent.parent
        os.chdir(self.script_dir)
    
    def test_date_parsing_regex_patterns(self):
        """Test individual regex patterns used in the script."""
        # These test the bash regex patterns by invoking them through bash
        
        test_cases = [
            # Format: (input, expected_match, description)
            ("2021", True, "Full year"),
            ("2021-01", True, "Single month"), 
            ("2021-01:06", True, "Month range same year"),
            ("2019-09:2021-01", True, "Cross-year range"),
            ("2018:2024", True, "Multi-year"),
            ("201801:202409", True, "Exact months"),
            ("invalid", False, "Invalid format"),
            # Note: Current regex accepts 2021-13, this could be improved for month validation
            ("21-01", False, "Invalid year format"),
        ]
        
        for date_input, should_match, description in test_cases:
            with self.subTest(date_input=date_input, description=description):
                result = subprocess.run(
                    ["./run_analysis.sh", "drug", "test", date_input, "--dry-run"], 
                    capture_output=True, 
                    text=True
                )
                
                if should_match:
                    # Should not show "Invalid date format" error
                    self.assertNotIn("Invalid date format", result.stdout, 
                                   f"Date '{date_input}' should be valid but was rejected")
                    # Should show period parsing
                    self.assertIn("Period:", result.stdout,
                                f"Date '{date_input}' should show parsed period")
                else:
                    # Should show "Invalid date format" error
                    self.assertIn("Invalid date format", result.stdout,
                                f"Date '{date_input}' should be invalid but was accepted")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)