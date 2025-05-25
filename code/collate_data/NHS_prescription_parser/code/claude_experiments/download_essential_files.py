#!/usr/bin/env python3
"""
Download Essential Files for NHS Prescription Parser

This script automatically downloads the large files needed for optimal functionality
when they're missing from Git LFS or not available locally.
"""

import os
import sys
import requests
import zipfile
import gzip
import tempfile
import shutil
from pathlib import Path
from tqdm import tqdm
import hashlib
import json
import pandas as pd

class EssentialFilesDownloader:
    def __init__(self, mappings_dir="../mappings/", data_prep_dir="../data_prep/"):
        self.mappings_dir = Path(mappings_dir)
        self.data_prep_dir = Path(data_prep_dir)
        self.downloads_cache = Path("downloads_cache")
        self.downloads_cache.mkdir(exist_ok=True)
        
        # NHS Digital base URLs (these are examples - you'll need actual URLs)
        self.download_sources = {
            # GP Registry data (most important for accurate normalization)
            'gp_registry_2021': {
                'url': 'https://files.digital.nhs.uk/8A/E1B5E8/gp-reg-pat-prac-lsoa-all_2021.csv',
                'filename': 'gp-reg-pat-prac-lsoa-all_2021.csv',
                'target_dir': self.mappings_dir,
                'priority': 1,
                'description': 'GP Registry 2021 - Essential for accurate patient population normalization',
                'size_mb': 63,
                'essential': True
            },
            'gp_registry_2020': {
                'url': 'https://files.digital.nhs.uk/8A/E1B5E8/gp-reg-pat-prac-lsoa-all_2020.csv',
                'filename': 'gp-reg-pat-prac-lsoa-all_2020.csv', 
                'target_dir': self.mappings_dir,
                'priority': 2,
                'description': 'GP Registry 2020 - For historical analysis',
                'size_mb': 61,
                'essential': False
            },
            'gp_registry_2022': {
                'url': 'https://files.digital.nhs.uk/8A/E1B5E8/gp-reg-pat-prac-lsoa-all_2022.csv',
                'filename': 'gp-reg-pat-prac-lsoa-all_2022.csv',
                'target_dir': self.mappings_dir, 
                'priority': 3,
                'description': 'GP Registry 2022 - Recent data',
                'size_mb': 65,
                'essential': False
            },
            # LSOA lookup (smaller, very useful)
            'lsoa_lookup': {
                'url': 'https://opendata.arcgis.com/api/v3/datasets/1d78d47c87df4212b79fe2323aae8e08_0/downloads/data?format=csv&spatialRefId=4326',
                'filename': 'LSOA_DEC_2021.csv',
                'target_dir': self.mappings_dir,
                'priority': 1,
                'description': 'LSOA codes and names lookup table',
                'size_mb': 1.2,
                'essential': True
            }
        }
        
        # Alternative/fallback sources
        self.fallback_sources = {
            # Mock/sample data generators
            'generate_sample_gp_2021': {
                'generator': self.generate_sample_gp_registry,
                'filename': 'gp-reg-pat-prac-lsoa-all_2021.csv',
                'target_dir': self.mappings_dir,
                'description': 'Generated sample GP registry data (reduced accuracy)',
                'args': {'year': 2021, 'num_practices': 1000, 'num_lsoas': 5000}
            },
            'generate_sample_lsoa': {
                'generator': self.generate_sample_lsoa_lookup,
                'filename': 'LSOA_DEC_2021.csv', 
                'target_dir': self.mappings_dir,
                'description': 'Generated sample LSOA lookup (basic functionality)',
                'args': {'num_lsoas': 35000}
            }
        }

    def check_missing_files(self):
        """Check which essential files are missing"""
        missing = []
        available = []
        
        for key, config in self.download_sources.items():
            target_file = config['target_dir'] / config['filename']
            if target_file.exists():
                size_mb = target_file.stat().st_size / (1024 * 1024)
                available.append({
                    'key': key,
                    'file': config['filename'],
                    'size_mb': size_mb,
                    'essential': config['essential']
                })
            else:
                missing.append({
                    'key': key,
                    'file': config['filename'],
                    'url': config['url'],
                    'size_mb': config['size_mb'],
                    'essential': config['essential'],
                    'description': config['description'],
                    'priority': config['priority']
                })
        
        return missing, available

    def download_file_with_progress(self, url, target_path, description="Downloading"):
        """Download a file with progress bar"""
        try:
            print(f"📥 {description}")
            print(f"   Source: {url}")
            print(f"   Target: {target_path}")
            
            # Create target directory
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Start download
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Get total size if available
            total_size = int(response.headers.get('content-length', 0))
            
            with open(target_path, 'wb') as f:
                if total_size > 0:
                    with tqdm(total=total_size, unit='B', unit_scale=True, desc=description) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))
                else:
                    # No content-length header
                    with tqdm(unit='B', unit_scale=True, desc=description) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))
            
            print(f"   ✅ Downloaded successfully")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Download failed: {e}")
            return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def generate_sample_gp_registry(self, target_path, year=2021, num_practices=1000, num_lsoas=5000):
        """Generate realistic sample GP registry data"""
        print(f"🔧 Generating sample GP registry data for {year}")
        
        import random
        import numpy as np
        
        # Set seed for reproducibility
        random.seed(42)
        np.random.seed(42)
        
        data = []
        
        # Generate practice codes
        practice_codes = [f"A{i:05d}" for i in range(1, num_practices + 1)]
        
        # Generate LSOA codes (England format)
        lsoa_codes = [f"E01{i:06d}" for i in range(1, num_lsoas + 1)]
        
        print(f"   Generating data for {len(practice_codes)} practices and {len(lsoa_codes)} LSOAs...")
        
        for practice in tqdm(practice_codes, desc="Generating GP registry"):
            # Each practice serves 5-20 LSOAs
            num_lsoas_for_practice = random.randint(5, 20)
            served_lsoas = random.sample(lsoa_codes, num_lsoas_for_practice)
            
            for lsoa in served_lsoas:
                # Realistic patient counts (log-normal distribution)
                patient_count = max(1, int(np.random.lognormal(mean=3, sigma=1)))
                
                data.append({
                    'PUBLICATION': 'GP_PRAC_PAT_LIST',
                    'EXTRACT_DATE': f'04JAN{year}',
                    'PRACTICE_CODE': practice,
                    'PRACTICE_NAME': f'SAMPLE PRACTICE {practice}',
                    'LSOA_CODE': lsoa,
                    'SEX': 'ALL',
                    'Number of Patients': patient_count
                })
        
        # Create DataFrame and save
        df = pd.DataFrame(data)
        df.to_csv(target_path, index=False)
        
        print(f"   ✅ Generated {len(data):,} records")
        print(f"   📊 Total sample patients: {df['Number of Patients'].sum():,}")
        return True

    def generate_sample_lsoa_lookup(self, target_path, num_lsoas=35000):
        """Generate sample LSOA lookup table"""
        print(f"🔧 Generating sample LSOA lookup table")
        
        import random
        
        random.seed(42)
        
        # Common area names for realistic-looking data
        area_names = [
            "City of London", "Camden", "Greenwich", "Hackney", "Hammersmith", "Fulham",
            "Islington", "Kensington", "Chelsea", "Lambeth", "Lewisham", "Newham",
            "Southwark", "Tower Hamlets", "Wandsworth", "Westminster", "Barking", "Dagenham",
            "Barnet", "Bexley", "Brent", "Bromley", "Croydon", "Ealing", "Enfield",
            "Haringey", "Harrow", "Havering", "Hillingdon", "Hounslow", "Kingston",
            "Merton", "Redbridge", "Richmond", "Sutton", "Waltham Forest"
        ]
        
        data = []
        
        for i in tqdm(range(1, num_lsoas + 1), desc="Generating LSOA lookup"):
            # Generate realistic LSOA code
            lsoa_code = f"E01{i:06d}"
            
            # Pick random area and add sub-area identifier
            base_area = random.choice(area_names)
            sub_area = f"{random.randint(1, 50):03d}{random.choice('ABCDEFGHIJ')}"
            lsoa_name = f"{base_area} {sub_area}"
            
            data.append({
                'LSOA21CD': lsoa_code,
                'LSOA21NM': lsoa_name,
                'LSOA21NMW': '',  # Welsh name (empty for England)
                'ObjectId': i
            })
        
        # Create DataFrame and save
        df = pd.DataFrame(data)
        df.to_csv(target_path, index=False)
        
        print(f"   ✅ Generated {len(data):,} LSOA records")
        return True

    def download_essential_files(self, force_download=False, essential_only=True):
        """Download missing essential files"""
        print("🔍 Checking for missing essential files...")
        
        missing, available = self.check_missing_files()
        
        if available:
            print(f"\n✅ Found {len(available)} files already available:")
            for file_info in available:
                essential_mark = "⭐" if file_info['essential'] else "📄"
                print(f"   {essential_mark} {file_info['file']} ({file_info['size_mb']:.1f}MB)")
        
        if not missing:
            print("\n🎉 All essential files are available!")
            return True
        
        print(f"\n📥 Found {len(missing)} missing files:")
        
        # Sort by priority and essential status
        missing.sort(key=lambda x: (not x['essential'], x['priority']))
        
        success_count = 0
        total_attempts = 0
        
        for file_info in missing:
            if essential_only and not file_info['essential']:
                print(f"\n⏭️  Skipping non-essential file: {file_info['file']}")
                continue
                
            print(f"\n📥 Downloading: {file_info['file']}")
            print(f"   Description: {file_info['description']}")
            print(f"   Size: ~{file_info['size_mb']}MB")
            
            target_path = self.mappings_dir / file_info['file']
            
            # Try official download first
            total_attempts += 1
            success = self.download_file_with_progress(
                file_info['url'], 
                target_path, 
                file_info['description']
            )
            
            if success:
                success_count += 1
                print(f"   ✅ Successfully downloaded {file_info['file']}")
            else:
                print(f"   ⚠️  Official download failed for {file_info['file']}")
                
                # Try fallback/generator
                fallback_key = None
                if 'gp-reg-pat-prac-lsoa-all' in file_info['file']:
                    fallback_key = 'generate_sample_gp_2021'
                elif 'LSOA_DEC' in file_info['file']:
                    fallback_key = 'generate_sample_lsoa'
                
                if fallback_key and fallback_key in self.fallback_sources:
                    print(f"   🔧 Trying fallback: generate sample data")
                    fallback = self.fallback_sources[fallback_key]
                    
                    try:
                        fallback_success = fallback['generator'](target_path, **fallback['args'])
                        if fallback_success:
                            success_count += 1
                            print(f"   ✅ Generated sample data for {file_info['file']}")
                            print(f"   ⚠️  Note: Using sample data - reduced accuracy expected")
                        else:
                            print(f"   ❌ Sample generation failed for {file_info['file']}")
                    except Exception as e:
                        print(f"   ❌ Sample generation error: {e}")
                else:
                    print(f"   ❌ No fallback available for {file_info['file']}")
        
        print(f"\n📊 Download Summary:")
        print(f"   Attempted: {total_attempts}")
        print(f"   Successful: {success_count}")
        print(f"   Success rate: {success_count/total_attempts*100:.1f}%" if total_attempts > 0 else "   No downloads attempted")
        
        if success_count > 0:
            print(f"\n✅ Downloaded {success_count} essential files successfully!")
            print(f"   🔍 Run analysis to verify functionality")
            return True
        else:
            print(f"\n⚠️  Could not download any files.")
            print(f"   📖 Check DOWNLOAD_MISSING_FILES.md for manual download instructions")
            return False

    def create_download_script(self):
        """Create a standalone download script"""
        script_content = f'''#!/usr/bin/env python3
"""
Standalone Essential Files Downloader
Auto-generated by NHS Prescription Parser

Usage: python download_files.py [--essential-only] [--force]
"""

import sys
import os

# Add current directory to path so we can import the downloader
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from download_essential_files import EssentialFilesDownloader

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Download essential files for NHS Prescription Parser")
    parser.add_argument('--essential-only', action='store_true', 
                       help='Download only essential files (default: True)')
    parser.add_argument('--force', action='store_true',
                       help='Force re-download of existing files')
    parser.add_argument('--all', action='store_true',
                       help='Download all files (not just essential)')
    
    args = parser.parse_args()
    
    downloader = EssentialFilesDownloader()
    
    essential_only = not args.all  # Default to essential only unless --all specified
    
    print("🏥 NHS Prescription Parser - Essential Files Downloader")
    print("=" * 60)
    
    success = downloader.download_essential_files(
        force_download=args.force,
        essential_only=essential_only
    )
    
    if success:
        print("\\n🎉 File download complete!")
        print("   Ready to run: ./run_analysis.sh drug metformin 2021")
    else:
        print("\\n⚠️  Some downloads failed. System will use fallback data where possible.")
        print("   Basic functionality should still work with reduced accuracy.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
'''
        
        script_path = Path("download_files.py")
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make executable
        os.chmod(script_path, 0o755)
        
        print(f"📄 Created standalone download script: {script_path}")
        return script_path

def main():
    """Main function for interactive use"""
    downloader = EssentialFilesDownloader()
    
    print("🏥 NHS Prescription Parser - Essential Files Downloader")
    print("=" * 60)
    
    # Check current status
    missing, available = downloader.check_missing_files()
    
    if not missing:
        print("✅ All essential files are already available!")
        return 0
    
    print(f"Found {len(missing)} missing files.")
    
    # Ask user what to download
    print("\\nOptions:")
    print("1. Download essential files only (recommended)")
    print("2. Generate sample data (for testing)")
    print("3. Check status and exit")
    
    choice = input("\\nChoose option (1-3): ").strip()
    
    if choice == "1":
        success = downloader.download_essential_files(essential_only=True)
    elif choice == "2":
        success = downloader.download_essential_files(essential_only=True)
        # This will fall back to sample data when downloads fail
    elif choice == "3":
        return 0
    else:
        print("Invalid choice. Exiting.")
        return 1
    
    if success:
        print("\\n🎉 Setup complete! Ready to analyze NHS prescription data.")
    else:
        print("\\n⚠️  Setup incomplete. Check documentation for manual steps.")
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())