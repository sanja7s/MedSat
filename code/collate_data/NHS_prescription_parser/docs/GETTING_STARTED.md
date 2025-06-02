# Getting Started with NHS Prescription Parser

## 🚀 One-Command Setup

```bash
git clone <repository-url>
cd NHS_prescription_parser
./bootstrap.sh
```

The bootstrap script will:
- ✅ Set up Python environment and dependencies
- ✅ Check for missing essential files
- ✅ Offer to download or generate sample data
- ✅ Create all utility scripts
- ✅ Guide you through Git LFS setup if needed

## 📥 File Download Options (During Bootstrap)

When essential files are missing, you'll see:
```
⚠️  Missing 2 essential files:
   - gp-reg-pat-prac-lsoa-all_2021.csv (~63MB) - GP Registry 2021

📥 Options:
   1. Try downloading essential files automatically
   2. Generate sample data (reduced accuracy)  
   3. Continue without (basic functionality)
   4. Exit and install Git LFS first

Choose option (1-4):
```

**Recommended**: Choose option 1 for best accuracy, or option 2 for quick testing.

## 🚀 Ready to Use

After bootstrap completes:

```bash
# Activate environment (if not auto-activated)
source activate_env.sh

# Verify everything works
./verify_setup.sh

# Start analyzing
./run_analysis.sh drug metformin 2021
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
