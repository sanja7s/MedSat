# Download Missing Files Guide

## 🗂️ **Current Issue: LFS Files Not Downloaded**

Your mapping files are currently **LFS pointers** (small text files) instead of the actual data files. This means Git LFS hasn't downloaded the large files yet.

## 🔍 **Quick Diagnosis**

Check if files are LFS pointers vs actual data:
```bash
# This should show CSV headers, NOT "version https://git-lfs.github.com/spec/v1"
head -3 code/mappings/CHEM_MASTER_MAP.csv

# Check file sizes - should be MB, not just a few KB
ls -lh code/mappings/ | head -5
```

## ✅ **Solution 1: Use Dedicated LFS Downloader (Recommended)**

```bash
# Run the comprehensive LFS downloader
./download_lfs_files.sh
```

This script will:
- Download all 47 LFS files (196MB total)
- Verify each file is actual data, not a pointer
- Provide detailed status and error reporting

## ✅ **Solution 2: Manual LFS Commands**

```bash
# 1. Install Git LFS if not present
# macOS: brew install git-lfs
# Ubuntu: sudo apt-get install git-lfs

# 2. Initialize LFS
git lfs install

# 3. Download all LFS files (multiple approaches)
git lfs fetch --all
git lfs pull
git lfs checkout

# 4. Force download mapping files specifically
git lfs pull --include="code/mappings/*"

# 5. Verify download
git lfs ls-files | wc -l  # Should show 47
```

## ✅ **Solution 3: Enhanced Bootstrap**

```bash
# Re-run bootstrap (now has enhanced LFS downloading)
./bootstrap.sh
```

The bootstrap now includes comprehensive LFS downloading and verification.

## 📊 **Files You Should Have After Download**

### **Large Files (>25MB) - 3 files:**
- `code/mappings/GP_LSOA_weights_2013.csv` (35MB)
- `code/mappings/GP_LSOA_PATIENTSDIST_2021.json` (29MB)
- `code/mappings/GP_LSOA_PATIENTSDIST.json` (26MB)

### **All Mapping Files - 21 files total:**
- Drug association graphs (.gexf files)
- Chemical master maps (.csv files)
- GP registries and patient distributions (.json files)
- Drug and condition mappings (.json files)
- Bipartite graphs (.pkl files)

## 🔧 **Troubleshooting**

### **Files Still Show as LFS Pointers**
```bash
# Force re-download specific problematic files
git lfs pull --include="code/mappings/CHEM_MASTER_MAP.csv"
git lfs pull --include="code/mappings/GP_LSOA_weights_2013.csv"

# Check LFS status
git lfs status
```

### **Git LFS Not Installed**
```bash
# Install based on your system
brew install git-lfs          # macOS
sudo apt-get install git-lfs  # Ubuntu/Debian
sudo yum install git-lfs      # CentOS/RHEL

# Then initialize
git lfs install
```

### **Network/Permission Issues**
```bash
# Check LFS endpoint access
git lfs env

# Clear LFS cache and retry
git lfs prune
git lfs pull
```

### **Complete Fresh Start**
```bash
# If all else fails, clean clone with LFS
git clone https://github.com/sanja7s/MedSat.git MedSat_fresh
cd MedSat_fresh/code/collate_data/NHS_prescription_parser
git checkout sagar/vibecode_patching
git lfs pull
./bootstrap.sh
```

## 🎯 **Verification Commands**

After downloading, verify success:
```bash
# Should show 47
git lfs ls-files | wc -l

# Should show actual CSV data, not LFS pointer
head -3 code/mappings/CHEM_MASTER_MAP.csv

# Should show large file sizes
ls -lh code/mappings/GP_LSOA_weights_2013.csv

# Run system verification
./verify_setup.sh
```

## 📝 **Expected Results**

**Successful download shows:**
```
✅ 47 LFS files tracked
✅ Mapping files show actual data (CSV headers, JSON content)
✅ Large files show correct sizes (35MB, 29MB, etc.)
✅ No "version https://git-lfs.github.com/spec/v1" in mapping files
✅ Bootstrap and analysis commands work without errors
```

## 🆘 **Still Having Issues?**

1. **Check Git LFS version**: `git lfs version` (need 2.0+)
2. **Run the diagnostic script**: `./download_lfs_files.sh` (shows detailed status)
3. **Check system requirements**: Ensure you have ~200MB free space
4. **Try different network**: Some networks block LFS downloads

## 💡 **Why This Happened**

Git LFS files require explicit downloading after cloning. The repository has been configured to use LFS for large mapping files, but the actual download step may have been skipped or failed silently.

---

**🎉 Once resolved, you'll have all mapping files and can run analyses without issues!**