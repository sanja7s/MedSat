## serialize.py
This script helps to serialize the raw NHS files, by adding some extra inferred columns that make processing easier. IF you do not want to run this fron scratch, please download 
the serialized files from here : https://tinyurl.com/serialisedpNHSprescr

## compute_condition_category_prevalence.py
This script allows to compute spatio-temporal prescription prevalence at the LSOA level. You need to supply a set of conditions (e.g., asthma, diabetes, hypertension), or a set of drug categories (e.g., antidepressant, antihistemine). If the supplied conditions/categories are matched with a set of drugs, the script would compute prevalence at the granularity of a Census LSOA across England. The output file contains the following columns:
1. YYYYMM : Month and year of the processed prescriptions dump.
2. LSOA_CODE : Lower super output area code based on 2011 census.
3. Total_quantity: Total number of pills (if fluid, milliliters) prescribed. 
4. Dosage_ratio: Total units of dosage ratios prescribed for all the drugs associated with the selected condition. The ratio for a prescribed drug is computed by normalizing the prescribed dosage (potency x quantity) by the minimum possible prescribed dosage for the same drug in the same month.
5. Total_cost: Total cost of all the prescriptions in this area, in GBP
6. Total_items : Total number of prescriptions. 
7. Patient_count: Total number of registered NHS patients in the LSOA

## compute_drug_prevalence.py
This file does the same thing as compute_condition_category_prevalence.py, but instead of a set of conditions/categories you can supply a set of drug names. This comes in handy of you want to calculate the trends in individual drugs e.g., Fentanyl across time. The script will produce file corresponding to each supplied drug, and the format would be identical to that from compute_condition_category_prevalence.py

## compute_ome.py
This is a special case of compute_condition_category_prevalence.py, which category = opioids. The Dosage_ratio would be replaced with oral morphine equivalence in the generated output

## total_presc_LSOA.py
This file will just compute the LSOA level prescription volume across time. 
