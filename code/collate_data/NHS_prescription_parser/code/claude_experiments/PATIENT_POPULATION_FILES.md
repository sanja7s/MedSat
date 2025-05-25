# Patient Population Files for Normalization

This document lists the essential CSV and JSON files required for proper per-capita normalization in the NHS prescription prevalence analysis.

## ✅ Critical Files (All Tracked in Git)

### 1. GP-LSOA Patient Distribution (mappings/)

**Primary Files:**
- `GP_LSOA_PATIENTSDIST.json` (27.3 MB) - Original GP to LSOA patient distribution
- `GP_LSOA_PATIENTSDIST_2021.json` (30.4 MB) - 2021 GP to LSOA patient distribution

**Purpose:** Maps GP practices to LSOA codes with patient population weights for distributing prescriptions geographically.

**Usage:** Used by `prepare_lsoa_GP_population()` and `load_lsoa_mappings()` functions in `commonFunc_updated.py`

### 2. GP Registry Files (mappings/)

**Files:**
- `GPs.json` (17.0 MB) - Current GP practice registry with patient populations
- `GPs_2013.json` (15.0 MB) - Historical GP practice registry (2013)

**Purpose:** Contains GP practice codes with their registered patient populations by LSOA.

**Structure:**
```json
{
  "GP_CODE": {
    "Patient_registry_LSOA": {
      "LSOA_CODE": patient_count,
      ...
    }
  }
}
```

### 3. GP Practice Registry (mappings/)

**Files:**
- `epraccur.csv` (3.1 MB) - GP practice details (historical)
- `epraccur_2021.csv` (3.2 MB) - GP practice details (2021)
- `GP_LSOA_weights_2013.csv` - Historical weighting factors

**Purpose:** Additional GP practice metadata and weighting factors for historical analysis.

## 📊 Patient Population Data Sources

### Year-Specific Usage
The system correctly uses year-appropriate patient populations:

- **Pre-2021 data:** Uses `GP_LSOA_PATIENTSDIST.json` and `GPs.json`
- **2021+ data:** Uses `GP_LSOA_PATIENTSDIST_2021.json` and updated mappings

### Normalization Formula
```
Total_X_per_capita = Total_X / Patient_count
```

Where `Patient_count` comes from the year-appropriate GP registry files.

## 🔍 File Verification

### File Sizes (as of tracking)
```bash
-rwxr-xr-x  27,356,055 bytes  GP_LSOA_PATIENTSDIST.json
-rwxr-xr-x  30,413,874 bytes  GP_LSOA_PATIENTSDIST_2021.json  
-rw-r--r--  16,959,963 bytes  GPs.json
-rw-r--r--  15,024,317 bytes  GPs_2013.json
-rwxr-xr-x   3,069,429 bytes  epraccur.csv
-rwxr-xr-x   3,194,697 bytes  epraccur_2021.csv
```

### Git Status: ✅ All Essential Files Tracked
```bash
git ls-files ../mappings/ | grep -E "(GP|LSOA|PATIENT|epraccur)"
../mappings/GP_LSOA_PATIENTSDIST.json
../mappings/GP_LSOA_PATIENTSDIST_2021.json
../mappings/GP_LSOA_weights_2013.csv
../mappings/GPs.json
../mappings/GPs_2013.json
../mappings/epraccur.csv
../mappings/epraccur_2021.csv
```

## 🚨 Critical for Statistical Validity

These files are **essential** for:

1. **Proper normalization**: Without year-specific patient populations, per-capita calculations would be invalid
2. **Geographic accuracy**: GP-LSOA mappings ensure prescriptions are correctly attributed to residential areas
3. **Temporal consistency**: Year-specific files account for population changes over time
4. **Statistical rigor**: Correlation analyses depend on consistent normalization methodology

## ⚠️ What's NOT Tracked (Intentionally)

The following files in `data_prep/` are excluded from git due to size:
- `gp-reg-pat-prac-lsoa-all_YYYY.csv` (60-90 MB each) - Raw NHS GP registry data
- `census2021_lsoa_level.xlsx` (114 MB) - Census data
- `EPD_202110.ZIP` (567 MB) - Prescription data files

These are **source data** that can be re-downloaded, whereas the mappings files contain processed/curated data essential for the analysis pipeline.

## 📝 Verification Commands

To verify all essential files are present and tracked:

```bash
# Check tracking status
git ls-files ../mappings/ | grep -E "(GP|LSOA|PATIENT|epraccur)"

# Verify file sizes
ls -la ../mappings/GP_LSOA_PATIENTSDIST*.json ../mappings/GPs*.json ../mappings/epraccur*.csv

# Test loading in Python
python -c "
import json
gp_dist = json.load(open('../mappings/GP_LSOA_PATIENTSDIST_2021.json'))
print(f'GP practices: {len(gp_dist)}')
total_lsoas = sum(len(practice.keys()) for practice in gp_dist.values())
print(f'Total GP-LSOA mappings: {total_lsoas}')
"
```

---
*This documentation ensures proper statistical validation and reproducibility of the NHS prescription prevalence analysis.*