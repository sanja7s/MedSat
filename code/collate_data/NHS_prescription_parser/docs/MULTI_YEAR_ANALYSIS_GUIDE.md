# Multi-Year Analysis Guide

## Fixed Issues and Solutions

### Problem 1: run_analysis.sh didn't support multi-year ranges
**Solution**: Added multi-year support with `YYYY:YYYY` format

### Problem 2: run_extended.py command syntax was unclear
**Solution**: Documented correct subcommand syntax

## Working Commands

### Option 1: Enhanced run_analysis.sh (Recommended for most cases)

```bash
cd code

# Multi-year range (all months from 2018 to 2021)
./run_analysis.sh drug metformin 2018:2021

# Multi-year condition analysis  
./run_analysis.sh condition asthma 2018:2021

# Multi-year custom list
./run_analysis.sh custom sample_list_antidepressants.json 2018:2021
```

**Supported year formats:**
- `2021` - Full year (Jan-Dec 2021)
- `2021-01` - Single month (Jan 2021) 
- `2021-01:06` - Month range within year (Jan-Jun 2021)
- `2018:2021` - **NEW**: Multi-year range (Jan 2018 - Dec 2021)

### Option 2: run_extended.py (For advanced features)

```bash
cd code
source ../venv/bin/activate

# Condition analysis with extended features
python run_extended.py condition -c asthma -s 201801 -e 202409

# Drug analysis with extended features
python run_extended.py drug -d metformin -s 201801 -e 202409 -y 2021

# Custom list with extended features
python run_extended.py list -l sample_list_antidepressants.json -s 202101 -e 202112 -y 2021

# Opioid analysis with OME calculations
python run_extended.py opioid -d tramadol -s 202101 -e 202112 -y 2021
```

**Key differences:**
- `run_extended.py` uses YYYYMM format for dates (e.g., 201801, 202409)
- `run_extended.py` supports year parameter (-y) for LSOA mapping
- `run_extended.py` has specialized opioid analysis with OME calculations

## Example Usage for Your Case

For analyzing asthma from 201801 to 202409:

**Option A (Simple):**
```bash
./run_analysis.sh condition asthma 2018:2024
```

**Option B (Extended features):**
```bash
python run_extended.py condition -c asthma -s 201801 -e 202409 -y 2021
```

## Performance Note

Multi-year analysis takes significant time:
- Each month takes ~30-60 seconds to process
- 3-year range (36 months) ≈ 30-60 minutes total
- Progress bars show current status

## Output

Both commands create the same output format:
- Files saved to `../data_prep/`
- CSV.gz format with LSOA-level prevalence data
- One file per drug/condition analyzed