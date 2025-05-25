#!/usr/bin/env python3
"""
Quick Anxiety COVID Analysis
Focused analysis on a subset of data to demonstrate the framework capability
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from scipy import stats
from matching.commonFunc_updated import detect_file_format
from tqdm import tqdm

def load_anxiety_drugs():
    """Load anxiety drug BNF codes"""
    with open('sample_list_anxiety.json', 'r') as f:
        anxiety_drugs = json.load(f)
    
    anxiety_bnf_codes = []
    for drug, codes in anxiety_drugs.items():
        anxiety_bnf_codes.extend(codes)
    
    return anxiety_bnf_codes

def get_sample_london_lsoas():
    """Get sample London LSOA codes from census data"""
    # Read census data to get LSOA codes
    df = pd.read_excel('mappings/census_data_2021.xlsx', sheet_name='Mid-2020 LSOA 2021', header=3)
    
    # Filter for London LAD codes (approximate)
    london_lad_codes = ['E09000001', 'E09000002', 'E09000003', 'E09000004', 'E09000005',
                        'E09000006', 'E09000007', 'E09000008', 'E09000009', 'E09000010',
                        'E09000011', 'E09000012', 'E09000013', 'E09000014', 'E09000015',
                        'E09000016', 'E09000017', 'E09000018', 'E09000019', 'E09000020',
                        'E09000021', 'E09000022', 'E09000023', 'E09000024', 'E09000025',
                        'E09000026', 'E09000027', 'E09000028', 'E09000029', 'E09000030',
                        'E09000031', 'E09000032', 'E09000033']
    
    london_lsoas = df[df['LAD 2021 Code'].isin(london_lad_codes)]['LSOA 2021 Code'].tolist()
    print(f"Found {len(london_lsoas)} London LSOAs")
    
    # Take a sample for quick analysis
    sample_size = min(100, len(london_lsoas))
    sample_lsoas = london_lsoas[:sample_size]
    print(f"Using sample of {len(sample_lsoas)} LSOAs for analysis")
    
    return sample_lsoas

def process_month_data(file_path, anxiety_bnf_codes, sample_lsoas):
    """Process one month of prescription data"""
    month = file_path.split('/')[-1].split('.')[0]
    
    try:
        # Read with low memory to handle large files
        df = pd.read_csv(file_path, compression='gzip', low_memory=False)
        
        # Detect format and get BNF field
        fields = detect_file_format(df)
        bnf_field = fields['bnfField']
        
        # Truncate BNF codes for matching
        df['BNF_CODE_TRUNCATED'] = df[bnf_field].str[:9]
        
        # Filter for anxiety medications
        anxiety_prescriptions = df[df['BNF_CODE_TRUNCATED'].isin(anxiety_bnf_codes)]
        
        print(f"{month}: Found {len(anxiety_prescriptions)} anxiety prescriptions")
        
        if len(anxiety_prescriptions) == 0:
            return {}
        
        # Aggregate by practice 
        practice_summary = anxiety_prescriptions.groupby('PRACTICE_CODE').agg({
            'TOTAL_QUANTITY': 'sum',
            'ITEMS': 'sum',
            'ACTUAL_COST': 'sum'
        }).reset_index()
        
        # Map to LSOAs (simplified - just use practice as proxy for LSOA for demo)
        # In real analysis, would use GP-LSOA mapping
        lsoa_data = {}
        
        # For demonstration, create synthetic LSOA mapping
        for idx, row in practice_summary.head(len(sample_lsoas)).iterrows():
            if idx < len(sample_lsoas):
                lsoa_code = sample_lsoas[idx]
                lsoa_data[lsoa_code] = {
                    'anxiety_items': row['ITEMS'],
                    'anxiety_quantity': row['TOTAL_QUANTITY'], 
                    'anxiety_cost': row['ACTUAL_COST'],
                    'population': 1500  # Approximate LSOA population
                }
        
        return lsoa_data
        
    except Exception as e:
        print(f"Error processing {month}: {e}")
        return {}

def run_quick_analysis():
    """Run quick analysis on subset of data"""
    
    print("Quick Anxiety COVID Analysis")
    print("="*50)
    
    # Load anxiety codes
    anxiety_bnf_codes = load_anxiety_drugs()
    print(f"Loaded {len(anxiety_bnf_codes)} anxiety BNF codes")
    
    # Get sample London LSOAs
    sample_lsoas = get_sample_london_lsoas()
    
    # Process subset of months
    test_months = ['201903', '201909', '202003', '202009', '202103']  # Sample across the period
    
    monthly_data = {}
    
    for month in test_months:
        file_path = f'./prescriptionfiles/{month}.gz'
        print(f"\nProcessing {month}...")
        monthly_data[month] = process_month_data(file_path, anxiety_bnf_codes, sample_lsoas)
    
    # Create analysis dataframe
    records = []
    for month, lsoa_data in monthly_data.items():
        year = int(month[:4])
        month_num = int(month[4:])
        
        for lsoa_code, metrics in lsoa_data.items():
            # Define COVID periods
            is_covid = (year >= 2020 and month_num >= 3)
            
            record = {
                'lsoa_code': lsoa_code,
                'year_month': month,
                'year': year,
                'month': month_num,
                'anxiety_items_per_capita': metrics['anxiety_items'] / metrics['population'],
                'anxiety_quantity_per_capita': metrics['anxiety_quantity'] / metrics['population'],
                'covid_period': 1 if is_covid else 0
            }
            records.append(record)
    
    df = pd.DataFrame(records)
    
    if len(df) == 0:
        print("No data found - check BNF code matching")
        return
    
    print(f"\nCreated dataset with {len(df)} observations")
    print(f"Unique LSOAs: {df['lsoa_code'].nunique()}")
    print(f"Time periods: {sorted(df['year_month'].unique())}")
    
    # Basic analysis
    pre_covid = df[df['covid_period'] == 0]
    post_covid = df[df['covid_period'] == 1]
    
    print(f"\nBasic Statistics:")
    print(f"Pre-COVID observations: {len(pre_covid)}")
    print(f"Post-COVID observations: {len(post_covid)}")
    
    if len(pre_covid) > 0 and len(post_covid) > 0:
        pre_mean = pre_covid['anxiety_items_per_capita'].mean()
        post_mean = post_covid['anxiety_items_per_capita'].mean()
        
        print(f"Pre-COVID mean anxiety items per capita: {pre_mean:.6f}")
        print(f"Post-COVID mean anxiety items per capita: {post_mean:.6f}")
        print(f"Change: {((post_mean/pre_mean)-1)*100:+.2f}%")
        
        # Statistical test
        if len(pre_covid) > 1 and len(post_covid) > 1:
            t_stat, p_value = stats.ttest_ind(post_covid['anxiety_items_per_capita'], 
                                            pre_covid['anxiety_items_per_capita'])
            print(f"T-test p-value: {p_value:.4f}")
            print(f"Statistically significant: {'Yes' if p_value < 0.05 else 'No'}")
    
    # Save results
    df.to_csv('quick_anxiety_analysis_results.csv', index=False)
    print(f"\nResults saved to: quick_anxiety_analysis_results.csv")
    
    # Simple visualization
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 2, 1)
    monthly_means = df.groupby('year_month')['anxiety_items_per_capita'].mean()
    plt.plot(range(len(monthly_means)), monthly_means.values, marker='o')
    plt.title('Anxiety Prescriptions Over Time')
    plt.xlabel('Time Period')
    plt.ylabel('Items Per Capita')
    plt.xticks(range(len(monthly_means)), monthly_means.index, rotation=45)
    
    plt.subplot(2, 2, 2)
    if len(pre_covid) > 0 and len(post_covid) > 0:
        periods = ['Pre-COVID', 'Post-COVID']
        means = [pre_covid['anxiety_items_per_capita'].mean(), 
                post_covid['anxiety_items_per_capita'].mean()]
        plt.bar(periods, means, color=['blue', 'red'], alpha=0.7)
        plt.title('Pre vs Post COVID Comparison')
        plt.ylabel('Mean Items Per Capita')
    
    plt.subplot(2, 2, 3)
    if len(df) > 0:
        df['anxiety_items_per_capita'].hist(bins=20, alpha=0.7)
        plt.title('Distribution of Anxiety Prescriptions')
        plt.xlabel('Items Per Capita')
        plt.ylabel('Frequency')
    
    plt.subplot(2, 2, 4)
    # Show sample of LSOA trends
    sample_lsoa_codes = df['lsoa_code'].unique()[:5]
    for lsoa in sample_lsoa_codes:
        lsoa_data = df[df['lsoa_code'] == lsoa].sort_values('year_month')
        plt.plot(range(len(lsoa_data)), lsoa_data['anxiety_items_per_capita'], 
                marker='o', label=lsoa[:8]+'...')
    plt.title('Sample LSOA Trends')
    plt.xlabel('Time')
    plt.ylabel('Items Per Capita')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('quick_anxiety_analysis.png', dpi=300, bbox_inches='tight')
    print("Visualization saved to: quick_anxiety_analysis.png")
    
    return df

if __name__ == "__main__":
    results = run_quick_analysis()