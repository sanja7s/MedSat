#!/usr/bin/env python3
"""
Test script to validate the updated downloader configuration.
This script tests the JSON configuration without requiring external dependencies.
"""

import json
import os
import re

def test_json_configuration():
    """Test the updated JSON configuration file."""
    print("Testing updated JSON configuration...")
    
    with open('serialized_file_paths.json', 'r') as f:
        sources = json.load(f)
    
    print(f"Total sources: {len(sources)}")
    
    # Count different file types
    gz_files = [k for k in sources.keys() if k.endswith('.gz')]
    zip_files = [k for k in sources.keys() if k.endswith('.ZIP')]
    
    print(f"GZ files: {len(gz_files)}")
    print(f"ZIP files: {len(zip_files)}")
    
    print("\nNew ZIP entries:")
    for key in sorted(zip_files):
        print(f"  {key}")
    
    # Check date range coverage
    all_dates = []
    date_pattern = re.compile(r'^(\d{6})\.')
    
    for key in sources.keys():
        match = date_pattern.match(key)
        if match:
            all_dates.append(match.group(1))
    
    all_dates = sorted(set(all_dates))
    print(f"\nDate range coverage: {all_dates[0]} to {all_dates[-1]}")
    print(f"Total months covered: {len(all_dates)}")
    
    # Check for duplicates (same date with different formats)
    date_counts = {}
    for date in all_dates:
        date_counts[date] = 0
        if f"{date}.gz" in sources:
            date_counts[date] += 1
        if f"{date}.ZIP" in sources:
            date_counts[date] += 1
    
    overlap_dates = [date for date, count in date_counts.items() if count > 1]
    if overlap_dates:
        print(f"\nDates with both formats available: {overlap_dates}")
    
    # Validate URL formats
    print("\nValidating URL formats...")
    invalid_urls = []
    for key, url in sources.items():
        if not url.startswith('https://'):
            invalid_urls.append(key)
        if 'dl=0' in url:
            invalid_urls.append(f"{key} (uses dl=0 instead of dl=1)")
    
    if invalid_urls:
        print(f"URLs that need attention: {invalid_urls}")
    else:
        print("All URLs look valid!")
    
    print("\nConfiguration test completed successfully!")
    return True

def test_downloader_compatibility():
    """Test compatibility with the downloader class structure."""
    print("\nTesting downloader compatibility...")
    
    # Test the year_source mapping logic
    with open('serialized_file_paths.json', 'r') as f:
        sources = json.load(f)
    
    year_source = {}
    for key, value in sources.items():
        year = key.split(".")[0]
        year_source[year] = value
    
    print(f"Year mapping created with {len(year_source)} entries")
    print(f"Available years: {sorted(year_source.keys())[-10:]}")
    
    # Test date format validation
    def is_date_format(input_string):
        pattern = re.compile('^(19|20)\d\d(0[1-9]|1[0-2])$')
        return bool(pattern.match(input_string))
    
    test_dates = ['202101', '202103', '202106', '202112', '202113', 'invalid']
    print("\nTesting date format validation:")
    for date in test_dates:
        valid = is_date_format(date)
        available = date in year_source
        print(f"  {date}: format_valid={valid}, available={available}")
    
    print("Compatibility test completed!")
    return True

if __name__ == "__main__":
    test_json_configuration()
    test_downloader_compatibility()