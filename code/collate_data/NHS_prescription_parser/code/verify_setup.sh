#!/bin/bash
# Verify NHS Prescription Parser setup

echo "🔍 NHS Prescription Parser Setup Verification"
echo "============================================="

# Activate environment
source ../venv/bin/activate

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
dirs=("." "prescriptionfiles" "../data_prep" "mappings")
dir_names=("code" "code/prescriptionfiles" "data_prep" "code/mappings")
for i in "${!dirs[@]}"; do
    dir="${dirs[$i]}"
    display_name="${dir_names[$i]}"
    if [ -d "$dir" ]; then
        echo "  ✅ $display_name"
    else
        echo "  ❌ $display_name (missing)"
    fi
done

# Check core files
echo ""
echo "📄 Checking core files..."
files=(
    "drug_prevalence.py"
    "condition_prevalence.py" 
    "custom_list_prevalence.py"
    "mappings/GPs.json"
    "mappings/drug_association_graph.gexf"
)

file_names=(
    "code/drug_prevalence.py"
    "code/condition_prevalence.py" 
    "code/custom_list_prevalence.py"
    "code/mappings/GPs.json"
    "code/mappings/drug_association_graph.gexf"
)

for i in "${!files[@]}"; do
    file="${files[$i]}"
    display_name="${file_names[$i]}"
    if [ -f "$file" ]; then
        echo "  ✅ $display_name"
    else
        echo "  ❌ $display_name (missing)"
    fi
done

# Test import
echo ""
echo "🧪 Testing core functionality..."
# We're already in the code directory
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
