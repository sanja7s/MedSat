#!/usr/bin/env python3
"""
Anxiety COVID Impact Analysis
Generate time series of anxiety prescriptions in London from March 2019 to March 2021
to test the hypothesis that COVID-19 increased anxiety prescriptions when controlled for demographics.
"""

import pandas as pd
import numpy as np
import json
import os
import glob
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.linear_model import LinearRegression
from matching.commonFunc_updated import detect_file_format, prepare_lsoa_GP_population
from sources.downloader import Downloader
from tqdm import tqdm

def load_anxiety_drugs():
    """Load anxiety drug BNF codes"""
    with open('sample_list_anxiety.json', 'r') as f:
        anxiety_drugs = json.load(f)
    
    # Flatten all BNF codes
    anxiety_bnf_codes = []
    for drug, codes in anxiety_drugs.items():
        anxiety_bnf_codes.extend(codes)
    
    return anxiety_bnf_codes, anxiety_drugs

def load_census_data():
    """Load census data for demographic controls"""
    census_data = {}
    
    # Load 2019, 2020, 2021 data
    for year in ['Mid-2019 LSOA 2021', 'Mid-2020 LSOA 2021', 'Mid-2021 LSOA 2021']:
        df = pd.read_excel('mappings/census_data_2021.xlsx', sheet_name=year, header=3)
        
        # Calculate key demographic variables
        df['total_population'] = df['Total']
        
        # Calculate age groups
        # Young adults (20-39)
        young_adult_cols = [f'F{i}' for i in range(20, 40)] + [f'M{i}' for i in range(20, 40)]
        young_adult_cols = [col for col in young_adult_cols if col in df.columns]
        df['young_adults'] = df[young_adult_cols].sum(axis=1)
        
        # Middle aged (40-64)
        middle_aged_cols = [f'F{i}' for i in range(40, 65)] + [f'M{i}' for i in range(40, 65)]
        middle_aged_cols = [col for col in middle_aged_cols if col in df.columns]
        df['middle_aged'] = df[middle_aged_cols].sum(axis=1)
        
        # Elderly (65+)
        elderly_cols = [f'F{i}' for i in range(65, 91)] + [f'M{i}' for i in range(65, 91)]
        elderly_cols = [col for col in elderly_cols if col in df.columns]
        df['elderly'] = df[elderly_cols].sum(axis=1)
        
        # Calculate proportions
        df['prop_young_adults'] = df['young_adults'] / df['total_population']
        df['prop_middle_aged'] = df['middle_aged'] / df['total_population']
        df['prop_elderly'] = df['elderly'] / df['total_population']
        
        # Store with year key
        year_key = year.split()[0].replace('Mid-', '')
        census_data[year_key] = df[['LSOA 2021 Code', 'total_population', 'young_adults', 
                                   'middle_aged', 'elderly', 'prop_young_adults', 
                                   'prop_middle_aged', 'prop_elderly']].copy()
    
    return census_data

def identify_london_lsoas():
    """Identify London LSOA codes"""
    # Load GP mapping to identify London practices
    with open('mappings/GPs.json', 'r') as f:
        gps_data = json.load(f)
    
    # London region codes (approximate)
    london_regions = ['Y05', 'Y06', 'Y07', 'Y08', 'Y09', 'Y10', 'Y11', 'Y12', 'Y13', 'Y14', 
                      'Y15', 'Y16', 'Y17', 'Y18', 'Y19', 'Y20', 'Y21', 'Y22', 'Y23', 'Y24']
    
    london_practices = []
    for practice_code, practice_info in gps_data.items():
        if any(region in practice_info.get('Region', '') for region in london_regions):
            london_practices.append(practice_code)
    
    # Get LSOA codes associated with London practices
    with open('mappings/GP_LSOA_PATIENTSDIST.json', 'r') as f:
        gp_lsoa_data = json.load(f)
    
    london_lsoas = set()
    for practice_code in london_practices:
        if practice_code in gp_lsoa_data:
            for lsoa_code in gp_lsoa_data[practice_code]['Patient_registry_LSOA'].keys():
                london_lsoas.add(lsoa_code)
    
    return list(london_lsoas)

def process_prescription_data(start_month, end_month, anxiety_bnf_codes):
    """Process prescription data for the time period"""
    
    # Download data
    downloader = Downloader(sourcesFile="sources/serialized_file_paths.json", 
                           download_dir="./prescriptionfiles/")
    files = downloader.download_range(start_month, end_month)
    
    monthly_anxiety_data = {}
    
    for file_path in tqdm(files, desc="Processing prescription files"):
        month = file_path.split('/')[-1].split('.')[0]
        print(f"\nProcessing {month}...")
        
        # Read prescription data
        try:
            df = pd.read_csv(file_path, compression='gzip')
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
        
        # Detect file format and get BNF field
        fields = detect_file_format(df)
        bnf_field = fields['bnfField']
        
        # Truncate BNF codes to match our anxiety list
        df['BNF_CODE_TRUNCATED'] = df[bnf_field].str[:9]
        
        # Filter for anxiety medications
        anxiety_prescriptions = df[df['BNF_CODE_TRUNCATED'].isin(anxiety_bnf_codes)]
        
        print(f"Found {len(anxiety_prescriptions)} anxiety prescriptions in {month}")
        
        if len(anxiety_prescriptions) > 0:
            # Group by practice and sum metrics
            practice_summary = anxiety_prescriptions.groupby('PRACTICE_CODE').agg({
                'TOTAL_QUANTITY': 'sum',
                'ITEMS': 'sum', 
                'ACTUAL_COST': 'sum'
            }).reset_index()
            
            monthly_anxiety_data[month] = practice_summary
    
    return monthly_anxiety_data

def map_to_lsoa_level(monthly_anxiety_data, london_lsoas):
    """Map practice-level data to LSOA level"""
    
    # Load GP-LSOA mapping
    with open('mappings/GP_LSOA_PATIENTSDIST.json', 'r') as f:
        gp_lsoa_mapping = json.load(f)
    
    monthly_lsoa_data = {}
    
    for month, practice_data in monthly_anxiety_data.items():
        lsoa_data = {}
        
        for _, row in practice_data.iterrows():
            practice_code = row['PRACTICE_CODE']
            
            if practice_code in gp_lsoa_mapping:
                practice_lsoa_dist = gp_lsoa_mapping[practice_code]['Patient_registry_LSOA']
                total_practice_patients = sum(practice_lsoa_dist.values())
                
                for lsoa_code, patient_count in practice_lsoa_dist.items():
                    if lsoa_code in london_lsoas:  # Filter for London only
                        if lsoa_code not in lsoa_data:
                            lsoa_data[lsoa_code] = {
                                'total_quantity': 0,
                                'total_items': 0,
                                'total_cost': 0,
                                'total_patients': 0
                            }
                        
                        # Distribute practice metrics proportionally
                        proportion = patient_count / total_practice_patients
                        lsoa_data[lsoa_code]['total_quantity'] += row['TOTAL_QUANTITY'] * proportion
                        lsoa_data[lsoa_code]['total_items'] += row['ITEMS'] * proportion
                        lsoa_data[lsoa_code]['total_cost'] += row['ACTUAL_COST'] * proportion
                        lsoa_data[lsoa_code]['total_patients'] += patient_count
        
        monthly_lsoa_data[month] = lsoa_data
    
    return monthly_lsoa_data

def create_time_series_dataframe(monthly_lsoa_data, census_data):
    """Create a time series dataframe with demographics"""
    
    records = []
    
    for month, lsoa_data in monthly_lsoa_data.items():
        year = month[:4]
        month_num = month[4:]
        date = f"{year}-{month_num}"
        
        # Get appropriate census year (use 2019 for 2019, 2020 for 2020, 2021 for 2021)
        census_year = year if year in census_data else '2019'
        census_df = census_data[census_year]
        
        for lsoa_code, metrics in lsoa_data.items():
            # Get census data for this LSOA
            lsoa_census = census_df[census_df['LSOA 2021 Code'] == lsoa_code]
            
            if len(lsoa_census) > 0:
                census_row = lsoa_census.iloc[0]
                
                # Calculate per capita metrics
                population = metrics['total_patients']
                if population > 0:
                    record = {
                        'lsoa_code': lsoa_code,
                        'year_month': month,
                        'year': int(year),
                        'month': int(month_num),
                        'date': date,
                        'anxiety_quantity_per_capita': metrics['total_quantity'] / population,
                        'anxiety_items_per_capita': metrics['total_items'] / population,
                        'anxiety_cost_per_capita': metrics['total_cost'] / population,
                        'total_population': census_row['total_population'],
                        'prop_young_adults': census_row['prop_young_adults'],
                        'prop_middle_aged': census_row['prop_middle_aged'],
                        'prop_elderly': census_row['prop_elderly'],
                        'covid_period': 1 if int(year) >= 2020 and int(month_num) >= 3 else 0,
                        'pre_covid': 1 if int(year) == 2019 or (int(year) == 2020 and int(month_num) < 3) else 0,
                        'post_covid': 1 if int(year) >= 2020 and int(month_num) >= 3 else 0
                    }
                    records.append(record)
    
    return pd.DataFrame(records)

def run_covid_impact_analysis(df):
    """Run statistical analysis to test COVID impact hypothesis"""
    
    print("\n" + "="*60)
    print("COVID-19 IMPACT ON ANXIETY PRESCRIPTIONS ANALYSIS")
    print("="*60)
    
    # Basic descriptive statistics
    print("\n1. DESCRIPTIVE STATISTICS")
    print("-" * 30)
    pre_covid = df[df['pre_covid'] == 1]
    post_covid = df[df['post_covid'] == 1]
    
    print(f"Pre-COVID observations: {len(pre_covid)}")
    print(f"Post-COVID observations: {len(post_covid)}")
    
    print(f"\nPre-COVID anxiety prescriptions per capita:")
    print(f"  Mean: {pre_covid['anxiety_items_per_capita'].mean():.6f}")
    print(f"  Median: {pre_covid['anxiety_items_per_capita'].median():.6f}")
    print(f"  Std: {pre_covid['anxiety_items_per_capita'].std():.6f}")
    
    print(f"\nPost-COVID anxiety prescriptions per capita:")
    print(f"  Mean: {post_covid['anxiety_items_per_capita'].mean():.6f}")
    print(f"  Median: {post_covid['anxiety_items_per_capita'].median():.6f}")
    print(f"  Std: {post_covid['anxiety_items_per_capita'].std():.6f}")
    
    # T-test for difference in means
    print("\n2. T-TEST FOR DIFFERENCE IN MEANS")
    print("-" * 30)
    t_stat, p_value = stats.ttest_ind(post_covid['anxiety_items_per_capita'], 
                                     pre_covid['anxiety_items_per_capita'])
    print(f"T-statistic: {t_stat:.4f}")
    print(f"P-value: {p_value:.6f}")
    print(f"Significant at 5% level: {'Yes' if p_value < 0.05 else 'No'}")
    
    # Effect size (Cohen's d)
    pooled_std = np.sqrt(((len(pre_covid) - 1) * pre_covid['anxiety_items_per_capita'].var() + 
                         (len(post_covid) - 1) * post_covid['anxiety_items_per_capita'].var()) / 
                        (len(pre_covid) + len(post_covid) - 2))
    cohens_d = (post_covid['anxiety_items_per_capita'].mean() - 
                pre_covid['anxiety_items_per_capita'].mean()) / pooled_std
    print(f"Cohen's d (effect size): {cohens_d:.4f}")
    
    # Regression with demographic controls
    print("\n3. REGRESSION WITH DEMOGRAPHIC CONTROLS")
    print("-" * 30)
    
    # Prepare regression data
    X = df[['post_covid', 'prop_young_adults', 'prop_middle_aged', 'prop_elderly', 'total_population']].copy()
    y = df['anxiety_items_per_capita'].copy()
    
    # Handle any missing values
    mask = ~(X.isnull().any(axis=1) | y.isnull())
    X_clean = X[mask]
    y_clean = y[mask]
    
    # Fit regression
    reg = LinearRegression()
    reg.fit(X_clean, y_clean)
    
    print(f"R-squared: {reg.score(X_clean, y_clean):.4f}")
    print("\nCoefficients:")
    feature_names = ['Post-COVID', 'Prop Young Adults', 'Prop Middle Aged', 'Prop Elderly', 'Total Population']
    for name, coef in zip(feature_names, reg.coef_):
        print(f"  {name}: {coef:.8f}")
    print(f"  Intercept: {reg.intercept_:.8f}")
    
    # Statistical significance of COVID coefficient
    # Calculate standard errors (simplified)
    mse = np.mean((y_clean - reg.predict(X_clean))**2)
    var_coef = mse * np.linalg.inv(X_clean.T @ X_clean).diagonal()
    se_coef = np.sqrt(var_coef)
    t_stats = reg.coef_ / se_coef
    
    print(f"\nCOVID coefficient significance:")
    print(f"  Coefficient: {reg.coef_[0]:.8f}")
    print(f"  Standard Error: {se_coef[0]:.8f}")
    print(f"  T-statistic: {t_stats[0]:.4f}")
    
    return {
        'pre_covid_mean': pre_covid['anxiety_items_per_capita'].mean(),
        'post_covid_mean': post_covid['anxiety_items_per_capita'].mean(),
        't_stat': t_stat,
        'p_value': p_value,
        'cohens_d': cohens_d,
        'r_squared': reg.score(X_clean, y_clean),
        'covid_coefficient': reg.coef_[0],
        'covid_t_stat': t_stats[0]
    }

def create_visualizations(df, results):
    """Create visualizations for the analysis"""
    
    # Set up the plotting style
    plt.style.use('default')
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('COVID-19 Impact on Anxiety Prescriptions in London LSOAs', fontsize=16, fontweight='bold')
    
    # 1. Time series plot
    monthly_means = df.groupby('year_month')['anxiety_items_per_capita'].mean().reset_index()
    monthly_means['date'] = pd.to_datetime(monthly_means['year_month'], format='%Y%m')
    
    axes[0,0].plot(monthly_means['date'], monthly_means['anxiety_items_per_capita'], 
                   marker='o', linewidth=2, markersize=6)
    axes[0,0].axvline(pd.to_datetime('2020-03'), color='red', linestyle='--', 
                      label='COVID-19 Start', alpha=0.7)
    axes[0,0].set_title('Monthly Anxiety Prescriptions Per Capita Over Time')
    axes[0,0].set_xlabel('Date')
    axes[0,0].set_ylabel('Anxiety Items Per Capita')
    axes[0,0].legend()
    axes[0,0].grid(True, alpha=0.3)
    
    # 2. Before/After comparison
    pre_post_data = df.groupby('post_covid')['anxiety_items_per_capita'].agg(['mean', 'std']).reset_index()
    pre_post_data['period'] = ['Pre-COVID', 'Post-COVID']
    
    axes[0,1].bar(pre_post_data['period'], pre_post_data['mean'], 
                  yerr=pre_post_data['std'], capsize=5, alpha=0.7,
                  color=['blue', 'red'])
    axes[0,1].set_title('Anxiety Prescriptions: Pre vs Post COVID')
    axes[0,1].set_ylabel('Mean Anxiety Items Per Capita')
    
    # Add statistical significance annotation
    axes[0,1].text(0.5, max(pre_post_data['mean']) * 1.1, 
                   f"p = {results['p_value']:.4f}\nCohen's d = {results['cohens_d']:.3f}",
                   ha='center', va='bottom', fontsize=10, 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
    
    # 3. Distribution comparison
    pre_covid = df[df['pre_covid'] == 1]['anxiety_items_per_capita']
    post_covid = df[df['post_covid'] == 1]['anxiety_items_per_capita']
    
    axes[1,0].hist(pre_covid, alpha=0.6, label='Pre-COVID', bins=30, density=True, color='blue')
    axes[1,0].hist(post_covid, alpha=0.6, label='Post-COVID', bins=30, density=True, color='red')
    axes[1,0].set_title('Distribution of Anxiety Prescriptions')
    axes[1,0].set_xlabel('Anxiety Items Per Capita')
    axes[1,0].set_ylabel('Density')
    axes[1,0].legend()
    
    # 4. LSOA-level heatmap (sample)
    sample_lsoas = df['lsoa_code'].unique()[:20]  # Sample for visualization
    sample_data = df[df['lsoa_code'].isin(sample_lsoas)]
    pivot_data = sample_data.pivot_table(values='anxiety_items_per_capita', 
                                        index='lsoa_code', 
                                        columns='year_month', 
                                        fill_value=0)
    
    im = axes[1,1].imshow(pivot_data.values, aspect='auto', cmap='YlOrRd')
    axes[1,1].set_title('LSOA-Level Anxiety Prescriptions Heatmap (Sample)')
    axes[1,1].set_xlabel('Time Period')
    axes[1,1].set_ylabel('LSOA Code (Sample)')
    
    # Add colorbar
    plt.colorbar(im, ax=axes[1,1], label='Anxiety Items Per Capita')
    
    plt.tight_layout()
    plt.savefig('anxiety_covid_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"\nVisualization saved as: anxiety_covid_analysis.png")

def main():
    """Main analysis function"""
    
    print("Starting Anxiety COVID Impact Analysis...")
    print("=" * 60)
    
    # Parameters
    start_month = "201903"  # March 2019
    end_month = "202103"    # March 2021
    
    # Load data
    print("\n1. Loading anxiety drug codes...")
    anxiety_bnf_codes, anxiety_drugs = load_anxiety_drugs()
    print(f"Loaded {len(anxiety_bnf_codes)} anxiety BNF codes for {len(anxiety_drugs)} drugs")
    
    print("\n2. Loading census demographic data...")
    census_data = load_census_data()
    print(f"Loaded census data for years: {list(census_data.keys())}")
    
    print("\n3. Identifying London LSOAs...")
    london_lsoas = identify_london_lsoas()
    print(f"Identified {len(london_lsoas)} London LSOAs")
    
    print("\n4. Processing prescription data...")
    monthly_anxiety_data = process_prescription_data(start_month, end_month, anxiety_bnf_codes)
    print(f"Processed {len(monthly_anxiety_data)} months of data")
    
    print("\n5. Mapping to LSOA level...")
    monthly_lsoa_data = map_to_lsoa_level(monthly_anxiety_data, london_lsoas)
    
    print("\n6. Creating time series dataframe...")
    df = create_time_series_dataframe(monthly_lsoa_data, census_data)
    print(f"Created dataset with {len(df)} observations across {df['lsoa_code'].nunique()} LSOAs")
    
    # Save intermediate data
    df.to_csv('anxiety_timeseries_london.csv', index=False)
    print("Saved time series data to: anxiety_timeseries_london.csv")
    
    print("\n7. Running COVID impact analysis...")
    results = run_covid_impact_analysis(df)
    
    print("\n8. Creating visualizations...")
    create_visualizations(df, results)
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE!")
    print("="*60)
    print(f"Key Findings:")
    print(f"- Pre-COVID mean: {results['pre_covid_mean']:.6f} items per capita")
    print(f"- Post-COVID mean: {results['post_covid_mean']:.6f} items per capita")
    print(f"- Change: {((results['post_covid_mean']/results['pre_covid_mean'])-1)*100:+.2f}%")
    print(f"- Statistical significance: {'Yes' if results['p_value'] < 0.05 else 'No'} (p={results['p_value']:.4f})")
    print(f"- Effect size: {results['cohens_d']:.3f} (Cohen's d)")
    print(f"- Regression R²: {results['r_squared']:.3f}")

if __name__ == "__main__":
    main()