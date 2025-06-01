#!/bin/bash
# NHS Prescription Parser - Easy Analysis Runner

set -e

# Activate environment
source ../venv/bin/activate

# We're already in code directory, no need to cd

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
    echo "  2018:2024   Multi-year range (2018-2024, all months)"
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
elif [[ $YEAR =~ ^([0-9]{4}):([0-9]{4})$ ]]; then
    # Multi-year range: 2018:2024 -> 201801 to 202412
    START_DATE="${BASH_REMATCH[1]}01"
    END_DATE="${BASH_REMATCH[2]}12"
else
    echo "❌ Invalid year format: $YEAR"
    echo "Use: YYYY, YYYY-MM, YYYY-MM:MM, or YYYY:YYYY"
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
