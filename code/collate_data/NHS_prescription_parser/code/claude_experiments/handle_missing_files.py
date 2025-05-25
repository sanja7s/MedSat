#!/usr/bin/env python3
"""
Handle Missing Large Files - Fallback Strategy

This script provides fallback mechanisms when large mapping files 
are not available due to Git LFS issues or missing files.
"""

import os
import json
import pandas as pd
from pathlib import Path

def check_file_availability(mappings_dir):
    """
    Check which essential mapping files are available.
    
    Returns:
        dict: Availability status of key files
    """
    files_to_check = {
        # Large CSV files (may be missing if LFS not set up)
        'gp_csv_2020': 'gp-reg-pat-prac-lsoa-all_2020.csv',
        'gp_csv_2021': 'gp-reg-pat-prac-lsoa-all_2021.csv', 
        'gp_csv_2022': 'gp-reg-pat-prac-lsoa-all_2022.csv',
        'gp_csv_2023': 'gp-reg-pat-prac-lsoa-all_2023.csv',
        'gp_csv_2024': 'gp-reg-pat-prac-lsoa-all_2024.csv',
        'gp_csv_2025': 'gp-reg-pat-prac-lsoa-all_2025.csv',
        'census_2021': 'census2021_lsoa_level.xlsx',
        'lsoa_lookup': 'LSOA_DEC_2021.csv',
        
        # Fallback JSON files (should always be available)
        'gp_json': 'GPs.json',
        'gp_json_2013': 'GPs_2013.json',
        'gp_dist_json': 'GP_LSOA_PATIENTSDIST.json',
        'gp_dist_2021_json': 'GP_LSOA_PATIENTSDIST_2021.json',
    }
    
    availability = {}
    for key, filename in files_to_check.items():
        filepath = os.path.join(mappings_dir, filename)
        availability[key] = {
            'filename': filename,
            'exists': os.path.exists(filepath),
            'size_mb': os.path.getsize(filepath) / (1024*1024) if os.path.exists(filepath) else 0
        }
    
    return availability

def create_download_instructions():
    """
    Create instructions for downloading missing large files.
    """
    instructions = """
# Large File Download Instructions

## Missing Files Detected

The following large files are required for optimal functionality but are missing 
from your local repository. This is likely because:

1. Git LFS (Large File Storage) is not configured
2. Files exceed GitHub's size limits and weren't committed
3. This is a fresh clone without LFS data

## Required Files

### GP Registry Data (CSV format - most accurate)
- `gp-reg-pat-prac-lsoa-all_2020.csv` (59MB)
- `gp-reg-pat-prac-lsoa-all_2021.csv` (60MB) 
- `gp-reg-pat-prac-lsoa-all_2022.csv` (62MB)
- `gp-reg-pat-prac-lsoa-all_2023.csv` (62MB)
- `gp-reg-pat-prac-lsoa-all_2024.csv` (63MB)
- `gp-reg-pat-prac-lsoa-all_2025.csv` (86MB)

### Census and Lookup Data
- `census2021_lsoa_level.xlsx` (109MB)
- `LSOA_DEC_2021.csv` (1.2MB)

## Download Sources

### Option 1: NHS Digital
Visit: https://digital.nhs.uk/data-and-information/publications/statistical/patients-registered-at-a-gp-practice

### Option 2: Office for National Statistics
Visit: https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates

### Option 3: Project Maintainer
Contact the project maintainer for access to processed files.

## Fallback Operation

The system will continue to work using legacy JSON files but with:
- Less accurate patient population data
- Limited year coverage (2013, 2021 only)
- Potentially missing some LSOAs

## Setup Git LFS (Recommended)

```bash
# Install Git LFS
brew install git-lfs  # macOS
# or: apt-get install git-lfs  # Ubuntu

# Initialize in repository
git lfs install

# Pull LFS files
git lfs pull
```
"""
    
    return instructions

def get_operational_status(mappings_dir):
    """
    Determine what level of functionality is available.
    """
    availability = check_file_availability(mappings_dir)
    
    # Check if any CSV files are available
    csv_available = any(availability[key]['exists'] for key in availability.keys() if 'gp_csv' in key)
    
    # Check if fallback JSON files are available
    json_available = availability['gp_json']['exists'] and availability['gp_dist_json']['exists']
    
    # Check essential lookup files
    lookup_available = availability['lsoa_lookup']['exists']
    
    status = {
        'csv_data_available': csv_available,
        'json_fallback_available': json_available,
        'lookup_available': lookup_available,
        'operational_level': 'unknown'
    }
    
    if csv_available and lookup_available:
        status['operational_level'] = 'optimal'
        status['description'] = 'All CSV files available - highest accuracy'
    elif json_available and lookup_available:
        status['operational_level'] = 'good'
        status['description'] = 'JSON fallback available - good accuracy'
    elif json_available:
        status['operational_level'] = 'basic'
        status['description'] = 'Basic functionality - limited accuracy'
    else:
        status['operational_level'] = 'critical'
        status['description'] = 'Missing essential files - system may not work'
    
    return status

def generate_missing_files_report(mappings_dir="../mappings/"):
    """
    Generate a comprehensive report of missing files and recommendations.
    """
    print("MISSING FILES ANALYSIS")
    print("=" * 50)
    
    availability = check_file_availability(mappings_dir)
    status = get_operational_status(mappings_dir)
    
    print(f"Operational Level: {status['operational_level'].upper()}")
    print(f"Description: {status['description']}")
    print()
    
    print("FILE AVAILABILITY:")
    print("-" * 30)
    
    missing_files = []
    for key, info in availability.items():
        status_icon = "✅" if info['exists'] else "❌"
        size_info = f"({info['size_mb']:.1f}MB)" if info['exists'] else "(missing)"
        print(f"{status_icon} {info['filename']} {size_info}")
        
        if not info['exists']:
            missing_files.append(info['filename'])
    
    if missing_files:
        print(f"\n⚠️  MISSING {len(missing_files)} FILES:")
        for filename in missing_files:
            print(f"   - {filename}")
        
        print("\nRECOMMENDATIONS:")
        print("1. Set up Git LFS and pull large files")
        print("2. Download missing files manually")
        print("3. Contact project maintainer for file access")
        print("4. System will use fallback data where possible")
        
        # Write instructions file
        instructions = create_download_instructions()
        with open("DOWNLOAD_MISSING_FILES.md", "w") as f:
            f.write(instructions)
        print("\n📄 Detailed instructions written to: DOWNLOAD_MISSING_FILES.md")
    
    else:
        print("\n✅ All essential files are available!")
    
    return availability, status

def main():
    """Main function to run missing files analysis"""
    mappings_dir = "../mappings/"
    
    if not os.path.exists(mappings_dir):
        print(f"❌ Mappings directory not found: {mappings_dir}")
        return
    
    availability, status = generate_missing_files_report(mappings_dir)
    
    print(f"\n{'='*50}")
    print("SYSTEM STATUS SUMMARY")
    print(f"{'='*50}")
    print(f"Status: {status['operational_level'].upper()}")
    print(f"CSV Data: {'✅ Available' if status['csv_data_available'] else '❌ Missing'}")
    print(f"JSON Fallback: {'✅ Available' if status['json_fallback_available'] else '❌ Missing'}")
    print(f"Lookup Data: {'✅ Available' if status['lookup_available'] else '❌ Missing'}")

if __name__ == "__main__":
    main()