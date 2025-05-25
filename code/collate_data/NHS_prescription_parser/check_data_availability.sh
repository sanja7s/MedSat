#!/bin/bash
# Check Data Availability for NHS Prescription Parser

echo "📊 NHS Prescription Parser - Data Availability Check"
echo "===================================================="

# Check LFS files
echo ""
echo "🗂️ LFS Files Status:"
LFS_COUNT=$(git lfs ls-files 2>/dev/null | wc -l | tr -d ' ')
echo "   LFS files tracked: $LFS_COUNT (expected: 47)"

# Check mapping files
echo ""
echo "📂 Mapping Files Status:"
if [ -d "code/mappings" ]; then
    MAPPING_COUNT=$(find code/mappings -type f \( -name "*.json" -o -name "*.csv" -o -name "*.pkl" -o -name "*.gexf" \) | wc -l | tr -d ' ')
    echo "   Mapping files found: $MAPPING_COUNT (expected: 21)"
    
    # Check if files are LFS pointers or actual data
    POINTER_COUNT=0
    for file in code/mappings/*.{json,csv,pkl,gexf}; do
        if [ -f "$file" ]; then
            FIRST_LINE=$(head -1 "$file" 2>/dev/null || echo "")
            if [[ "$FIRST_LINE" == "version https://git-lfs.github.com/spec/v1" ]]; then
                POINTER_COUNT=$((POINTER_COUNT + 1))
            fi
        fi
    done
    
    if [ "$POINTER_COUNT" -gt 0 ]; then
        echo "   ⚠️  $POINTER_COUNT files are still LFS pointers (not downloaded)"
        echo "   Run: ./force_download_all.sh"
    else
        echo "   ✅ All mapping files downloaded successfully"
    fi
else
    echo "   ❌ Mapping directory not found"
fi

# Check prescription files
echo ""
echo "💊 Prescription Files Status:"
if [ -d "code/prescriptionfiles" ]; then
    PRESCRIPTION_COUNT=$(find code/prescriptionfiles -name "*.gz" | wc -l | tr -d ' ')
    echo "   Prescription files (.gz): $PRESCRIPTION_COUNT"
    
    # Show available date ranges
    DATES=($(find code/prescriptionfiles -name "*.gz" | grep -o '[0-9]\{6\}' | sort))
    if [ ${#DATES[@]} -gt 0 ]; then
        echo "   Date range: ${DATES[0]} to ${DATES[-1]}"
        echo "   Available dates: ${DATES[@]}"
    else
        echo "   ❌ No prescription files found"
    fi
else
    echo "   ❌ Prescription files directory not found"
fi

# Check supported data ranges
echo ""
echo "📅 Supported Data Ranges:"
echo "   Historical (old format): 201401 to 202102"
echo "   Current (new format):    202101 to 202112"
echo "   Latest available:        202112 (December 2021)"

# Check sources configuration
echo ""
echo "🔗 Sources Configuration:"
if [ -f "code/sources/serialized_file_paths.json" ]; then
    SOURCE_COUNT=$(grep -c '"' code/sources/serialized_file_paths.json | head -1)
    echo "   Configured sources: $((SOURCE_COUNT / 2)) URLs"
    
    # Get latest date from sources
    LATEST_SOURCE=$(grep -o '"[0-9]\{6\}' code/sources/serialized_file_paths.json | sed 's/"//g' | sort | tail -1)
    echo "   Latest source date: $LATEST_SOURCE"
else
    echo "   ❌ Sources configuration not found"
fi

# Test examples
echo ""
echo "🧪 Test Examples:"
echo "   # Valid date ranges (2021 data):"
echo "   ./run_analysis.sh drug metformin 2021"
echo "   ./run_analysis.sh drug metformin 2021-01:03"
echo "   ./run_analysis.sh condition diabetes 2021"
echo ""
echo "   # Invalid (2022 not available):"
echo "   ./run_analysis.sh drug metformin 2022  # ❌ Will fail"

# Environment check
echo ""
echo "🔧 Environment Status:"
if [ -f "venv/bin/activate" ]; then
    echo "   ✅ Virtual environment found"
else
    echo "   ⚠️  Virtual environment not found - run ./bootstrap.sh"
fi

if command -v git-lfs &> /dev/null; then
    echo "   ✅ Git LFS installed: $(git lfs version | head -1)"
else
    echo "   ❌ Git LFS not installed"
fi

# Quick verification test
echo ""
echo "🚀 Quick Verification:"
echo "   Run this to test the system:"
echo "   ./run_analysis.sh drug metformin 2021-01:01"
echo ""
echo "   Expected: Should download prescription data for Jan 2021 and calculate metformin prevalence"

echo ""
echo "💡 If issues persist:"
echo "   1. Run: ./force_download_all.sh"
echo "   2. Run: ./verify_setup.sh" 
echo "   3. Check: DOWNLOAD_MISSING_FILES.md"