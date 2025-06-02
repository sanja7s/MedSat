#!/bin/bash
# Activate NHS Prescription Parser environment
echo "🏥 Activating NHS Prescription Parser environment..."
source ./venv/bin/activate
echo "✅ Environment activated! Use 'deactivate' to exit."
echo ""
echo "Quick start commands:"
echo "  ./run_analysis.sh --help              # Show available analysis options"
echo "  ./run_analysis.sh drug metformin 2019 # Analyze metformin for 2019"
echo "  cd code && python drug_prevalence.py --help  # Direct script usage"
