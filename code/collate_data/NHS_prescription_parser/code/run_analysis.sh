#!/bin/bash
# NHS Prescription Parser - Easy Analysis Runner

set -e

# Activate environment
source ../venv/bin/activate

# Function to show help
show_help() {
    echo "NHS Prescription Parser - Analysis Runner"
    echo "========================================"
    echo ""
    echo "USAGE: $0 <analysis_type> <target> <year> [options]"
    echo ""
    echo "ANALYSIS TYPES:"
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
    echo "DATE FORMATS (colon-separated ranges supported):"
    echo "  2021        Analyze full year (Jan-Dec 2021)"
    echo "  2021-01     Single month (Jan 2021)"
    echo "  2021-01:06  Date range (Jan-Jun 2021)"
    echo "  2019-09:2021-01  Cross-year range"
    echo "  2018:2024   Multi-year (all months)"
    echo "  201801:202409   Exact months"
    echo ""
    echo "Options:"
    echo "  --output DIR    Output directory (default: ../data_prep/)"
    echo "  --parallel N    Parallel processing (N cores)"
    echo "  --serial        Serial processing (1 core)"
    echo "  --info          Show system information"
    echo "  --help         Show this help"
    echo ""
    echo "Direct script usage (more options):"
    echo "  python drug_prevalence.py --help"
    echo "  python condition_prevalence.py --help"
    echo "  python custom_list_prevalence.py --help"
}

# Check for flags first
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
elif [ "$1" = "--info" ]; then
    echo "🏥 NHS Prescription Parser - System Information"
    echo "==============================================="
    echo "Version: Latest"
    echo "Python: $(python --version 2>&1)"
    echo "Environment: $(pwd)/../venv"
    echo "Data directory: $(pwd)/../data_prep"
    echo "Code directory: $(pwd)"
    echo "CPU Cores: $(python -c "import os; print(os.cpu_count())")"
    echo "RAM: $(python -c "import psutil; print(f'{psutil.virtual_memory().total // (1024**3)} GB')" 2>/dev/null || echo "N/A")"
    echo ""
    echo "Available analysis types: drug, condition, custom"
    echo "Processing modes: parallel (default), serial"
    exit 0
fi

# Check arguments
if [ $# -lt 3 ]; then
    echo "❌ Insufficient arguments provided"
    echo ""
    show_help
    exit 0
fi

ANALYSIS_TYPE=$1
TARGET=$2

# Check if 4th argument is a date (space-separated format support)
if [ $# -ge 4 ] && [[ "$4" =~ ^[0-9]{4}(-[0-9]{2})?$ ]]; then
    # Space-separated format: script condition asthma 2020-01 2021-01
    START_DATE_ARG=$3
    END_DATE_ARG=$4
    YEAR="$START_DATE_ARG:$END_DATE_ARG"
    shift 4
    echo "⚠️  Space-separated dates are deprecated. Use: $ANALYSIS_TYPE $TARGET $YEAR"
    echo "❌ Unknown option: $4"
    exit 1
else
    # Standard format: script condition asthma 2020-01:2021-01
    YEAR=$3
    shift 3
fi

# Parse year format with comprehensive regex patterns
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
elif [[ $YEAR =~ ^([0-9]{4})-([0-9]{2}):([0-9]{4})-([0-9]{2})$ ]]; then
    # Cross-year range: 2020-01:2021-01 -> 202001 to 202101
    START_DATE="${BASH_REMATCH[1]}${BASH_REMATCH[2]}"
    END_DATE="${BASH_REMATCH[3]}${BASH_REMATCH[4]}"
elif [[ $YEAR =~ ^([0-9]{4}):([0-9]{4})$ ]]; then
    # Multi-year: 2018:2024 -> 201801 to 202412
    START_DATE="${BASH_REMATCH[1]}01"
    END_DATE="${BASH_REMATCH[2]}12"
elif [[ $YEAR =~ ^([0-9]{6}):([0-9]{6})$ ]]; then
    # Exact months: 201801:202409 -> 201801 to 202409
    START_DATE="${BASH_REMATCH[1]}"
    END_DATE="${BASH_REMATCH[2]}"
else
    echo "❌ Invalid date format: $YEAR"
    echo ""
    echo "Valid formats (colon-separated only):"
    echo "  YYYY          - Full year (e.g., 2021)"
    echo "  YYYY-MM       - Single month (e.g., 2021-01)"
    echo "  YYYY-MM:MM    - Month range same year (e.g., 2021-01:06)"
    echo "  YYYY-MM:YYYY-MM - Cross-year range (e.g., 2019-09:2021-01)"
    echo "  YYYY:YYYY     - Multi-year (e.g., 2018:2024)"
    echo "  YYYYMM:YYYYMM - Exact months (e.g., 201801:202409)"
    exit 1
fi

# Parse processing options
PROCESSING_MODE=""
PARALLEL_CORES=""
DRY_RUN=false
REMAINING_ARGS=()

for arg in "$@"; do
    case $arg in
        --parallel)
            PROCESSING_MODE="parallel"
            ;;
        --parallel=*)
            PROCESSING_MODE="parallel"
            PARALLEL_CORES="${arg#*=}"
            ;;
        --cores)
            PROCESSING_MODE="parallel"
            ;;
        --cores=*)
            PROCESSING_MODE="parallel"
            PARALLEL_CORES="${arg#*=}"
            ;;
        --serial)
            PROCESSING_MODE="serial"
            ;;
        --dry-run)
            DRY_RUN=true
            ;;
        *)
            REMAINING_ARGS+=("$arg")
            ;;
    esac
done

# Set remaining args
set -- "${REMAINING_ARGS[@]}"

echo "🏥 NHS Prescription Parser Analysis"
echo "==================================="
echo "Type: $ANALYSIS_TYPE"
echo "Target: $TARGET"
echo "Period: $START_DATE to $END_DATE"

if [ "$PROCESSING_MODE" = "serial" ]; then
    echo "Processing: Serial (1 core)"
elif [ "$PROCESSING_MODE" = "parallel" ]; then
    if [ -n "$PARALLEL_CORES" ]; then
        echo "Processing: Parallel ($PARALLEL_CORES cores)"
    else
        echo "Processing: Parallel (4 cores)"
    fi
fi

echo ""

# If dry run, just show what would be executed
if [ "$DRY_RUN" = true ]; then
    echo "🧪 Dry run mode - showing command that would be executed:"
    case $ANALYSIS_TYPE in
        "drug")
            echo "Command: python drug_prevalence.py -d \"$TARGET\" -s $START_DATE -e $END_DATE $*"
            ;;
        "condition")
            echo "Command: python condition_prevalence.py -c \"$TARGET\" -s $START_DATE -e $END_DATE $*"
            ;;
        "custom")
            echo "Command: python custom_list_prevalence.py -l \"$TARGET\" -s $START_DATE -e $END_DATE $*"
            ;;
        *)
            echo "❌ Unknown analysis type: $ANALYSIS_TYPE"
            echo "Use: drug, condition, or custom"
            exit 1
            ;;
    esac
    echo "✅ Dry run complete!"
    exit 0
fi

# Validate analysis type and run appropriate analysis
case $ANALYSIS_TYPE in
    "drug")
        echo "🔍 Running drug prevalence analysis..."
        python drug_prevalence.py -d "$TARGET" -s $START_DATE -e $END_DATE "$@"
        ;;
    "condition")
        echo "🔍 Running condition prevalence analysis..."
        python condition_prevalence.py -c "$TARGET" -s $START_DATE -e $END_DATE "$@"
        ;;
    "custom")
        echo "🔍 Running custom list prevalence analysis..."
        if [ ! -f "$TARGET" ]; then
            echo "❌ Custom list file not found: $TARGET"
            exit 1
        fi
        python custom_list_prevalence.py -l "$TARGET" -s $START_DATE -e $END_DATE "$@"
        ;;
    *)
        echo "❌ Unknown analysis type: $ANALYSIS_TYPE"
        echo "Use: drug, condition, or custom"
        exit 1
        ;;
esac

echo ""
echo "✅ Analysis complete! Check ../data_prep/ for output files."