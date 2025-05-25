
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
