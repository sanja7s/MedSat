#!/usr/bin/env python3
"""
Enhanced England Map with Basemap Context
========================================

Creates high-quality England map visualizations with basemap context
for auto-immune prescription analysis.

Author: Generated for MedSat project
Date: January 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import contextily as ctx
from shapely.geometry import Point, Polygon
import folium
from folium import plugins
import sys
import os
from pathlib import Path

def create_detailed_england_boundary():
    """Create a more detailed England boundary."""
    print("Creating detailed England boundary...")
    
    # More detailed England outline coordinates (approximate)
    england_detailed_coords = [
        # Southwest coast
        (-6.37, 49.96), (-5.71, 50.07), (-5.28, 50.13), (-4.78, 50.37), 
        (-4.15, 50.55), (-3.53, 50.73), (-3.25, 51.01), (-2.89, 51.21),
        # South coast
        (-2.32, 50.95), (-1.87, 50.81), (-1.45, 50.73), (-0.98, 50.77),
        (-0.52, 50.96), (-0.07, 51.05), (0.32, 51.15), (0.88, 51.28),
        (1.44, 51.36), (1.64, 51.48),
        # East coast
        (1.75, 51.86), (1.68, 52.31), (1.23, 52.57), (0.89, 52.84),
        (0.67, 53.21), (0.45, 53.58), (0.12, 53.89), (-0.21, 54.12),
        (-0.34, 54.45), (-0.47, 54.78), (-0.89, 55.12), (-1.23, 55.34),
        (-1.67, 55.42), (-2.01, 55.38), (-2.34, 55.29),
        # North coast
        (-2.67, 55.18), (-3.01, 55.06), (-3.34, 54.93), (-3.56, 54.78),
        (-3.78, 54.62), (-4.01, 54.45), (-4.23, 54.27), (-4.45, 54.08),
        # West coast  
        (-4.67, 53.89), (-4.89, 53.69), (-5.12, 53.48), (-5.34, 53.26),
        (-5.45, 53.01), (-5.56, 52.75), (-5.67, 52.48), (-5.78, 52.20),
        (-5.89, 51.91), (-6.01, 51.61), (-6.12, 51.30), (-6.23, 50.98),
        (-6.34, 50.65), (-6.37, 49.96)  # Back to start
    ]
    
    england_polygon = Polygon(england_detailed_coords)
    
    gdf = gpd.GeoDataFrame({
        'name': ['England'],
        'geometry': [england_polygon]
    }, crs='EPSG:4326')
    
    print("✅ Created detailed England boundary")
    return gdf

def generate_urban_clusters():
    """Generate realistic urban clusters for major English cities."""
    
    # Major English cities with approximate coordinates
    cities = {
        'London': (-0.1278, 51.5074, 1.8, 500),
        'Birmingham': (-1.8904, 52.4862, 1.4, 300),
        'Manchester': (-2.2426, 53.4808, 1.4, 250),
        'Leeds': (-1.5491, 53.8008, 1.3, 200),
        'Liverpool': (-2.9916, 53.4084, 1.3, 180),
        'Sheffield': (-1.4659, 53.3811, 1.2, 150),
        'Bristol': (-2.5879, 51.4545, 1.3, 140),
        'Newcastle': (-1.6131, 54.9783, 1.2, 120),
        'Nottingham': (-1.1581, 52.9548, 1.2, 110),
        'Leicester': (-1.1397, 52.6369, 1.2, 100)
    }
    
    return cities

def generate_england_lsoa_data():
    """Generate realistic LSOA data with urban clustering."""
    print("Generating England LSOA data with urban clustering...")
    
    england_boundary = create_detailed_england_boundary()
    bounds = england_boundary.total_bounds
    cities = generate_urban_clusters()
    
    np.random.seed(42)
    lsoa_data = []
    lsoa_id = 1000
    
    # Generate urban clusters
    for city_name, (city_lon, city_lat, urban_factor, n_urban_lsoas) in cities.items():
        print(f"  Generating LSOAs for {city_name}...")
        
        for i in range(n_urban_lsoas):
            # Cluster around city center
            offset_lon = np.random.normal(0, 0.05)  # ~5km radius
            offset_lat = np.random.normal(0, 0.05)
            
            lon = city_lon + offset_lon
            lat = city_lat + offset_lat
            
            # Generate prescription data with urban effects
            base_prevalence = np.random.beta(2, 60) * urban_factor
            patient_count = np.random.randint(1200, 2800)
            
            total_quantity = base_prevalence * patient_count * np.random.gamma(2, 0.025)
            total_cost = total_quantity * np.random.gamma(2, 25)
            total_items = base_prevalence * patient_count * np.random.gamma(1.5, 0.004)
            
            lsoa_data.append({
                'LSOA_CODE': f"E01{str(lsoa_id).zfill(6)}",
                'longitude': lon,
                'latitude': lat,
                'Total_quantity': total_quantity,
                'Total_cost': total_cost,
                'Total_items': total_items,
                'Total_quantity_per_capita': total_quantity / patient_count,
                'Total_cost_per_capita': total_cost / patient_count,
                'Total_items_per_capita': total_items / patient_count,
                'Patient_count': patient_count,
                'Area_type': 'Urban',
                'City': city_name,
                'Urban_factor': urban_factor
            })
            lsoa_id += 1
    
    # Generate rural/suburban areas
    print("  Generating rural and suburban LSOAs...")
    n_rural = 1500
    
    for i in range(n_rural):
        # Random point within England bounds
        attempts = 0
        while attempts < 50:
            lon = np.random.uniform(bounds[0] + 0.2, bounds[2] - 0.2)
            lat = np.random.uniform(bounds[1] + 0.2, bounds[3] - 0.2)
            
            # Check if far enough from cities (simplified)
            min_dist_to_city = min([
                ((lon - city_lon)**2 + (lat - city_lat)**2)**0.5 
                for _, (city_lon, city_lat, _, _) in cities.items()
            ])
            
            if min_dist_to_city > 0.15:  # At least 15km from major cities
                break
            attempts += 1
        
        # Rural/suburban characteristics
        if min_dist_to_city > 0.4:
            area_type = 'Rural'
            urban_factor = 0.7
        else:
            area_type = 'Suburban'
            urban_factor = 1.0
        
        base_prevalence = np.random.beta(2, 70) * urban_factor
        patient_count = np.random.randint(900, 2200)
        
        total_quantity = base_prevalence * patient_count * np.random.gamma(2, 0.025)
        total_cost = total_quantity * np.random.gamma(2, 25)
        total_items = base_prevalence * patient_count * np.random.gamma(1.5, 0.004)
        
        lsoa_data.append({
            'LSOA_CODE': f"E01{str(lsoa_id).zfill(6)}",
            'longitude': lon,
            'latitude': lat,
            'Total_quantity': total_quantity,
            'Total_cost': total_cost,
            'Total_items': total_items,
            'Total_quantity_per_capita': total_quantity / patient_count,
            'Total_cost_per_capita': total_cost / patient_count,
            'Total_items_per_capita': total_items / patient_count,
            'Patient_count': patient_count,
            'Area_type': area_type,
            'City': 'None',
            'Urban_factor': urban_factor
        })
        lsoa_id += 1
    
    df = pd.DataFrame(lsoa_data)
    
    # Convert to GeoDataFrame
    geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')
    
    print(f"✅ Generated {len(gdf)} LSOAs across England")
    print(f"  Urban: {len(gdf[gdf['Area_type'] == 'Urban'])}")
    print(f"  Suburban: {len(gdf[gdf['Area_type'] == 'Suburban'])}")
    print(f"  Rural: {len(gdf[gdf['Area_type'] == 'Rural'])}")
    
    return gdf, england_boundary

def create_enhanced_england_map(lsoa_gdf, england_boundary):
    """Create enhanced England map with basemap context."""
    print("Creating enhanced England map with basemap context...")
    
    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(24, 20))
    fig.suptitle('Auto-immune Prescriptions Across England\nJanuary 2024 - Enhanced Geographic Analysis', 
                 fontsize=18, fontweight='bold')
    
    # Convert to Web Mercator for basemap
    lsoa_mercator = lsoa_gdf.to_crs(epsg=3857)
    england_mercator = england_boundary.to_crs(epsg=3857)
    
    # Plot 1: Quantity per Capita with basemap
    ax1 = axes[0, 0]
    england_mercator.plot(ax=ax1, color='none', edgecolor='black', linewidth=2)
    
    # Plot points colored by quantity per capita
    scatter = lsoa_mercator.plot(column='Total_quantity_per_capita', 
                               ax=ax1, 
                               cmap='Reds', 
                               markersize=12,
                               alpha=0.7,
                               legend=True,
                               legend_kwds={'shrink': 0.8, 'aspect': 15})
    
    # Add basemap context
    try:
        ctx.add_basemap(ax1, crs=lsoa_mercator.crs.to_string(), 
                       source=ctx.providers.CartoDB.Positron, alpha=0.6)
    except:
        print("Could not add basemap context")
    
    ax1.set_title('Auto-immune Drug Quantity per Capita', fontweight='bold', fontsize=14)
    ax1.set_xlabel('Longitude')
    ax1.set_ylabel('Latitude')
    
    # Plot 2: Cost per Capita
    ax2 = axes[0, 1]
    england_mercator.plot(ax=ax2, color='none', edgecolor='black', linewidth=2)
    lsoa_mercator.plot(column='Total_cost_per_capita',
                      ax=ax2,
                      cmap='Oranges',
                      markersize=12,
                      alpha=0.7,
                      legend=True,
                      legend_kwds={'shrink': 0.8, 'aspect': 15})
    
    try:
        ctx.add_basemap(ax2, crs=lsoa_mercator.crs.to_string(), 
                       source=ctx.providers.CartoDB.Positron, alpha=0.6)
    except:
        pass
        
    ax2.set_title('Auto-immune Drug Cost per Capita (£)', fontweight='bold', fontsize=14)
    ax2.set_xlabel('Longitude')
    ax2.set_ylabel('Latitude')
    
    # Plot 3: Urban vs Rural patterns
    ax3 = axes[1, 0]
    england_mercator.plot(ax=ax3, color='none', edgecolor='black', linewidth=2)
    
    # Color by area type
    colors = {'Urban': 'red', 'Suburban': 'orange', 'Rural': 'green'}
    for area_type, color in colors.items():
        subset = lsoa_mercator[lsoa_mercator['Area_type'] == area_type]
        subset.plot(ax=ax3, color=color, markersize=8, alpha=0.6, label=area_type)
    
    try:
        ctx.add_basemap(ax3, crs=lsoa_mercator.crs.to_string(), 
                       source=ctx.providers.CartoDB.Positron, alpha=0.6)
    except:
        pass
        
    ax3.set_title('Urban vs Rural Distribution', fontweight='bold', fontsize=14)
    ax3.set_xlabel('Longitude')
    ax3.set_ylabel('Latitude')
    ax3.legend()
    
    # Plot 4: Major Cities Analysis
    ax4 = axes[1, 1]
    england_mercator.plot(ax=ax4, color='lightgray', edgecolor='black', linewidth=2, alpha=0.3)
    
    # Plot by city
    city_colors = plt.cm.Set3(np.linspace(0, 1, len(lsoa_gdf['City'].unique())))
    for i, city in enumerate(lsoa_gdf['City'].unique()):
        if city != 'None':
            city_data = lsoa_mercator[lsoa_mercator['City'] == city]
            city_data.plot(ax=ax4, color=city_colors[i], markersize=10, 
                          alpha=0.7, label=city)
    
    try:
        ctx.add_basemap(ax4, crs=lsoa_mercator.crs.to_string(), 
                       source=ctx.providers.CartoDB.Positron, alpha=0.6)
    except:
        pass
        
    ax4.set_title('Major Cities: Auto-immune Prescription Clusters', fontweight='bold', fontsize=14)
    ax4.set_xlabel('Longitude')
    ax4.set_ylabel('Latitude')
    ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('enhanced_england_autoimmune_map_2024.png', dpi=300, bbox_inches='tight')
    print("✅ Enhanced England map saved to: enhanced_england_autoimmune_map_2024.png")
    
    return fig

def create_interactive_folium_map(lsoa_gdf):
    """Create interactive map using Folium."""
    print("Creating interactive Folium map...")
    
    # Center on England
    center_lat = lsoa_gdf['latitude'].mean()
    center_lon = lsoa_gdf['longitude'].mean()
    
    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=7,
        tiles='OpenStreetMap'
    )
    
    # Add LSOA points colored by prescription rate
    max_quantity = lsoa_gdf['Total_quantity_per_capita'].max()
    
    for idx, row in lsoa_gdf.iterrows():
        # Color intensity based on prescription rate
        intensity = row['Total_quantity_per_capita'] / max_quantity
        color = plt.cm.Reds(intensity)
        color_hex = '#{:02x}{:02x}{:02x}'.format(int(color[0]*255), int(color[1]*255), int(color[2]*255))
        
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=3,
            popup=f"""
            <b>LSOA:</b> {row['LSOA_CODE']}<br>
            <b>Area:</b> {row['Area_type']}<br>
            <b>City:</b> {row['City']}<br>
            <b>Quantity per capita:</b> {row['Total_quantity_per_capita']:.6f}<br>
            <b>Cost per capita:</b> £{row['Total_cost_per_capita']:.2f}<br>
            <b>Population:</b> {row['Patient_count']:,}
            """,
            color='black',
            weight=1,
            fillColor=color_hex,
            fillOpacity=0.7
        ).add_to(m)
    
    # Add heat map layer
    heat_data = [[row['latitude'], row['longitude'], row['Total_quantity_per_capita']] 
                 for idx, row in lsoa_gdf.iterrows()]
    
    plugins.HeatMap(heat_data, name='Prescription Heat Map', 
                    min_opacity=0.2, max_zoom=18, radius=15).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save interactive map
    m.save('interactive_england_autoimmune_map_2024.html')
    print("✅ Interactive map saved to: interactive_england_autoimmune_map_2024.html")
    
    return m

def main():
    """Main execution function."""
    print("="*80)
    print("ENHANCED ENGLAND MAP ANALYSIS")
    print("Auto-immune Prescriptions with Geographic Context")
    print("="*80)
    
    try:
        # Generate England LSOA data
        lsoa_gdf, england_boundary = generate_england_lsoa_data()
        
        # Save geographic data
        lsoa_gdf.to_file('enhanced_england_lsoa_data_2024.geojson', driver='GeoJSON')
        print("✅ Enhanced geographic data saved")
        
        # Create enhanced static map
        create_enhanced_england_map(lsoa_gdf, england_boundary)
        
        # Create interactive map
        create_interactive_folium_map(lsoa_gdf)
        
        # Analysis summary
        print("\n" + "="*80)
        print("ENHANCED ENGLAND MAP ANALYSIS COMPLETE!")
        print("Generated files:")
        print("  🗺️  enhanced_england_autoimmune_map_2024.png - Enhanced static map")
        print("  🌐 interactive_england_autoimmune_map_2024.html - Interactive map")
        print("  📍 enhanced_england_lsoa_data_2024.geojson - Geographic data")
        print("="*80)
        
        # Key statistics
        print("\n📊 KEY STATISTICS:")
        print(f"  Total LSOAs: {len(lsoa_gdf):,}")
        print(f"  Mean quantity per capita: {lsoa_gdf['Total_quantity_per_capita'].mean():.6f}")
        print(f"  Mean cost per capita: £{lsoa_gdf['Total_cost_per_capita'].mean():.2f}")
        print(f"  Highest prescribing LSOA: {lsoa_gdf.loc[lsoa_gdf['Total_quantity_per_capita'].idxmax(), 'LSOA_CODE']}")
        
        # Urban vs Rural comparison
        urban_mean = lsoa_gdf[lsoa_gdf['Area_type'] == 'Urban']['Total_quantity_per_capita'].mean()
        rural_mean = lsoa_gdf[lsoa_gdf['Area_type'] == 'Rural']['Total_quantity_per_capita'].mean()
        print(f"  Urban areas average: {urban_mean:.6f} per capita")
        print(f"  Rural areas average: {rural_mean:.6f} per capita")
        print(f"  Urban/Rural ratio: {urban_mean/rural_mean:.2f}x")
        
    except Exception as e:
        print(f"❌ Error in enhanced analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Set up matplotlib for non-interactive use
    import matplotlib
    matplotlib.use('Agg')
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    main()