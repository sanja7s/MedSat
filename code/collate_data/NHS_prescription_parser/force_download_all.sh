#!/bin/bash
# Force Download ALL LFS Files - Foolproof Method
# This script tries every possible method to download LFS files

set -e

echo "🚀 Force Download All LFS Files"
echo "==============================="
echo "This script will download all 47 LFS files (196MB) using every available method."
echo ""

# Check Git LFS
if ! command -v git-lfs &> /dev/null; then
    echo "❌ Git LFS not found. Install it first:"
    echo "   macOS: brew install git-lfs"
    echo "   Ubuntu: sudo apt-get install git-lfs"
    exit 1
fi

echo "✅ Git LFS found: $(git lfs version)"

# Initialize
git lfs install
echo "✅ Git LFS initialized"

# Method 1: Standard approach
echo ""
echo "📥 Method 1: Standard LFS download..."
git lfs fetch --all 2>/dev/null || echo "Fetch failed, continuing..."
git lfs pull 2>/dev/null || echo "Pull failed, continuing..."

# Method 2: Checkout approach
echo ""
echo "📥 Method 2: LFS checkout..."
git lfs checkout 2>/dev/null || echo "Checkout failed, continuing..."

# Method 3: Specific patterns
echo ""
echo "📥 Method 3: Download specific patterns..."
git lfs pull --include="*.json" 2>/dev/null || echo "JSON pull failed, continuing..."
git lfs pull --include="*.csv" 2>/dev/null || echo "CSV pull failed, continuing..."
git lfs pull --include="*.pkl" 2>/dev/null || echo "PKL pull failed, continuing..."
git lfs pull --include="*.gexf" 2>/dev/null || echo "GEXF pull failed, continuing..."

# Method 4: Mapping directory specific
echo ""
echo "📥 Method 4: Download mapping files specifically..."
git lfs pull --include="code/mappings/*" 2>/dev/null || echo "Mappings pull failed, continuing..."

# Method 5: Individual large files
echo ""
echo "📥 Method 5: Download known large files individually..."
LARGE_FILES=(
    "code/mappings/GP_LSOA_weights_2013.csv"
    "code/mappings/GP_LSOA_PATIENTSDIST_2021.json"
    "code/mappings/GP_LSOA_PATIENTSDIST.json"
    "code/mappings/GPs.json"
    "code/mappings/GPs_2013.json"
    "code/mappings/Drugbank_drugs_data.json"
)

for file in "${LARGE_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "Downloading $file..."
        git lfs pull --include="$file" 2>/dev/null || echo "Failed to download $file"
    fi
done

# Method 6: All tracked files
echo ""
echo "📥 Method 6: Download all LFS tracked files..."
git lfs ls-files | while read hash path; do
    if [ -n "$path" ]; then
        echo "Downloading $path..."
        git lfs pull --include="$path" 2>/dev/null || echo "Failed: $path"
    fi
done

# Final verification
echo ""
echo "🔍 Verification:"
echo "=================="

LFS_COUNT=$(git lfs ls-files 2>/dev/null | wc -l | tr -d ' ')
echo "LFS files tracked: $LFS_COUNT"

if [ -d "code/mappings" ]; then
    echo ""
    echo "Mapping files status:"
    TOTAL_MAPPING=0
    DOWNLOADED_MAPPING=0
    POINTER_FILES=()
    
    for file in code/mappings/*; do
        if [ -f "$file" ]; then
            TOTAL_MAPPING=$((TOTAL_MAPPING + 1))
            
            # Check if it's downloaded (actual data) or still a pointer
            FIRST_LINE=$(head -1 "$file" 2>/dev/null || echo "")
            if [[ "$FIRST_LINE" == "version https://git-lfs.github.com/spec/v1" ]]; then
                POINTER_FILES+=("$(basename "$file")")
            else
                DOWNLOADED_MAPPING=$((DOWNLOADED_MAPPING + 1))
            fi
        fi
    done
    
    echo "Total mapping files: $TOTAL_MAPPING"
    echo "Downloaded (actual data): $DOWNLOADED_MAPPING"
    echo "Still pointers: $((TOTAL_MAPPING - DOWNLOADED_MAPPING))"
    
    if [ ${#POINTER_FILES[@]} -gt 0 ]; then
        echo ""
        echo "❌ Files still as LFS pointers:"
        for file in "${POINTER_FILES[@]}"; do
            echo "   - $file"
        done
        echo ""
        echo "🔧 Try these commands manually:"
        for file in "${POINTER_FILES[@]}"; do
            echo "   git lfs pull --include=\"code/mappings/$file\""
        done
    else
        echo "✅ All mapping files successfully downloaded!"
    fi
else
    echo "❌ Mapping directory not found"
fi

# Show some file sizes for verification
echo ""
echo "Sample file sizes:"
for file in code/mappings/GP_LSOA_weights_2013.csv code/mappings/CHEM_MASTER_MAP.csv code/mappings/GPs.json; do
    if [ -f "$file" ]; then
        SIZE=$(ls -lh "$file" | awk '{print $5}')
        echo "  $(basename "$file"): $SIZE"
    fi
done

echo ""
if [ "$DOWNLOADED_MAPPING" -eq "$TOTAL_MAPPING" ] && [ "$LFS_COUNT" -gt 40 ]; then
    echo "🎉 SUCCESS! All files downloaded successfully."
    echo "   You can now run: ./bootstrap.sh"
else
    echo "⚠️  Some files may still need manual intervention."
    echo "   Check the DOWNLOAD_MISSING_FILES.md guide for more help."
fi

echo ""
echo "💡 Useful next steps:"
echo "   ./verify_setup.sh     # Verify the installation"
echo "   ./bootstrap.sh        # Complete the setup"
echo "   git lfs status        # Check LFS status"