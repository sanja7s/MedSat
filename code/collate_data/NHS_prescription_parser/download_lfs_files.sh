#!/bin/bash
# Dedicated LFS File Downloader for NHS Prescription Parser
# Ensures all 47 LFS files (196MB) are properly downloaded

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🗂️ NHS Prescription Parser - LFS File Downloader"
echo "=================================================="

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    print_error "Not in a git repository. Please run from the NHS_prescription_parser root directory."
    exit 1
fi

# Check for Git LFS
if ! command -v git-lfs &> /dev/null; then
    print_error "Git LFS not found. Please install it first:"
    echo ""
    echo "macOS:   brew install git-lfs"
    echo "Ubuntu:  sudo apt-get install git-lfs"
    echo "CentOS:  sudo yum install git-lfs"
    echo ""
    echo "After installation: git lfs install"
    exit 1
fi

print_success "Git LFS found"

# Initialize LFS
print_status "Initializing Git LFS..."
git lfs install

# Show LFS info
print_status "Checking LFS tracking..."
LFS_TRACKED=$(git lfs track | grep -c "Listing tracked patterns" || echo "0")
if [ "$LFS_TRACKED" -eq 0 ]; then
    print_warning "No LFS tracking patterns found"
else
    git lfs track | head -10
fi

# Download all LFS files with multiple approaches
print_status "Downloading all LFS files (47 files, ~196MB)..."
echo "This may take several minutes depending on your connection..."

# Approach 1: Fetch all LFS objects
print_status "Step 1/4: Fetching all LFS objects..."
git lfs fetch --all

# Approach 2: Pull LFS files
print_status "Step 2/4: Pulling LFS files..."
git lfs pull

# Approach 3: Checkout LFS files
print_status "Step 3/4: Checking out LFS files..."
git lfs checkout

# Approach 4: Pull specific patterns if needed
print_status "Step 4/4: Ensuring mapping files are downloaded..."
git lfs pull --include="code/mappings/*" || true
git lfs pull --include="*.json,*.csv,*.pkl,*.gexf" || true

# Verify download
print_status "Verifying LFS file download..."

# Count LFS files
LFS_COUNT=$(git lfs ls-files 2>/dev/null | wc -l | tr -d ' ')
print_status "Found $LFS_COUNT LFS-tracked files"

if [ "$LFS_COUNT" -lt 40 ]; then
    print_warning "Expected ~47 LFS files, only found $LFS_COUNT"
else
    print_success "LFS file count looks good ($LFS_COUNT files)"
fi

# Check mapping files specifically
print_status "Checking mapping files..."
MAPPING_COUNT=0
POINTER_COUNT=0

if [ -d "code/mappings" ]; then
    for file in code/mappings/*.{json,csv,pkl,gexf}; do
        if [ -f "$file" ]; then
            MAPPING_COUNT=$((MAPPING_COUNT + 1))
            
            # Check if it's an LFS pointer or actual data
            FIRST_LINE=$(head -1 "$file" 2>/dev/null || echo "")
            if [[ "$FIRST_LINE" == "version https://git-lfs.github.com/spec/v1" ]]; then
                POINTER_COUNT=$((POINTER_COUNT + 1))
                print_warning "$(basename "$file") is still an LFS pointer"
            fi
        fi
    done
    
    print_status "Mapping files found: $MAPPING_COUNT"
    
    if [ "$POINTER_COUNT" -gt 0 ]; then
        print_warning "$POINTER_COUNT files are still LFS pointers (not downloaded)"
        print_status "Attempting to force download these files..."
        
        # Try to download the pointer files specifically
        for file in code/mappings/*.{json,csv,pkl,gexf}; do
            if [ -f "$file" ]; then
                FIRST_LINE=$(head -1 "$file" 2>/dev/null || echo "")
                if [[ "$FIRST_LINE" == "version https://git-lfs.github.com/spec/v1" ]]; then
                    print_status "Downloading $(basename "$file")..."
                    git lfs pull --include="$file" || true
                fi
            fi
        done
    else
        print_success "All mapping files successfully downloaded!"
    fi
else
    print_error "Mapping directory not found: code/mappings"
fi

# Final verification
echo ""
echo "📊 Final Status:"
echo "=================="

# LFS status
git lfs status | head -5

# File sizes
echo ""
echo "Sample file sizes:"
for file in code/mappings/GP_LSOA_weights_2013.csv code/mappings/GP_LSOA_PATIENTSDIST_2021.json code/mappings/CHEM_MASTER_MAP.csv; do
    if [ -f "$file" ]; then
        SIZE=$(ls -lh "$file" | awk '{print $5}')
        echo "  $(basename "$file"): $SIZE"
    fi
done

echo ""
if [ "$POINTER_COUNT" -eq 0 ] && [ "$LFS_COUNT" -gt 40 ]; then
    print_success "✅ All LFS files successfully downloaded!"
    print_status "You can now run: ./bootstrap.sh or ./run_analysis.sh"
else
    print_warning "⚠️  Some issues detected. You may need to:"
    echo "1. Check your Git LFS installation: git lfs version"
    echo "2. Verify network access to GitHub LFS"
    echo "3. Try running this script again"
    echo "4. Contact repository maintainer if issues persist"
fi

echo ""
echo "💡 Useful commands:"
echo "   git lfs ls-files                    # List all LFS files"
echo "   git lfs status                      # Check LFS status"
echo "   git lfs pull                        # Download LFS files"
echo "   ./bootstrap.sh                      # Run full setup"