#!/usr/bin/env python3
"""
Exploratory Data Analysis - Shipping Patterns
Phase 3 Step 3.1: Analyze collected data for patterns
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path
from supabase import create_client

# =============================================================================
# DATA LOADING
# =============================================================================

def load_supabase_data():
    """Load all data from Supabase into DataFrames"""
    url = 'https://hssnbnsffqorupviykha.supabase.co'
    key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhzc25ibnNmZnFvcnVwdml5a2hhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODAyNDYwMiwiZXhwIjoyMDgzNjAwNjAyfQ.S8q15OUhTcco8gFEEqAfW5Npmi-1TAfV_g9qzozc1bY'
    
    client = create_client(url, key)
    
    data = {}
    
    # Load each table
    tables = [
        'kaggle_supply_chain',
        'kaggle_logistics', 
        'kaggle_port_performance',
        'historical_disruptions',
        'routes',
        'vessels',
        'ports'
    ]
    
    for table in tables:
        try:
            result = client.table(table).select('*').execute()
            data[table] = pd.DataFrame(result.data)
            print(f"✓ {table}: {len(data[table])} records")
        except Exception as e:
            print(f"✗ {table}: {e}")
            data[table] = pd.DataFrame()
    
    return data


def load_synthetic_data():
    """Load synthetic transit data"""
    data_path = Path(__file__).parent.parent / "data" / "sample" / "synthetic_data.json"
    
    if data_path.exists():
        with open(data_path) as f:
            raw = json.load(f)
        
        transits = pd.DataFrame(raw.get('transits', []))
        print(f"✓ synthetic_transits: {len(transits)} records")
        return transits
    
    return pd.DataFrame()


# =============================================================================
# ROUTE DURATION ANALYSIS
# =============================================================================

def analyze_route_duration(transits_df):
    """Analyze typical route durations"""
    print("\n" + "="*60)
    print("📊 ROUTE DURATION ANALYSIS")
    print("="*60)
    
    if transits_df.empty:
        print("No transit data available")
        return {}
    
    # Group by route
    if 'route_id' in transits_df.columns and 'actual_duration_hours' in transits_df.columns:
        route_stats = transits_df.groupby('route_id').agg({
            'actual_duration_hours': ['mean', 'std', 'min', 'max', 'count']
        }).round(2)
        
        route_stats.columns = ['avg_hours', 'std_hours', 'min_hours', 'max_hours', 'count']
        route_stats['avg_days'] = (route_stats['avg_hours'] / 24).round(1)
        
        print("\nRoute Duration Statistics:")
        print(route_stats.to_string())
        
        # Overall stats
        overall = {
            'avg_duration_hours': transits_df['actual_duration_hours'].mean(),
            'avg_duration_days': transits_df['actual_duration_hours'].mean() / 24,
            'std_duration_hours': transits_df['actual_duration_hours'].std(),
            'typical_range_days': (
                transits_df['actual_duration_hours'].quantile(0.25) / 24,
                transits_df['actual_duration_hours'].quantile(0.75) / 24
            )
        }
        
        print(f"\nOverall Statistics:")
        print(f"  Average Duration: {overall['avg_duration_days']:.1f} days")
        print(f"  Std Deviation: {overall['std_duration_hours']:.1f} hours")
        print(f"  Typical Range: {overall['typical_range_days'][0]:.1f} - {overall['typical_range_days'][1]:.1f} days")
        
        return overall
    
    return {}


# =============================================================================
# SEASONAL VARIATION ANALYSIS
# =============================================================================

def analyze_seasonal_patterns(transits_df):
    """Analyze seasonal variations in shipping"""
    print("\n" + "="*60)
    print("🌊 SEASONAL VARIATION ANALYSIS")
    print("="*60)
    
    if transits_df.empty or 'departure_date' not in transits_df.columns:
        print("No seasonal data available")
        return {}
    
    # Convert to datetime
    transits_df['departure_date'] = pd.to_datetime(transits_df['departure_date'])
    transits_df['month'] = transits_df['departure_date'].dt.month
    transits_df['quarter'] = transits_df['departure_date'].dt.quarter
    
    # Monthly patterns
    monthly = transits_df.groupby('month').agg({
        'actual_duration_hours': 'mean',
        'delay_hours': 'mean' if 'delay_hours' in transits_df.columns else lambda x: 0
    }).round(2)
    
    if 'delay_hours' not in transits_df.columns:
        transits_df['delay_hours'] = transits_df['actual_duration_hours'] - transits_df.get('scheduled_duration_hours', transits_df['actual_duration_hours'] * 0.95)
        monthly = transits_df.groupby('month').agg({
            'actual_duration_hours': 'mean',
            'delay_hours': 'mean'
        }).round(2)
    
    monthly.columns = ['avg_duration_hours', 'avg_delay_hours']
    
    print("\nMonthly Patterns:")
    month_names = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun',
                   7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
    
    for month, row in monthly.iterrows():
        delay_indicator = "⚠️" if row['avg_delay_hours'] > 10 else "✓"
        print(f"  {month_names[month]}: {row['avg_duration_hours']:.0f}h avg, {row['avg_delay_hours']:.1f}h delay {delay_indicator}")
    
    # Identify high-risk months (typhoon season, peak shipping)
    high_risk_months = monthly[monthly['avg_delay_hours'] > monthly['avg_delay_hours'].mean()].index.tolist()
    
    seasonal_insights = {
        'peak_delay_months': high_risk_months,
        'typhoon_season': [7, 8, 9, 10],  # July-October
        'peak_shipping': [9, 10, 11],      # Before holidays
        'lowest_delay_months': monthly['avg_delay_hours'].nsmallest(3).index.tolist()
    }
    
    print(f"\n📌 Key Seasonal Insights:")
    print(f"  Peak Delay Months: {[month_names[m] for m in high_risk_months]}")
    print(f"  Typhoon Season: Jul-Oct")
    print(f"  Pre-Holiday Rush: Sep-Nov")
    
    return seasonal_insights


# =============================================================================
# SPEED VARIATION ANALYSIS  
# =============================================================================

def analyze_speed_patterns(transits_df):
    """Analyze vessel speed variations"""
    print("\n" + "="*60)
    print("⚡ SPEED VARIATION ANALYSIS")
    print("="*60)
    
    if transits_df.empty:
        print("No speed data available")
        return {}
    
    # Calculate speed if not present
    if 'avg_speed_knots' not in transits_df.columns:
        # Estimate: Taiwan to LA ~6500 nautical miles
        route_distances = {
            'kaohsiung_losangeles': 6500,
            'kaohsiung_longbeach': 6480,
            'kaohsiung_oakland': 6200,
            'taiwan_la': 6500,
            'default': 6500
        }
        
        def calc_speed(row):
            dist = route_distances.get(row.get('route_id', 'default'), 6500)
            hours = row.get('actual_duration_hours', 336)  # 14 days default
            return dist / hours if hours > 0 else 0
        
        transits_df['avg_speed_knots'] = transits_df.apply(calc_speed, axis=1)
    
    speed_stats = {
        'mean_speed': transits_df['avg_speed_knots'].mean(),
        'std_speed': transits_df['avg_speed_knots'].std(),
        'min_speed': transits_df['avg_speed_knots'].min(),
        'max_speed': transits_df['avg_speed_knots'].max(),
        'typical_range': (
            transits_df['avg_speed_knots'].quantile(0.25),
            transits_df['avg_speed_knots'].quantile(0.75)
        )
    }
    
    print(f"\nSpeed Statistics:")
    print(f"  Average Speed: {speed_stats['mean_speed']:.1f} knots")
    print(f"  Std Deviation: {speed_stats['std_speed']:.1f} knots")
    print(f"  Range: {speed_stats['min_speed']:.1f} - {speed_stats['max_speed']:.1f} knots")
    print(f"  Typical: {speed_stats['typical_range'][0]:.1f} - {speed_stats['typical_range'][1]:.1f} knots")
    
    # Speed categories
    slow = len(transits_df[transits_df['avg_speed_knots'] < 15])
    normal = len(transits_df[(transits_df['avg_speed_knots'] >= 15) & (transits_df['avg_speed_knots'] < 20)])
    fast = len(transits_df[transits_df['avg_speed_knots'] >= 20])
    
    print(f"\n  Speed Distribution:")
    print(f"    Slow (<15 kts): {slow} ({100*slow/len(transits_df):.1f}%)")
    print(f"    Normal (15-20 kts): {normal} ({100*normal/len(transits_df):.1f}%)")
    print(f"    Fast (≥20 kts): {fast} ({100*fast/len(transits_df):.1f}%)")
    
    return speed_stats


# =============================================================================
# DISRUPTION ANALYSIS
# =============================================================================

def analyze_disruptions(disruptions_df):
    """Analyze historical disruption patterns"""
    print("\n" + "="*60)
    print("⚠️ DISRUPTION PATTERN ANALYSIS")
    print("="*60)
    
    if disruptions_df.empty:
        print("No disruption data available")
        return {}
    
    # By type
    type_stats = disruptions_df.groupby('event_type').agg({
        'delay_days': ['mean', 'max', 'count'],
        'cost_impact_usd': 'sum'
    }).round(2)
    
    type_stats.columns = ['avg_delay', 'max_delay', 'count', 'total_cost']
    type_stats = type_stats.sort_values('count', ascending=False)
    
    print("\nDisruption by Type:")
    for event_type, row in type_stats.iterrows():
        print(f"  {event_type}: {row['count']} events, avg {row['avg_delay']:.1f}d delay, ${row['total_cost']/1e9:.1f}B cost")
    
    # By severity
    if 'severity' in disruptions_df.columns:
        severity_stats = disruptions_df.groupby('severity').agg({
            'delay_days': 'mean',
            'duration_days': 'mean'
        }).round(1)
        
        print(f"\nBy Severity:")
        for sev, row in severity_stats.iterrows():
            print(f"  {sev}: avg {row['delay_days']:.1f}d delay, {row['duration_days']:.0f}d duration")
    
    # Most impactful events
    print(f"\nTop 5 Most Costly Events:")
    top_cost = disruptions_df.nlargest(5, 'cost_impact_usd')[['event_date', 'event_type', 'delay_days', 'cost_impact_usd']]
    for _, row in top_cost.iterrows():
        print(f"  {row['event_date']}: {row['event_type']} - {row['delay_days']}d delay, ${row['cost_impact_usd']/1e9:.1f}B")
    
    return {
        'total_events': len(disruptions_df),
        'avg_delay_days': disruptions_df['delay_days'].mean(),
        'total_cost_usd': disruptions_df['cost_impact_usd'].sum(),
        'most_common_type': type_stats['count'].idxmax()
    }


# =============================================================================
# SUMMARY STATISTICS
# =============================================================================

def generate_summary(data):
    """Generate overall summary statistics"""
    print("\n" + "="*60)
    print("📈 SUMMARY STATISTICS")
    print("="*60)
    
    summary = {
        'data_sources': {},
        'total_records': 0,
        'analysis_date': datetime.now().isoformat()
    }
    
    for table, df in data.items():
        count = len(df) if isinstance(df, pd.DataFrame) else 0
        summary['data_sources'][table] = count
        summary['total_records'] += count
    
    print(f"\nData Sources:")
    for table, count in summary['data_sources'].items():
        print(f"  {table}: {count} records")
    
    print(f"\nTotal Records: {summary['total_records']}")
    
    return summary


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("="*60)
    print("🔬 EXPLORATORY DATA ANALYSIS")
    print("   Phase 3 Step 3.1: Shipping Pattern Analysis")
    print("="*60)
    
    # Load data
    print("\n📥 Loading data from Supabase...")
    supabase_data = load_supabase_data()
    
    print("\n📥 Loading synthetic transit data...")
    transits = load_synthetic_data()
    
    # Run analyses
    route_analysis = analyze_route_duration(transits)
    seasonal_analysis = analyze_seasonal_patterns(transits)
    speed_analysis = analyze_speed_patterns(transits)
    
    if 'historical_disruptions' in supabase_data and not supabase_data['historical_disruptions'].empty:
        disruption_analysis = analyze_disruptions(supabase_data['historical_disruptions'])
    else:
        disruption_analysis = {}
    
    # Generate summary
    all_data = {**supabase_data, 'synthetic_transits': transits}
    summary = generate_summary(all_data)
    
    # Save results
    results = {
        'summary': summary,
        'route_analysis': route_analysis,
        'seasonal_analysis': seasonal_analysis,
        'speed_analysis': speed_analysis,
        'disruption_analysis': disruption_analysis
    }
    
    output_path = Path(__file__).parent / "eda_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved to: {output_path}")
    print("="*60)
    
    return results


if __name__ == "__main__":
    main()
