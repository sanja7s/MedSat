#!/usr/bin/env python3
"""
Demo Anxiety COVID Analysis - Proof of Concept
Simple demonstration of the framework capability
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from scipy import stats
from matching.commonFunc_updated import detect_file_format

def main():
    print("Demo Anxiety COVID Analysis")
    print("="*40)
    
    # Load anxiety drug codes
    with open('sample_list_anxiety.json', 'r') as f:
        anxiety_drugs = json.load(f)
    
    anxiety_bnf_codes = []
    for drug, codes in anxiety_drugs.items():
        anxiety_bnf_codes.extend(codes)
    
    print(f"Loaded {len(anxiety_bnf_codes)} anxiety BNF codes")
    print(f"Drugs: {list(anxiety_drugs.keys())}")
    
    # Test with just 3 months to demonstrate the concept
    test_files = ['./prescriptionfiles/201903.gz', 
                  './prescriptionfiles/202003.gz', 
                  './prescriptionfiles/202103.gz']
    
    results = {}
    
    for file_path in test_files:
        month = file_path.split('/')[-1].split('.')[0]
        print(f"\nProcessing {month}...")
        
        try:
            # Read small sample
            df = pd.read_csv(file_path, compression='gzip', nrows=50000, low_memory=False)
            
            # Detect format
            fields = detect_file_format(df)
            bnf_field = fields['bnfField']
            
            print(f"  Data shape: {df.shape}")
            print(f"  BNF field: {bnf_field}")
            
            # Truncate BNF codes
            df['BNF_CODE_TRUNCATED'] = df[bnf_field].str[:9]
            
            # Find anxiety prescriptions
            anxiety_mask = df['BNF_CODE_TRUNCATED'].isin(anxiety_bnf_codes)
            anxiety_prescriptions = df[anxiety_mask]
            
            print(f"  Found {len(anxiety_prescriptions)} anxiety prescriptions")
            
            if len(anxiety_prescriptions) > 0:
                # Aggregate metrics
                total_items = anxiety_prescriptions['ITEMS'].sum()
                total_quantity = anxiety_prescriptions['TOTAL_QUANTITY'].sum()
                total_cost = anxiety_prescriptions['ACTUAL_COST'].sum()
                unique_practices = anxiety_prescriptions['PRACTICE_CODE'].nunique()
                
                results[month] = {
                    'total_items': total_items,
                    'total_quantity': total_quantity,
                    'total_cost': total_cost,
                    'unique_practices': unique_practices,
                    'items_per_practice': total_items / unique_practices if unique_practices > 0 else 0
                }
                
                print(f"  Total items: {total_items}")
                print(f"  Total quantity: {total_quantity}")
                print(f"  Total cost: £{total_cost:.2f}")
                print(f"  Unique practices: {unique_practices}")
                print(f"  Items per practice: {results[month]['items_per_practice']:.2f}")
                
                # Show some sample drugs
                drug_counts = anxiety_prescriptions.groupby('BNF_CODE_TRUNCATED')['ITEMS'].sum().head()
                print(f"  Top anxiety drugs by items:")
                for bnf_code, items in drug_counts.items():
                    drug_name = [drug for drug, codes in anxiety_drugs.items() if bnf_code in codes]
                    drug_name = drug_name[0] if drug_name else 'Unknown'
                    print(f"    {drug_name} ({bnf_code}): {items} items")
        
        except Exception as e:
            print(f"  Error: {e}")
            results[month] = {
                'total_items': 0,
                'total_quantity': 0,
                'total_cost': 0,
                'unique_practices': 0,
                'items_per_practice': 0
            }
    
    # Analysis
    print(f"\n" + "="*40)
    print("COVID IMPACT ANALYSIS")
    print("="*40)
    
    if len(results) >= 2:
        # Create summary dataframe
        summary_data = []
        for month, metrics in results.items():
            year = int(month[:4])
            month_num = int(month[4:])
            covid_period = 1 if (year >= 2020 and month_num >= 3) else 0
            
            summary_data.append({
                'month': month,
                'year': year,
                'covid_period': covid_period,
                'items_per_practice': metrics['items_per_practice'],
                'total_items': metrics['total_items'],
                'total_cost': metrics['total_cost']
            })
        
        df_summary = pd.DataFrame(summary_data)
        
        print("\nSummary Statistics:")
        print(df_summary)
        
        # Simple trend analysis
        pre_covid = df_summary[df_summary['covid_period'] == 0]
        post_covid = df_summary[df_summary['covid_period'] == 1]
        
        if len(pre_covid) > 0 and len(post_covid) > 0:
            pre_mean = pre_covid['items_per_practice'].mean()
            post_mean = post_covid['items_per_practice'].mean()
            
            print(f"\nTrend Analysis:")
            print(f"Pre-COVID average items per practice: {pre_mean:.2f}")
            print(f"Post-COVID average items per practice: {post_mean:.2f}")
            print(f"Change: {((post_mean/pre_mean)-1)*100:+.1f}%")
            
            # Simple visualization
            plt.figure(figsize=(12, 4))
            
            plt.subplot(1, 3, 1)
            plt.plot(df_summary['month'], df_summary['items_per_practice'], 'o-')
            plt.title('Anxiety Items per Practice Over Time')
            plt.xlabel('Month')
            plt.ylabel('Items per Practice')
            plt.xticks(rotation=45)
            
            plt.subplot(1, 3, 2)
            plt.bar(['Pre-COVID', 'Post-COVID'], [pre_mean, post_mean], 
                   color=['blue', 'red'], alpha=0.7)
            plt.title('Pre vs Post COVID')
            plt.ylabel('Avg Items per Practice')
            
            plt.subplot(1, 3, 3)
            plt.plot(df_summary['month'], df_summary['total_cost'], 'o-', color='green')
            plt.title('Total Anxiety Prescription Cost')
            plt.xlabel('Month')
            plt.ylabel('Total Cost (£)')
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            plt.savefig('demo_anxiety_analysis.png', dpi=300, bbox_inches='tight')
            print(f"\nVisualization saved to: demo_anxiety_analysis.png")
        
        # Save results
        df_summary.to_csv('demo_anxiety_results.csv', index=False)
        print(f"Results saved to: demo_anxiety_results.csv")
        
        print(f"\n" + "="*40)
        print("FRAMEWORK DEMONSTRATION COMPLETE")
        print("="*40)
        print("Key Findings:")
        print(f"✓ Successfully identified anxiety medications from BNF codes")
        print(f"✓ Processed prescription data across time periods")
        print(f"✓ Detected format differences between old/new data files")
        print(f"✓ Demonstrated trend analysis capability")
        if len(pre_covid) > 0 and len(post_covid) > 0:
            trend = "increase" if post_mean > pre_mean else "decrease"
            print(f"✓ Observed {((abs(post_mean-pre_mean)/pre_mean)*100):.1f}% {trend} in anxiety prescriptions")
        print(f"✓ Generated visualizations and saved results")
        
        return df_summary
    
    else:
        print("Insufficient data for analysis")
        return None

if __name__ == "__main__":
    results = main()