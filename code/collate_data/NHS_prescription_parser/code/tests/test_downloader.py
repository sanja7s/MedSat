#!/usr/bin/env python3
"""
Unit tests for the downloader functionality.
"""

import unittest
import os
import tempfile
import json
import zipfile
import gzip
import shutil
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sources.downloader import Downloader


class TestDownloader(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.sources_file = os.path.join(self.temp_dir, 'test_sources.json')
        self.download_dir = os.path.join(self.temp_dir, 'downloads')
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Create test sources file
        test_sources = {
            "202001.gz": "https://example.com/202001.gz",
            "202002.gz": "https://example.com/202002.gz",
            "202103.ZIP": "https://example.com/EPD_202103.ZIP"
        }
        with open(self.sources_file, 'w') as f:
            json.dump(test_sources, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test downloader initialization."""
        downloader = Downloader(self.sources_file, self.download_dir)
        
        self.assertEqual(len(downloader.sources), 3)
        self.assertEqual(len(downloader.year_source), 3)
        self.assertIn("202001", downloader.year_source)
        self.assertIn("202002", downloader.year_source)
        self.assertIn("202103", downloader.year_source)
    
    def test_date_format_validation(self):
        """Test date format validation."""
        downloader = Downloader(self.sources_file, self.download_dir)
        
        # Valid dates
        self.assertTrue(downloader.is_date_format_("202001"))
        self.assertTrue(downloader.is_date_format_("201412"))
        
        # Invalid dates
        self.assertFalse(downloader.is_date_format_("20200"))
        self.assertFalse(downloader.is_date_format_("202013"))
        self.assertFalse(downloader.is_date_format_("invalid"))
    
    def test_generate_dates(self):
        """Test date range generation."""
        downloader = Downloader(self.sources_file, self.download_dir)
        
        dates = downloader.generate_dates("202001", "202003")
        expected = ["202001", "202002", "202003"]
        self.assertEqual(dates, expected)
        
        # Single month
        dates = downloader.generate_dates("202001", "202001")
        self.assertEqual(dates, ["202001"])
    
    def test_takestock(self):
        """Test file caching functionality."""
        # Create some test files
        gz_file = os.path.join(self.download_dir, "202001.gz")
        zip_file = os.path.join(self.download_dir, "202103.ZIP")
        
        with open(gz_file, 'w') as f:
            f.write("test")
        with open(zip_file, 'w') as f:
            f.write("test")
        
        downloader = Downloader(self.sources_file, self.download_dir)
        downloader.takestock_()
        
        self.assertIn("202001", downloader.cache)
        self.assertIn("202103", downloader.cache)
    
    def test_extract_and_process_zip(self):
        """Test ZIP file extraction and processing."""
        downloader = Downloader(self.sources_file, self.download_dir)
        
        # Create a test ZIP file with CSV content
        test_csv_content = "col1,col2,col3\n1,2,3\n4,5,6\n"
        zip_path = os.path.join(self.download_dir, "test_202103.ZIP")
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.writestr("EPD_202103.csv", test_csv_content)
        
        # Test extraction
        result = downloader.extract_and_process_zip(zip_path, "202103")
        
        self.assertIsNotNone(result)
        self.assertTrue(result.endswith("202103.gz"))
        self.assertTrue(os.path.exists(result))
        
        # Verify content
        with gzip.open(result, 'rt') as f:
            content = f.read()
            self.assertEqual(content, test_csv_content)
    
    @patch('sources.downloader.requests.get')
    def test_download_file(self, mock_get):
        """Test file download functionality."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b'test content']
        mock_get.return_value = mock_response
        
        downloader = Downloader(self.sources_file, self.download_dir)
        result = downloader.download_file("https://example.com/test.gz")
        
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(result))
        
        # Test failed download
        mock_response.status_code = 404
        result = downloader.download_file("https://example.com/notfound.gz")
        self.assertIsNone(result)


class TestDownloaderIntegration(unittest.TestCase):
    """Integration tests for downloader with real-like scenarios."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.sources_file = os.path.join(self.temp_dir, 'test_sources.json')
        self.download_dir = os.path.join(self.temp_dir, 'downloads')
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Create comprehensive test sources
        test_sources = {
            "202001.gz": "https://example.com/202001.gz",
            "202002.gz": "https://example.com/202002.gz", 
            "202101.gz": "https://example.com/202101.gz",
            "202101.ZIP": "https://example.com/EPD_202101.ZIP",
            "202102.ZIP": "https://example.com/EPD_202102.ZIP"
        }
        with open(self.sources_file, 'w') as f:
            json.dump(test_sources, f)
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_download_range_validation(self):
        """Test download range validation."""
        downloader = Downloader(self.sources_file, self.download_dir)
        
        # Valid range
        try:
            # This will fail because we're not actually downloading
            downloader.download_range("202001", "202002")
        except Exception:
            pass  # Expected to fail in test environment
        
        # Invalid date format
        with self.assertRaises(ValueError):
            downloader.download_range("invalid", "202002")
        
        # Out of range dates
        with self.assertRaises(ValueError):
            downloader.download_range("199901", "199902")


if __name__ == '__main__':
    unittest.main()