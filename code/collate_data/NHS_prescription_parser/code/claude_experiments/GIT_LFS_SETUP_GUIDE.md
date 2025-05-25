# Git LFS Setup Guide for Large Mapping Files

## ❌ Issue Encountered
Large mapping files (58-109MB) exceed GitHub's file size limits:
- Files >50MB get warnings  
- Files >100MB are rejected completely

## ✅ Solution: Git LFS (Large File Storage)

### 1. Install Git LFS
```bash
# Install Git LFS
brew install git-lfs

# Initialize LFS in repository
git lfs install
```

### 2. Configure .gitattributes
Create `.gitattributes` in repository root:
```gitattributes
# Large mapping files (CSV > 50MB)
**/mappings/gp-reg-pat-prac-lsoa-all_*.csv filter=lfs diff=lfs merge=lfs -text
**/mappings/census2021_lsoa_level.xlsx filter=lfs diff=lfs merge=lfs -text
**/mappings/GP_LSOA_weights_*.csv filter=lfs diff=lfs merge=lfs -text

# Other large files
*.zip filter=lfs diff=lfs merge=lfs -text
*.gz filter=lfs diff=lfs merge=lfs -text
**/*_V4.csv.gz filter=lfs diff=lfs merge=lfs -text
**/mappings/*.xlsx filter=lfs diff=lfs merge=lfs -text
```

### 3. Track Large Files
```bash
# Track each large file explicitly
git lfs track "code/mappings/gp-reg-pat-prac-lsoa-all_*.csv"
git lfs track "code/mappings/census2021_lsoa_level.xlsx"

# Or track by pattern
git lfs track "*.csv" 
git lfs track "*.xlsx"
```

### 4. Add and Commit Files
```bash
# Add .gitattributes first
git add .gitattributes

# Add large files (now tracked by LFS)
git add code/mappings/gp-reg-pat-prac-lsoa-all_*.csv
git add code/mappings/census2021_lsoa_level.xlsx
git add code/mappings/LSOA_DEC_2021.csv

# Commit
git commit -m "Add large mapping files using Git LFS"
```

### 5. Verify LFS Tracking
```bash
# Check which files are in LFS
git lfs ls-files

# Should show something like:
# abc123def * code/mappings/gp-reg-pat-prac-lsoa-all_2020.csv
# def456ghi * code/mappings/census2021_lsoa_level.xlsx
```

### 6. Push to GitHub
```bash
git push origin branch-name
```

## 📁 File Size Analysis

| File | Size | Status | Action |
|------|------|--------|--------|
| `gp-reg-pat-prac-lsoa-all_2020.csv` | 59MB | ⚠️ >50MB | LFS |
| `gp-reg-pat-prac-lsoa-all_2021.csv` | 60MB | ⚠️ >50MB | LFS |
| `gp-reg-pat-prac-lsoa-all_2022.csv` | 62MB | ⚠️ >50MB | LFS |
| `gp-reg-pat-prac-lsoa-all_2023.csv` | 62MB | ⚠️ >50MB | LFS |
| `gp-reg-pat-prac-lsoa-all_2024.csv` | 63MB | ⚠️ >50MB | LFS |
| `gp-reg-pat-prac-lsoa-all_2025.csv` | 86MB | ⚠️ >50MB | LFS |
| `census2021_lsoa_level.xlsx` | 109MB | ❌ >100MB | LFS |
| `LSOA_DEC_2021.csv` | 1.2MB | ✅ Normal | Regular Git |
| `GP_LSOA_weights_2013.csv` | 35MB | ✅ Normal | Regular Git |

## 🔧 Alternative Solutions

### Option 1: Compress Files
```bash
# Compress large CSV files
gzip code/mappings/gp-reg-pat-prac-lsoa-all_*.csv

# This would reduce sizes significantly but changes file access
```

### Option 2: External Storage
- Store large files in cloud storage (S3, Google Drive, etc.)
- Include download scripts in repository
- Update code to handle missing files gracefully

### Option 3: File Splitting
```bash
# Split large files into smaller chunks
split -l 100000 large_file.csv large_file_part_

# Combine when needed:
cat large_file_part_* > large_file.csv
```

## 🚨 Important Notes

1. **LFS Storage Limits**: GitHub LFS has bandwidth and storage limits
   - Free: 1GB storage, 1GB bandwidth/month
   - Paid plans available for more

2. **Clone Behavior**: `git clone` downloads LFS files automatically
   - Use `git lfs clone` for faster LFS-aware cloning
   - Use `--depth 1` for shallow clones to save bandwidth

3. **Code Integration**: Ensure code handles missing files gracefully:
   ```python
   def load_gp_registry_csv(mappings_dir, year=None):
       csv_file = os.path.join(mappings_dir, f'gp-reg-pat-prac-lsoa-all_{year}.csv')
       if not os.path.exists(csv_file):
           print(f"Warning: {csv_file} not found. Using fallback data.")
           return load_fallback_data(mappings_dir, year)
       return pd.read_csv(csv_file)
   ```

## ✅ Recommended Approach

1. **Use Git LFS** for files >50MB
2. **Keep essential small files** in regular Git
3. **Implement fallback logic** in code for missing LFS files
4. **Document LFS requirements** for new developers

This ensures the repository works both with and without LFS files while maintaining statistical accuracy when all data is available.