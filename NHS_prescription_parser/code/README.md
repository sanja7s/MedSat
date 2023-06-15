
# Submodule to compute drug prevalences. 
This module contains code to compute LSOA level prevalences given 
1. A list of drug names 
2. A list of drugnames with their respective BNF codes. 
3. A list of conditions/symptoms, provided we can find associated drugs from drugbank 
4. Opioid OME prevalence 

## Installing. 
Simply create a conda environment ```conda env create -f environment.yml```
Activate the environment 

## Prevalence based on drug names 
This will generate prevalence values for a list of drug names. The script will try to find BNF codes for variants of the said drug names and then compute LSOA level prevalences. 
- Cd into the code directory
- run the script as such ```python drug_prevalence.py -d metformin -s <Start_YYYYMM> -e <End_YYYYMM>```

## PRevalence based on list of Drug names 
WIP

## Prevalence for conditions/symptoms
WIP 

## Opioids prevalence
WIP