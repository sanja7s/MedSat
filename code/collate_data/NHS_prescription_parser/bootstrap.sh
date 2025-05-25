#!/bin/bash
# NHS Prescription Parser Bootstrap Script
# Automatically sets up environment and dependencies

set -e  # Exit on any error

echo "🏥 NHS Prescription Parser Bootstrap"
echo "====================================="

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

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found. Please run this script from the NHS_prescription_parser root directory."
    exit 1
fi

print_status "Setting up NHS Prescription Parser environment..."

# Detect Python version
PYTHON_VERSION=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d'.' -f1-2 || echo "")
if [ -z "$PYTHON_VERSION" ]; then
    print_error "Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

print_status "Found Python $PYTHON_VERSION"

# Check if python version is sufficient (3.8+)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    print_error "Python 3.8+ required. Found Python $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment if it doesn't exist
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv $VENV_DIR
    print_success "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install requirements
print_status "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p code/prescriptionfiles
mkdir -p data_prep
mkdir -p data_prep/temp_extract

print_success "Directory structure created"

# Check for Git LFS
print_status "Checking for Git LFS..."
if command -v git-lfs &> /dev/null; then
    print_success "Git LFS found"
    
    # Initialize LFS if needed
    if [ -d ".git" ]; then
        git lfs install
        print_status "Attempting to pull LFS files..."
        git lfs pull || print_warning "Could not pull LFS files (this is okay if files aren't set up yet)"
    fi
else
    print_warning "Git LFS not found. Large mapping files may not be available."
    print_status "Install with: brew install git-lfs (macOS) or apt-get install git-lfs (Ubuntu)"
fi

# Check file availability
print_status "Checking file availability..."
cd code
python3 -c "
import sys
sys.path.append('claude_experiments')
from handle_missing_files import generate_missing_files_report
print()
generate_missing_files_report('../mappings/')
" 2>/dev/null || print_warning "Could not run file availability check"

cd ..

# Create activation script
print_status "Creating activation script..."
cat > activate_env.sh << 'EOF'
#!/bin/bash
# Activate NHS Prescription Parser environment
echo "🏥 Activating NHS Prescription Parser environment..."
source venv/bin/activate
echo "✅ Environment activated! Use 'deactivate' to exit."
echo ""
echo "Quick start commands:"
echo "  ./run_analysis.sh --help              # Show available analysis options"
echo "  ./run_analysis.sh drug metformin 2019 # Analyze metformin for 2019"
echo "  cd code && python drug_prevalence.py --help  # Direct script usage"
EOF

chmod +x activate_env.sh

# Create easy-to-use analysis runner
print_status "Creating analysis runner script..."
cat > run_analysis.sh << 'EOF'
#!/bin/bash
# NHS Prescription Parser - Easy Analysis Runner

set -e

# Activate environment
source venv/bin/activate

# Change to code directory
cd code

# Function to show help
show_help() {
    echo "NHS Prescription Parser - Analysis Runner"
    echo "========================================"
    echo ""
    echo "Usage: $0 <analysis_type> <target> <year> [options]"
    echo ""
    echo "Analysis Types:"
    echo "  drug        Analyze specific drug prevalence"
    echo "  condition   Analyze condition-based prevalence"
    echo "  custom      Use custom drug list from JSON file"
    echo ""
    echo "Examples:"
    echo "  $0 drug metformin 2021"
    echo "  $0 drug \"metformin ibuprofen\" 2021"
    echo "  $0 condition depression 2021"
    echo "  $0 custom sample_list_antidepressants.json 2021"
    echo ""
    echo "Year formats:"
    echo "  2021        Analyze full year (Jan-Dec 2021)"
    echo "  2021-01     Single month (Jan 2021)"
    echo "  2021-01:06  Date range (Jan-Jun 2021)"
    echo ""
    echo "Options:"
    echo "  --output DIR    Output directory (default: ../data_prep/)"
    echo "  --help         Show this help"
    echo ""
    echo "Direct script usage (more options):"
    echo "  python drug_prevalence.py --help"
    echo "  python condition_prevalence.py --help"
    echo "  python custom_list_prevalence.py --help"
}

# Check arguments
if [ $# -lt 3 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

ANALYSIS_TYPE=$1
TARGET=$2
YEAR=$3
shift 3

# Parse year format
if [[ $YEAR =~ ^([0-9]{4})$ ]]; then
    # Full year: 2021 -> 202101 to 202112
    START_DATE="${YEAR}01"
    END_DATE="${YEAR}12"
elif [[ $YEAR =~ ^([0-9]{4})-([0-9]{2})$ ]]; then
    # Single month: 2021-01 -> 202101 to 202101
    START_DATE="${BASH_REMATCH[1]}${BASH_REMATCH[2]}"
    END_DATE="${BASH_REMATCH[1]}${BASH_REMATCH[2]}"
elif [[ $YEAR =~ ^([0-9]{4})-([0-9]{2}):([0-9]{2})$ ]]; then
    # Date range: 2021-01:06 -> 202101 to 202106
    START_DATE="${BASH_REMATCH[1]}${BASH_REMATCH[2]}"
    END_DATE="${BASH_REMATCH[1]}${BASH_REMATCH[3]}"
else
    echo "❌ Invalid year format: $YEAR"
    echo "Use: YYYY, YYYY-MM, or YYYY-MM:MM"
    exit 1
fi

echo "🏥 NHS Prescription Parser Analysis"
echo "==================================="
echo "Type: $ANALYSIS_TYPE"
echo "Target: $TARGET"
echo "Period: $START_DATE to $END_DATE"
echo ""

# Run appropriate analysis
case $ANALYSIS_TYPE in
    "drug")
        echo "🔍 Running drug prevalence analysis..."
        python drug_prevalence.py -d $TARGET -s $START_DATE -e $END_DATE "$@"
        ;;
    "condition")
        echo "🔍 Running condition prevalence analysis..."
        python condition_prevalence.py -c $TARGET -s $START_DATE -e $END_DATE "$@"
        ;;
    "custom")
        echo "🔍 Running custom list prevalence analysis..."
        if [ ! -f "$TARGET" ]; then
            echo "❌ Custom list file not found: $TARGET"
            exit 1
        fi
        python custom_list_prevalence.py -l $TARGET -s $START_DATE -e $END_DATE "$@"
        ;;
    *)
        echo "❌ Unknown analysis type: $ANALYSIS_TYPE"
        echo "Use: drug, condition, or custom"
        exit 1
        ;;
esac

echo ""
echo "✅ Analysis complete! Check ../data_prep/ for output files."
EOF

chmod +x run_analysis.sh

# Create quick setup verification script
print_status "Creating verification script..."
cat > verify_setup.sh << 'EOF'
#!/bin/bash
# Verify NHS Prescription Parser setup

echo "🔍 NHS Prescription Parser Setup Verification"
echo "============================================="

# Activate environment
source venv/bin/activate

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
EOF

chmod +x verify_setup.sh

print_success "Bootstrap complete!"

echo ""
echo "🎉 NHS Prescription Parser is ready to use!"
echo ""
echo "📋 Next steps:"
echo "   1. Activate environment:    source activate_env.sh"
echo "   2. Verify setup:           ./verify_setup.sh"
echo "   3. Run analysis:           ./run_analysis.sh --help"
echo ""
echo "📖 Quick examples:"
echo "   ./run_analysis.sh drug metformin 2021"
echo "   ./run_analysis.sh condition depression 2021"
echo "   ./run_analysis.sh custom code/sample_list_antidepressants.json 2021"
echo ""
echo "📁 Output will be in: data_prep/"

# Create a simple getting started guide
cat > GETTING_STARTED.md << 'EOF'
# Getting Started with NHS Prescription Parser

## 🚀 Quick Setup

1. **Clone and bootstrap:**
   ```bash
   git clone <repository-url>
   cd NHS_prescription_parser
   ./bootstrap.sh
   ```

2. **Activate environment:**
   ```bash
   source activate_env.sh
   ```

3. **Verify setup:**
   ```bash
   ./verify_setup.sh
   ```

## 📊 Running Analysis

### Easy Mode (Recommended)
```bash
# Analyze a drug for full year
./run_analysis.sh drug metformin 2021

# Analyze multiple drugs
./run_analysis.sh drug "metformin insulin" 2021

# Analyze a condition
./run_analysis.sh condition depression 2021

# Use custom drug list
./run_analysis.sh custom code/sample_list_antidepressants.json 2021

# Analyze specific months
./run_analysis.sh drug metformin 2021-01:06  # Jan-Jun 2021
```

### Direct Script Usage (More Options)
```bash
cd code

# Drug prevalence
python drug_prevalence.py -d metformin -s 202101 -e 202112

# Condition prevalence  
python condition_prevalence.py -c depression -s 202101 -e 202112

# Custom list prevalence
python custom_list_prevalence.py -l sample_list_antidepressants.json -s 202101 -e 202112
```

## 📁 Output

Results are saved to `data_prep/` with files like:
- `metformin_V4.csv.gz` - Monthly prescription data
- Extract yearly prevalence using the Jupyter notebook

## 🔧 Advanced Usage

See individual script help:
```bash
python drug_prevalence.py --help
python condition_prevalence.py --help
python custom_list_prevalence.py --help
```

## 📚 Additional Resources

- **Statistical Analysis**: `code/claude_experiments/` - Advanced analysis tools
- **Missing Files**: Run `python code/claude_experiments/handle_missing_files.py`
- **Documentation**: Check `*.md` files for detailed guides
EOF

print_success "Setup guide created: GETTING_STARTED.md"