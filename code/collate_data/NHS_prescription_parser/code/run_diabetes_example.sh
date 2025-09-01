#!/bin/bash

# This script demonstrates how to run the diabetes prevalence calculation
# with the new data and extended scripts.

# Set the working directory
cd "$(dirname "$0")"

echo "Working in directory: $(pwd)"

# 1. Process the new data files
echo "Step 1: Processing new data files..."
echo "NOTE: You'll need to run this command manually with the appropriate Python environment:"
echo "python process_new_data.py \\"
echo "  --gp-registry ../data_prep/gp-reg-pat-prac-lsoa-all_2021.csv \\"
echo "  --years 2021 \\"
echo "  --lsoa-mapping ../data_prep/LSOA_DEC_2021.csv \\"
echo "  --epd-file ../data_prep/EPD_202110.ZIP \\"
echo "  --mappings-dir ./mappings \\"
echo "  --prescriptions-dir ./prescriptionfiles"
echo ""

# 2. Run the diabetes prevalence calculation
echo "Step 2: Calculating diabetes prevalence..."
echo "NOTE: You'll need to run this command manually with the appropriate Python environment:"
echo "python run_extended.py condition \\"
echo "  -c diabetes \\"
echo "  -s 202110 \\"
echo "  -e 202110 \\"
echo "  -y 2021"
echo ""

# 3. Post-processing
echo "Step 3: Post-processing..."
echo "After generating the prevalence data, you can use the Jupyter notebooks"
echo "extract_yearly_prevalence.ipynb and outcomes-master.ipynb for post-processing."
echo ""

echo "Example completed. Please ensure you have the correct Python environment activated"
echo "before running the commands above."