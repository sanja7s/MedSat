#!/usr/bin/env python3
"""
Comprehensive Anxiety COVID Analysis
Proper before/after analysis with sufficient months on each side of March 2020 lockdown
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from scipy import stats
import os
import sys
sys.path.append('..')
from matching.commonFunc_updated import detect_file_format

def main():
    print("Comprehensive Anxiety COVID Analysis")
    print("="*50)
    print("Analyzing prescription trends before/after UK lockdown (March 23, 2020)")
    
    # Load anxiety drug codes
    with open('../sample_list_anxiety.json', 'r') as f:
        anxiety_drugs = json.load(f)
    
    anxiety_bnf_codes = []
    for drug, codes in anxiety_drugs.items():
        anxiety_bnf_codes.extend(codes)
    
    print(f"Loaded {len(anxiety_bnf_codes)} anxiety BNF codes")
    print(f"Anxiety medications: {list(anxiety_drugs.keys())}")
    
    # Define focused time periods
    # Pre-COVID: 3 months before lockdown (Dec 2019 - Feb 2020) 
    pre_covid_months = ['201912', '202001', '202002']
    
    # Post-COVID: 3 months after lockdown started (March 2020 - May 2020)
    post_covid_months = ['202003', '202004', '202005']
    
    all_months = pre_covid_months + post_covid_months
    
    print(f"\nAnalysis periods:")
    print(f"Pre-COVID (3 months): {pre_covid_months}")
    print(f"Post-COVID (3 months): {post_covid_months}")
    
    results = {}
    
    for month in all_months:
        file_path = f'../prescriptionfiles/{month}.gz'
        print(f"\nProcessing {month}...")
        
        if not os.path.exists(file_path):
            print(f"  File not found: {file_path}")
            continue
            
        try:
            # Read larger sample for better representation
            df = pd.read_csv(file_path, compression='gzip', nrows=100000, low_memory=False)
            
            # Detect format
            fields = detect_file_format(df)
            bnf_field = fields['bnfField']
            
            print(f"  Data shape: {df.shape}")
            
            # Truncate BNF codes for matching
            df['BNF_CODE_TRUNCATED'] = df[bnf_field].str[:9]
            
            # Find anxiety prescriptions
            anxiety_mask = df['BNF_CODE_TRUNCATED'].isin(anxiety_bnf_codes)
            anxiety_prescriptions = df[anxiety_mask]
            
            print(f"  Found {len(anxiety_prescriptions)} anxiety prescriptions")
            
            if len(anxiety_prescriptions) > 0:
                # Calculate comprehensive metrics
                total_items = anxiety_prescriptions['ITEMS'].sum()
                total_quantity = anxiety_prescriptions['TOTAL_QUANTITY'].sum()
                total_cost = anxiety_prescriptions['ACTUAL_COST'].sum()
                unique_practices = anxiety_prescriptions['PRACTICE_CODE'].nunique()
                
                # Calculate per-practice metrics
                items_per_practice = total_items / unique_practices if unique_practices > 0 else 0
                quantity_per_practice = total_quantity / unique_practices if unique_practices > 0 else 0
                cost_per_practice = total_cost / unique_practices if unique_practices > 0 else 0
                
                results[month] = {
                    'total_items': total_items,
                    'total_quantity': total_quantity,
                    'total_cost': total_cost,
                    'unique_practices': unique_practices,
                    'items_per_practice': items_per_practice,
                    'quantity_per_practice': quantity_per_practice,
                    'cost_per_practice': cost_per_practice
                }
                
                print(f"  Total items: {total_items:,}")
                print(f"  Items per practice: {items_per_practice:.2f}")
                print(f"  Total cost: £{total_cost:,.2f}")
                
                # Show drug breakdown
                drug_breakdown = anxiety_prescriptions.groupby('BNF_CODE_TRUNCATED').agg({
                    'ITEMS': 'sum',
                    'TOTAL_QUANTITY': 'sum',
                    'ACTUAL_COST': 'sum'
                }).sort_values('ITEMS', ascending=False).head(3)
                
                print(f"  Top 3 anxiety drugs:")
                for bnf_code, row in drug_breakdown.iterrows():
                    drug_name = [drug for drug, codes in anxiety_drugs.items() if bnf_code in codes]
                    drug_name = drug_name[0] if drug_name else 'Unknown'
                    print(f"    {drug_name}: {row['ITEMS']} items, £{row['ACTUAL_COST']:.2f}")
            else:
                # Zero results
                results[month] = {
                    'total_items': 0,
                    'total_quantity': 0,
                    'total_cost': 0,
                    'unique_practices': 0,
                    'items_per_practice': 0,
                    'quantity_per_practice': 0,
                    'cost_per_practice': 0
                }
        
        except Exception as e:
            print(f"  Error processing {month}: {e}")
            results[month] = {
                'total_items': 0,
                'total_quantity': 0,
                'total_cost': 0,
                'unique_practices': 0,
                'items_per_practice': 0,
                'quantity_per_practice': 0,
                'cost_per_practice': 0
            }
    
    # Statistical Analysis
    print(f"\n" + "="*60)
    print("COMPREHENSIVE COVID IMPACT ANALYSIS")
    print("="*60)
    
    if len(results) >= 3:  # Need sufficient data points
        # Create analysis dataframe
        analysis_data = []
        for month, metrics in results.items():
            year = int(month[:4])
            month_num = int(month[4:])
            
            # Define COVID periods more precisely
            # Pre-COVID: Before March 2020
            # Post-COVID: March 2020 onwards (lockdown announced March 23, 2020)
            is_post_covid = (year > 2020) or (year == 2020 and month_num >= 3)
            
            analysis_data.append({
                'month': month,
                'year': year,
                'month_num': month_num,
                'covid_period': 1 if is_post_covid else 0,
                'period_label': 'Post-COVID' if is_post_covid else 'Pre-COVID',
                'items_per_practice': metrics['items_per_practice'],
                'quantity_per_practice': metrics['quantity_per_practice'],
                'cost_per_practice': metrics['cost_per_practice'],
                'total_items': metrics['total_items'],
                'total_cost': metrics['total_cost']
            })
        
        df_analysis = pd.DataFrame(analysis_data)
        
        print("\nMonthly Summary:")
        print(df_analysis[['month', 'period_label', 'items_per_practice', 'cost_per_practice']])
        
        # Separate pre and post COVID data
        pre_covid = df_analysis[df_analysis['covid_period'] == 0]
        post_covid = df_analysis[df_analysis['covid_period'] == 1]
        
        print(f"\n1. DESCRIPTIVE STATISTICS")
        print("-" * 30)
        print(f"Pre-COVID months analyzed: {len(pre_covid)}")
        print(f"Post-COVID months analyzed: {len(post_covid)}")
        
        if len(pre_covid) > 0 and len(post_covid) > 0:
            # Calculate means and standard deviations
            pre_mean_items = pre_covid['items_per_practice'].mean()
            pre_std_items = pre_covid['items_per_practice'].std()
            post_mean_items = post_covid['items_per_practice'].mean()
            post_std_items = post_covid['items_per_practice'].std()
            
            pre_mean_cost = pre_covid['cost_per_practice'].mean()
            post_mean_cost = post_covid['cost_per_practice'].mean()
            
            print(f"\nAnxiety Items per Practice:")
            print(f"  Pre-COVID:  {pre_mean_items:.2f} ± {pre_std_items:.2f}")
            print(f"  Post-COVID: {post_mean_items:.2f} ± {post_std_items:.2f}")
            print(f"  Change: {((post_mean_items/pre_mean_items)-1)*100:+.1f}%")
            
            print(f"\nCost per Practice:")
            print(f"  Pre-COVID:  £{pre_mean_cost:.2f}")
            print(f"  Post-COVID: £{post_mean_cost:.2f}")
            print(f"  Change: {((post_mean_cost/pre_mean_cost)-1)*100:+.1f}%")
            
            # Statistical significance testing
            print(f"\n2. STATISTICAL SIGNIFICANCE TESTS")
            print("-" * 30)
            
            # T-test for items per practice
            t_stat_items, p_val_items = stats.ttest_ind(post_covid['items_per_practice'], 
                                                       pre_covid['items_per_practice'])
            
            # T-test for cost per practice
            t_stat_cost, p_val_cost = stats.ttest_ind(post_covid['cost_per_practice'], 
                                                     pre_covid['cost_per_practice'])
            
            print(f"Items per Practice T-test:")
            print(f"  T-statistic: {t_stat_items:.4f}")
            print(f"  P-value: {p_val_items:.6f}")
            print(f"  Significant at 5%: {'Yes' if p_val_items < 0.05 else 'No'}")
            
            print(f"\nCost per Practice T-test:")
            print(f"  T-statistic: {t_stat_cost:.4f}")
            print(f"  P-value: {p_val_cost:.6f}")
            print(f"  Significant at 5%: {'Yes' if p_val_cost < 0.05 else 'No'}")
            
            # Effect size (Cohen's d)
            pooled_std_items = np.sqrt(((len(pre_covid) - 1) * pre_covid['items_per_practice'].var() + 
                                       (len(post_covid) - 1) * post_covid['items_per_practice'].var()) / 
                                      (len(pre_covid) + len(post_covid) - 2))
            cohens_d_items = (post_covid['items_per_practice'].mean() - 
                             pre_covid['items_per_practice'].mean()) / pooled_std_items
            
            print(f"\nEffect Size (Cohen's d): {cohens_d_items:.4f}")
            effect_interpretation = ("Small" if abs(cohens_d_items) < 0.5 else 
                                   "Medium" if abs(cohens_d_items) < 0.8 else "Large")
            print(f"Effect size interpretation: {effect_interpretation}")
            
            # Time trend analysis
            print(f"\n3. TIME TREND ANALYSIS")
            print("-" * 30)
            
            # Calculate month-to-month changes
            df_sorted = df_analysis.sort_values('month')
            monthly_changes = []
            for i in range(1, len(df_sorted)):
                prev_val = df_sorted.iloc[i-1]['items_per_practice']
                curr_val = df_sorted.iloc[i]['items_per_practice']
                if prev_val > 0:
                    change = ((curr_val / prev_val) - 1) * 100
                    monthly_changes.append(change)
            
            if monthly_changes:
                avg_monthly_change = np.mean(monthly_changes)
                print(f"Average monthly change: {avg_monthly_change:+.2f}%")
                
                # Identify the biggest change around lockdown period
                lockdown_month_idx = df_sorted[df_sorted['month'] == '202003'].index
                if len(lockdown_month_idx) > 0:
                    lockdown_idx = lockdown_month_idx[0]
                    if lockdown_idx > 0:
                        feb_val = df_sorted.iloc[lockdown_idx-1]['items_per_practice']
                        mar_val = df_sorted.iloc[lockdown_idx]['items_per_practice']
                        if feb_val > 0:
                            lockdown_change = ((mar_val / feb_val) - 1) * 100
                            print(f"Feb 2020 → Mar 2020 change: {lockdown_change:+.2f}%")
        
        # Create comprehensive visualizations
        create_comprehensive_visualizations(df_analysis, pre_covid, post_covid)
        
        # Save detailed results
        df_analysis.to_csv('comprehensive_anxiety_covid_analysis.csv', index=False)
        print(f"\nDetailed results saved to: comprehensive_anxiety_covid_analysis.csv")
        
        # Summary
        print(f"\n" + "="*60)
        print("HYPOTHESIS TEST RESULTS")
        print("="*60)
        print(f"Hypothesis: COVID-19 lockdown increased anxiety prescriptions")
        
        if len(pre_covid) > 0 and len(post_covid) > 0:
            result = "SUPPORTED" if post_mean_items > pre_mean_items and p_val_items < 0.05 else "NOT SUPPORTED"
            print(f"Result: {result}")
            print(f"Evidence:")
            print(f"  • {len(pre_covid)} pre-COVID months vs {len(post_covid)} post-COVID months")
            print(f"  • {((post_mean_items/pre_mean_items)-1)*100:+.1f}% change in prescriptions per practice")
            print(f"  • Statistical significance: p = {p_val_items:.4f}")
            print(f"  • Effect size: {cohens_d_items:.3f} ({effect_interpretation})")
            
        return df_analysis
    
    else:
        print("Insufficient data for comprehensive analysis")
        return None

def create_comprehensive_visualizations(df_analysis, pre_covid, post_covid):
    """Create comprehensive visualizations"""
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Comprehensive COVID-19 Impact on Anxiety Prescriptions', fontsize=16, fontweight='bold')
    
    # 1. Time series of items per practice
    df_sorted = df_analysis.sort_values('month')
    axes[0,0].plot(range(len(df_sorted)), df_sorted['items_per_practice'], 'o-', linewidth=2, markersize=6)
    axes[0,0].axvline(len(df_sorted[df_sorted['covid_period']==0])-0.5, color='red', linestyle='--', 
                      label='COVID Lockdown', alpha=0.7)
    axes[0,0].set_title('Anxiety Items per Practice Over Time')
    axes[0,0].set_xlabel('Month')
    axes[0,0].set_ylabel('Items per Practice')
    axes[0,0].set_xticks(range(len(df_sorted)))
    axes[0,0].set_xticklabels(df_sorted['month'], rotation=45)
    axes[0,0].legend()
    axes[0,0].grid(True, alpha=0.3)
    
    # 2. Before/After comparison - Items
    if len(pre_covid) > 0 and len(post_covid) > 0:
        periods = ['Pre-COVID\n(3 months)', 'Post-COVID\n(3 months)']
        means = [pre_covid['items_per_practice'].mean(), post_covid['items_per_practice'].mean()]
        stds = [pre_covid['items_per_practice'].std(), post_covid['items_per_practice'].std()]
        
        axes[0,1].bar(periods, means, yerr=stds, capsize=5, alpha=0.7, color=['blue', 'red'])
        axes[0,1].set_title('Pre vs Post COVID: Items per Practice')
        axes[0,1].set_ylabel('Mean Items per Practice')
        
        # Add statistical annotation
        t_stat, p_val = stats.ttest_ind(post_covid['items_per_practice'], pre_covid['items_per_practice'])
        sig_text = f"p = {p_val:.4f}\n{'Significant' if p_val < 0.05 else 'Not Significant'}"
        axes[0,1].text(0.5, max(means) * 1.1, sig_text, ha='center', va='bottom', 
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
    
    # 3. Before/After comparison - Cost
    if len(pre_covid) > 0 and len(post_covid) > 0:
        cost_means = [pre_covid['cost_per_practice'].mean(), post_covid['cost_per_practice'].mean()]
        cost_stds = [pre_covid['cost_per_practice'].std(), post_covid['cost_per_practice'].std()]
        
        axes[0,2].bar(periods, cost_means, yerr=cost_stds, capsize=5, alpha=0.7, color=['green', 'orange'])
        axes[0,2].set_title('Pre vs Post COVID: Cost per Practice')
        axes[0,2].set_ylabel('Mean Cost per Practice (£)')
    
    # 4. Distribution comparison
    if len(pre_covid) > 0 and len(post_covid) > 0:
        axes[1,0].hist(pre_covid['items_per_practice'], alpha=0.6, label='Pre-COVID', bins=10, 
                       density=True, color='blue')
        axes[1,0].hist(post_covid['items_per_practice'], alpha=0.6, label='Post-COVID', bins=10, 
                       density=True, color='red')
        axes[1,0].set_title('Distribution of Items per Practice')
        axes[1,0].set_xlabel('Items per Practice')
        axes[1,0].set_ylabel('Density')
        axes[1,0].legend()
    
    # 5. Monthly totals over time
    axes[1,1].plot(range(len(df_sorted)), df_sorted['total_items'], 'o-', color='purple', linewidth=2)
    axes[1,1].axvline(len(df_sorted[df_sorted['covid_period']==0])-0.5, color='red', linestyle='--', 
                      alpha=0.7)
    axes[1,1].set_title('Total Anxiety Items Over Time')
    axes[1,1].set_xlabel('Month')
    axes[1,1].set_ylabel('Total Items')
    axes[1,1].set_xticks(range(len(df_sorted)))
    axes[1,1].set_xticklabels(df_sorted['month'], rotation=45)
    axes[1,1].grid(True, alpha=0.3)
    
    # 6. Cost trends
    axes[1,2].plot(range(len(df_sorted)), df_sorted['total_cost'], 'o-', color='green', linewidth=2)
    axes[1,2].axvline(len(df_sorted[df_sorted['covid_period']==0])-0.5, color='red', linestyle='--', 
                      alpha=0.7)
    axes[1,2].set_title('Total Anxiety Prescription Cost Over Time')
    axes[1,2].set_xlabel('Month')
    axes[1,2].set_ylabel('Total Cost (£)')
    axes[1,2].set_xticks(range(len(df_sorted)))
    axes[1,2].set_xticklabels(df_sorted['month'], rotation=45)
    axes[1,2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('comprehensive_anxiety_covid_analysis.png', dpi=300, bbox_inches='tight')
    print(f"Comprehensive visualization saved to: comprehensive_anxiety_covid_analysis.png")

if __name__ == "__main__":
    results = main()