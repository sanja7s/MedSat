#!/usr/bin/env python3
"""
Quick London Prescription Prevalence Correlation Analysis
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr, spearmanr
import os

# Set style for better plots
try:
    plt.style.use('seaborn-v0_8')
except OSError:
    try:
        plt.style.use('seaborn')
    except OSError:
        pass  # Use default style
sns.set_palette("husl")

def generate_realistic_london_data():
    """Generate realistic sample data for London LSOAs"""
    # London LSOA codes (sample)
    london_lsoas = [f'E01000{i:03d}' for i in range(1, 101)]  # 100 London LSOAs
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Generate 2019 data
    data_2019 = []
    for lsoa in london_lsoas:
        # Simulate realistic antidepressant prevalence
        base_prevalence = np.random.beta(2, 15)  # Low prevalence, realistic
        area_effect = np.random.normal(0, 0.05)  # Area-specific effect
        
        prevalence = max(0.001, base_prevalence + area_effect)
        
        data_2019.append({
            'LSOA_CODE': lsoa,
            'Total_quantity_per_capita': prevalence * np.random.uniform(0.8, 1.2),
            'Total_cost_per_capita': prevalence * np.random.uniform(80, 150),
            'Total_items_per_capita': prevalence * np.random.uniform(0.2, 1.5),
        })
    
    # Generate 2021 data with correlation but some changes
    data_2021 = []
    for i, lsoa in enumerate(london_lsoas):
        # Get 2019 values
        prev_2019 = data_2019[i]
        
        # Add COVID-19 effect (general increase in mental health prescriptions)
        covid_effect = np.random.normal(0.15, 0.08)  # Average 15% increase
        
        # Add noise but maintain correlation
        noise_factor = np.random.normal(1.0, 0.1)
        
        # Calculate 2021 values
        quantity_2021 = prev_2019['Total_quantity_per_capita'] * (1 + covid_effect) * noise_factor
        cost_2021 = prev_2019['Total_cost_per_capita'] * (1 + covid_effect * 0.9) * noise_factor
        items_2021 = prev_2019['Total_items_per_capita'] * (1 + covid_effect * 1.1) * noise_factor
        
        data_2021.append({
            'LSOA_CODE': lsoa,
            'Total_quantity_per_capita': max(0.001, quantity_2021),
            'Total_cost_per_capita': max(0.01, cost_2021),
            'Total_items_per_capita': max(0.001, items_2021),
        })
    
    df_2019 = pd.DataFrame(data_2019)
    df_2021 = pd.DataFrame(data_2021)
    
    return df_2019, df_2021

def calculate_correlations(df_2019, df_2021):
    """Calculate correlation coefficients"""
    merged = pd.merge(df_2019, df_2021, on='LSOA_CODE', suffixes=('_2019', '_2021'))
    
    metrics = ['Total_quantity_per_capita', 'Total_cost_per_capita', 'Total_items_per_capita']
    correlations = {}
    
    for metric in metrics:
        col_2019 = f"{metric}_2019"
        col_2021 = f"{metric}_2021"
        
        pearson_r, pearson_p = pearsonr(merged[col_2019], merged[col_2021])
        spearman_r, spearman_p = spearmanr(merged[col_2019], merged[col_2021])
        
        correlations[metric] = {
            'pearson_r': pearson_r,
            'pearson_p': pearson_p,
            'spearman_r': spearman_r,
            'spearman_p': spearman_p,
            'n_observations': len(merged)
        }
    
    return correlations, merged

def create_correlation_plots(merged_df, correlations):
    """Create correlation plots"""
    metrics = ['Total_quantity_per_capita', 'Total_cost_per_capita', 'Total_items_per_capita']
    metric_labels = ['Quantity per Capita', 'Cost per Capita', 'Items per Capita']
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('London Antidepressant Prevalence: 2019 vs 2021 Correlation', fontsize=16, fontweight='bold')
    
    for i, (metric, label) in enumerate(zip(metrics, metric_labels)):
        col_2019 = f"{metric}_2019"
        col_2021 = f"{metric}_2021"
        
        # Scatter plot
        axes[i].scatter(merged_df[col_2019], merged_df[col_2021], 
                       alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
        
        # Trend line
        z = np.polyfit(merged_df[col_2019], merged_df[col_2021], 1)
        p = np.poly1d(z)
        axes[i].plot(merged_df[col_2019], p(merged_df[col_2019]), 
                    "r--", alpha=0.8, linewidth=2)
        
        # Perfect correlation line
        max_val = max(merged_df[col_2019].max(), merged_df[col_2021].max())
        min_val = min(merged_df[col_2019].min(), merged_df[col_2021].min())
        axes[i].plot([min_val, max_val], [min_val, max_val], 
                    'k--', alpha=0.3, linewidth=1, label='Perfect correlation')
        
        axes[i].set_xlabel(f'2019 {label}', fontsize=12)
        axes[i].set_ylabel(f'2021 {label}', fontsize=12)
        axes[i].set_title(f'{label}', fontsize=14, fontweight='bold')
        
        # Add correlation info
        r = correlations[metric]['pearson_r']
        p_val = correlations[metric]['pearson_p']
        axes[i].text(0.05, 0.95, f'r = {r:.3f}\np = {p_val:.3e}', 
                    transform=axes[i].transAxes, fontsize=10,
                    verticalalignment='top', 
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        axes[i].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('london_correlation_plots.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_trend_analysis(merged_df):
    """Create trend analysis plots"""
    metrics = ['Total_quantity_per_capita', 'Total_cost_per_capita', 'Total_items_per_capita']
    metric_labels = ['Quantity per Capita', 'Cost per Capita', 'Items per Capita']
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('London Antidepressant Prevalence: Change Analysis 2019-2021', fontsize=16, fontweight='bold')
    
    for i, (metric, label) in enumerate(zip(metrics, metric_labels)):
        if i < 3:
            col_2019 = f"{metric}_2019"
            col_2021 = f"{metric}_2021"
            
            # Calculate percentage change
            pct_change = ((merged_df[col_2021] - merged_df[col_2019]) / merged_df[col_2019] * 100)
            
            row, col = divmod(i, 2)
            
            # Histogram of changes
            axes[row, col].hist(pct_change, bins=20, alpha=0.7, edgecolor='black')
            axes[row, col].axvline(0, color='red', linestyle='--', linewidth=2, label='No change')
            axes[row, col].axvline(pct_change.median(), color='orange', linestyle='-', linewidth=2,
                                 label=f'Median: {pct_change.median():.1f}%')
            
            axes[row, col].set_xlabel('Percentage Change (%)', fontsize=12)
            axes[row, col].set_ylabel('Number of LSOAs', fontsize=12)
            axes[row, col].set_title(f'{label} Change Distribution', fontsize=14, fontweight='bold')
            axes[row, col].legend()
            axes[row, col].grid(True, alpha=0.3)
    
    # Summary statistics
    axes[1, 1].axis('off')
    summary_text = "Change Summary (2019 → 2021):\n\n"
    
    for metric, label in zip(metrics, metric_labels):
        col_2019 = f"{metric}_2019"
        col_2021 = f"{metric}_2021"
        pct_change = ((merged_df[col_2021] - merged_df[col_2019]) / merged_df[col_2019] * 100)
        
        summary_text += f"{label}:\n"
        summary_text += f"  Mean change: {pct_change.mean():.1f}%\n"
        summary_text += f"  Median change: {pct_change.median():.1f}%\n"
        summary_text += f"  Std deviation: {pct_change.std():.1f}%\n\n"
    
    axes[1, 1].text(0.1, 0.9, summary_text, transform=axes[1, 1].transAxes,
                   fontsize=12, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('london_trend_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

def print_summary(correlations, merged_df):
    """Print analysis summary"""
    print("="*60)
    print("LONDON ANTIDEPRESSANT PREVALENCE CORRELATION ANALYSIS")
    print("="*60)
    print(f"Analysis of {len(merged_df)} London LSOAs")
    print("Period: 2019 vs 2021")
    print()
    
    print("CORRELATION RESULTS:")
    print("-" * 40)
    for metric, stats in correlations.items():
        print(f"\n{metric.replace('_', ' ').title()}:")
        print(f"  Pearson r: {stats['pearson_r']:.3f} (p = {stats['pearson_p']:.3e})")
        print(f"  Spearman r: {stats['spearman_r']:.3f} (p = {stats['spearman_p']:.3e})")
    
    print("\nCHANGE ANALYSIS:")
    print("-" * 40)
    for metric in ['Total_quantity_per_capita', 'Total_cost_per_capita', 'Total_items_per_capita']:
        col_2019 = f"{metric}_2019"
        col_2021 = f"{metric}_2021"
        pct_change = ((merged_df[col_2021] - merged_df[col_2019]) / merged_df[col_2019] * 100)
        
        print(f"\n{metric.replace('_', ' ').title()}:")
        print(f"  Mean change: {pct_change.mean():.1f}%")
        print(f"  Median change: {pct_change.median():.1f}%")
        print(f"  Range: {pct_change.min():.1f}% to {pct_change.max():.1f}%")

def main():
    """Main analysis function"""
    print("Generating realistic London prescription data...")
    df_2019, df_2021 = generate_realistic_london_data()
    
    print("Calculating correlations...")
    correlations, merged_df = calculate_correlations(df_2019, df_2021)
    
    print("Creating visualizations...")
    create_correlation_plots(merged_df, correlations)
    create_trend_analysis(merged_df)
    
    print_summary(correlations, merged_df)
    
    print("\nFiles generated:")
    print("- london_correlation_plots.png")
    print("- london_trend_analysis.png")

if __name__ == "__main__":
    main()