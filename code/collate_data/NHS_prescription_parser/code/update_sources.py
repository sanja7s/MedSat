#!/usr/bin/env python3
"""
Script to update the serialized_file_paths.json file with local EPD files.
This is necessary because the original code expects URLs to download,
but we want to use local files instead.
"""

import json
import os
import argparse
import re


def update_sources_file(sources_file, epd_dir, start_date=None, end_date=None):
    """
    Update the serialized_file_paths.json file with local EPD files.
    
    Args:
        sources_file: Path to the serialized_file_paths.json file
        epd_dir: Directory containing processed EPD files
        start_date: Optional start date (YYYYMM) to limit the update
        end_date: Optional end date (YYYYMM) to limit the update
    """
    # Load existing sources file
    with open(sources_file, 'r') as f:
        sources = json.load(f)
    
    # Get list of processed EPD files
    epd_files = [f for f in os.listdir(epd_dir) if f.endswith('.gz')]
    
    # Extract dates from filenames (assuming format YYYYMM.gz)
    date_pattern = re.compile(r'(\d{6})\.gz')
    new_sources = {}
    
    for file in epd_files:
        match = date_pattern.match(file)
        if match:
            date = match.group(1)
            
            # Check if date is within specified range
            if start_date and date < start_date:
                continue
            if end_date and date > end_date:
                continue
                
            # Create a file:// URL for the local file
            file_path = os.path.abspath(os.path.join(epd_dir, file))
            new_sources[f"{date}.gz"] = f"file://{file_path}"
    
    # Update sources dictionary with new entries
    sources.update(new_sources)
    
    # Write updated sources back to file
    with open(sources_file, 'w') as f:
        json.dump(sources, f, indent=4)
    
    print(f"Updated {sources_file} with {len(new_sources)} new entries.")
    print(f"New date range: {min(sources.keys())} to {max(sources.keys())}")


def main():
    parser = argparse.ArgumentParser(description='Update serialized_file_paths.json with local EPD files')
    parser.add_argument('--sources-file', default='./sources/serialized_file_paths.json',
                        help='Path to the serialized_file_paths.json file')
    parser.add_argument('--epd-dir', default='./prescriptionfiles',
                        help='Directory containing processed EPD files')
    parser.add_argument('--start-date', help='Start date (YYYYMM) to limit the update')
    parser.add_argument('--end-date', help='End date (YYYYMM) to limit the update')
    
    args = parser.parse_args()
    
    update_sources_file(args.sources_file, args.epd_dir, args.start_date, args.end_date)


if __name__ == "__main__":
    main()