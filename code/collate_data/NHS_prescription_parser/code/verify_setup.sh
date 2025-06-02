#!/bin/bash
# Verify NHS Prescription Parser setup

echo "🔍 NHS Prescription Parser Setup Verification"
echo "============================================="

# Activate environment
source ./venv/bin/activate

echo "✅ Virtual environment activated"

# Check Python packages
echo ""
echo "📦 Checking Python packages..."
python3 -c "
import sys
packages = ['pandas', 'numpy', 'tqdm', 'networkx', 'requests', 'matplotlib', 'scipy']
missing = []
for pkg in packages:
    try:
        __import__(pkg)
        print(f'  ✅ {pkg}')
    except ImportError:
        print(f'  ❌ {pkg} (missing)')
        missing.append(pkg)

if missing:
    print(f'\n❌ Missing packages: {missing}')
    sys.exit(1)
else:
    print('\n✅ All packages available')
"

# Check directory structure
echo ""
echo "📁 Checking directory structure..."
dirs=("code" "code/prescriptionfiles" "data_prep" "code/mappings")
for dir in "${dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir"
    else
        echo "  ❌ $dir (missing)"
    fi
done

# Check core files
echo ""
echo "📄 Checking core files..."
files=(
    "code/drug_prevalence.py"
    "code/condition_prevalence.py" 
    "code/custom_list_prevalence.py"
    "code/mappings/GPs.json"
    "code/mappings/drug_association_graph.gexf"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (missing)"
    fi
done

# Test import
echo ""
echo "🧪 Testing core functionality..."
cd code
python3 -c "
import sys
sys.path.append('.')
try:
    from sources.downloader import Downloader
    from matching.drugMatching import DrugMatcher
    print('  ✅ Core modules import successfully')
except Exception as e:
    print(f'  ❌ Import error: {e}')
    sys.exit(1)
"

echo ""
echo "✅ Setup verification complete!"
echo "   Ready to run: ./run_analysis.sh --help"
