#!/bin/bash
# NHS Prescription Parser - Easy Analysis Runner

set -e

# Activate environment
source ../venv/bin/activate

# We're already in code directory, no need to cd

# Function to show help
show_help() {
    echo "🏥 NHS Prescription Parser - Analysis Runner"
    echo "============================================="
    echo ""
    echo "📋 USAGE: $0 <analysis_type> <target> <date_range> [options]"
    echo ""
    echo "🔍 ANALYSIS TYPES:"
    echo "  drug        Analyze specific drug prevalence by name"
    echo "  condition   Analyze condition-based prevalence (uses DrugBank mapping)"
    echo "  custom      Use custom drug list from JSON file with BNF codes"
    echo ""
    echo "📅 DATE FORMATS (Choose what works best for your research):"
    echo "  2021        Full year analysis (Jan-Dec 2021) - Most common"
    echo "  2021-01     Single month (Jan 2021) - Quick testing"
    echo "  2021-01:06  Month range within year (Jan-Jun 2021) - Seasonal analysis"
    echo "  2018:2024   Multi-year range (2018-2024, all months) - Longitudinal studies"
    echo "  201801:202409  Exact month range (Jan 2018 - Sep 2024) - Precise control"
    echo ""
    echo "✨ COMMON EXAMPLES:"
    echo ""
    echo "  📊 Quick drug analysis (single year):"
    echo "    $0 drug metformin 2021"
    echo ""
    echo "  🔬 Multiple drugs (space-separated, quoted):"
    echo "    $0 drug \"metformin insulin aspirin\" 2021"
    echo ""
    echo "  🏥 Medical condition analysis:"
    echo "    $0 condition depression 2021"
    echo "    $0 condition asthma 2018:2022"
    echo ""
    echo "  📋 Custom drug lists (with BNF codes):"
    echo "    $0 custom sample_list_antidepressants.json 2021"
    echo ""
    echo "  ⏱️ Quick testing (single month):"
    echo "    $0 drug metformin 2021-01"
    echo ""
    echo "  📈 Longitudinal studies (multi-year):"
    echo "    $0 condition diabetes 2018:2024"
    echo ""
    echo "  🎯 Precise date control (exact months):"
    echo "    $0 condition asthma 201801:202409"
    echo ""
    echo "⚙️ OPTIONS:"
    echo "  --output DIR    Custom output directory (default: ../data_prep/)"
    echo "  --help         Show this comprehensive help"
    echo ""
    echo "⏰ PERFORMANCE GUIDE:"
    echo "  Single month:   ~30-60 seconds"
    echo "  Full year:      ~10-20 minutes (12 months)"
    echo "  Multi-year:     ~30-60 minutes (depends on range)"
    echo ""
    echo "📁 OUTPUT:"
    echo "  Results saved to: ../data_prep/<drug/condition>_V4.csv.gz"
    echo "  Format: LSOA-level prevalence data with patient counts"
    echo ""
    echo "🚀 QUICK START:"
    echo "  1. Test with single month:  $0 drug metformin 2021-01"
    echo "  2. Run full analysis:       $0 condition asthma 2021"
    echo "  3. Check results:           ls ../data_prep/"
    echo ""
    echo "🔧 ADVANCED USAGE (Direct Python scripts with more options):"
    echo "  python drug_prevalence.py --help"
    echo "  python condition_prevalence.py --help"
    echo "  python custom_list_prevalence.py --help"
    echo ""
    echo "❓ NEED HELP?"
    echo "  • For 2021+ data with extended features: python run_extended.py --help"
    echo "  • System verification: ./verify_setup.sh"
    echo "  • Test suite: ./run_tests.sh"
    echo ""
    echo "💡 TIP: Start with single month analysis to verify your setup works!"
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

# Parse date format
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
elif [[ $YEAR =~ ^([0-9]{6}):([0-9]{6})$ ]]; then
    # Exact month range: 201801:202409 -> 201801 to 202409
    START_DATE="${BASH_REMATCH[1]}"
    END_DATE="${BASH_REMATCH[2]}"
else
    echo "❌ Invalid date format: '$YEAR'"
    echo ""
    echo "📅 Valid formats:"
    echo "  YYYY        Full year (e.g., 2021)"
    echo "  YYYY-MM     Single month (e.g., 2021-01)"
    echo "  YYYY-MM:MM  Month range (e.g., 2021-01:06)"
    echo "  YYYY:YYYY   Multi-year (e.g., 2018:2024)"
    echo "  YYYYMM:YYYYMM  Exact months (e.g., 201801:202409)"
    echo ""
    echo "💡 Examples:"
    echo "  $0 drug metformin 2021"
    echo "  $0 condition asthma 2021-01"
    echo "  $0 condition depression 2018:2022"
    echo "  $0 condition asthma 201801:202409"
    echo ""
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
            echo "❌ Custom list file not found: '$TARGET'"
            echo ""
            echo "📋 Available sample files:"
            ls -1 sample_list_*.json 2>/dev/null | head -5 || echo "  No sample_list_*.json files found"
            echo ""
            echo "💡 Create your own JSON file with format:"
            echo '  {"drug_name": ["BNF_code1", "BNF_code2"]}'
            echo ""
            echo "📖 Example: sample_list_antidepressants.json"
            exit 1
        fi
        python custom_list_prevalence.py -l $TARGET -s $START_DATE -e $END_DATE "$@"
        ;;
    *)
        echo "❌ Unknown analysis type: '$ANALYSIS_TYPE'"
        echo ""
        echo "🔍 Valid analysis types:"
        echo "  drug        Analyze specific drug prevalence"
        echo "  condition   Analyze medical condition prevalence"
        echo "  custom      Use custom JSON drug list"
        echo ""
        echo "💡 Examples:"
        echo "  $0 drug metformin 2021"
        echo "  $0 condition depression 2021"
        echo "  $0 custom sample_list_antidepressants.json 2021"
        echo ""
        echo "❓ For full help: $0 --help"
        exit 1
        ;;
esac

echo ""
echo "✅ Analysis complete! Check ../data_prep/ for output files."
